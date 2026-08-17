from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4


class JobNotFound(KeyError):
    pass


class LeaseConflict(RuntimeError):
    pass


class DurableQueue:
    def __init__(self, database: str | Path, max_attempts: int = 3, base_backoff: int = 5):
        if type(max_attempts) is not int or max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if type(base_backoff) is not int or base_backoff < 0:
            raise ValueError("base_backoff must be non-negative")
        self.database = Path(database)
        self.max_attempts = max_attempts
        self.base_backoff = base_backoff
        if self.database.exists():
            self._state = json.loads(self.database.read_text(encoding="utf-8"))
        else:
            self._state = {"next_sequence": 0, "jobs": [], "idempotency": {}}
            self._persist()

    def enqueue(self, payload, idempotency_key: str) -> dict:
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise ValueError("idempotency_key must be non-empty")
        existing = self._state["idempotency"].get(idempotency_key)
        if existing is not None:
            return deepcopy(self._find(existing))
        job = {
            "id": uuid4().hex,
            "sequence": self._state["next_sequence"],
            "payload": deepcopy(payload),
            "idempotency_key": idempotency_key,
            "state": "queued",
            "attempts": 0,
            "available_at": 0,
            "lease_owner": None,
            "lease_until": None,
            "last_error": None,
        }
        self._state["next_sequence"] += 1
        self._state["jobs"].append(job)
        self._state["idempotency"][idempotency_key] = job["id"]
        self._persist()
        return deepcopy(job)

    def claim(self, worker_id: str, lease_seconds: int, now: int) -> dict | None:
        self._validate_worker(worker_id)
        if type(lease_seconds) is not int or lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self._validate_now(now)
        self.recover_expired(now)
        eligible = [job for job in self._state["jobs"] if job["state"] == "queued" and job["available_at"] <= now]
        if not eligible:
            return None
        job = min(eligible, key=lambda item: (item["available_at"], item["sequence"]))
        job["state"] = "leased"
        job["attempts"] += 1
        job["lease_owner"] = worker_id
        job["lease_until"] = now + lease_seconds
        self._persist()
        return deepcopy(job)

    def ack(self, job_id: str, worker_id: str) -> dict:
        self._validate_worker(worker_id)
        job = self._find(job_id)
        if job["state"] == "succeeded" and job["lease_owner"] == worker_id:
            return deepcopy(job)
        self._require_owner(job, worker_id)
        job["state"] = "succeeded"
        job["lease_until"] = None
        self._persist()
        return deepcopy(job)

    def fail(self, job_id: str, worker_id: str, error: str, now: int) -> dict:
        self._validate_worker(worker_id)
        self._validate_now(now)
        job = self._find(job_id)
        self._require_owner(job, worker_id)
        self._retry_or_dead(job, error, now)
        self._persist()
        return deepcopy(job)

    def recover_expired(self, now: int) -> int:
        self._validate_now(now)
        recovered = 0
        for job in self._state["jobs"]:
            if job["state"] == "leased" and job["lease_until"] <= now:
                self._retry_or_dead(job, "lease_expired", job["lease_until"])
                recovered += 1
        if recovered:
            self._persist()
        return recovered

    def jobs(self) -> list[dict]:
        return deepcopy(self._state["jobs"])

    def _retry_or_dead(self, job: dict, error: str, failure_time: int) -> None:
        job["last_error"] = error
        job["lease_until"] = None
        if job["attempts"] >= self.max_attempts:
            job["state"] = "dead"
        else:
            job["state"] = "queued"
            job["available_at"] = failure_time + self.base_backoff * 2 ** (job["attempts"] - 1)

    def _require_owner(self, job: dict, worker_id: str) -> None:
        if job["state"] != "leased" or job["lease_owner"] != worker_id:
            raise LeaseConflict(job["id"])

    def _find(self, job_id: str) -> dict:
        for job in self._state["jobs"]:
            if job["id"] == job_id:
                return job
        raise JobNotFound(job_id)

    @staticmethod
    def _validate_worker(worker_id: str) -> None:
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id must be non-empty")

    @staticmethod
    def _validate_now(now: int) -> None:
        if type(now) is not int or now < 0:
            raise ValueError("now must be a non-negative integer")

    def _persist(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{self.database.name}.", dir=self.database.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(self._state, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.database)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
