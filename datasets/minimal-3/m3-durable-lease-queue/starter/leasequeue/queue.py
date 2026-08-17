from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


class JobNotFound(KeyError):
    pass


class LeaseConflict(RuntimeError):
    pass


class DurableQueue:
    def __init__(self, database: str | Path, max_attempts: int = 3, base_backoff: int = 5):
        self.database = Path(database)
        self.max_attempts = max_attempts
        self.base_backoff = base_backoff
        if self.database.exists():
            self._state = json.loads(self.database.read_text(encoding="utf-8"))
        else:
            self._state = {"next_sequence": 0, "jobs": [], "idempotency": {}}
            self._persist()

    def enqueue(self, payload, idempotency_key: str) -> dict:
        job = {
            "id": uuid4().hex,
            "sequence": self._state["next_sequence"],
            "payload": payload,
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
        self._persist()
        return dict(job)

    def claim(self, worker_id: str, lease_seconds: int, now: int) -> dict | None:
        for job in self._state["jobs"]:
            if job["state"] == "queued" and job["available_at"] <= now:
                job["state"] = "leased"
                job["lease_owner"] = worker_id
                job["lease_until"] = now + lease_seconds
                self._persist()
                return dict(job)
        return None

    def ack(self, job_id: str, worker_id: str) -> dict:
        job = self._find(job_id)
        job["state"] = "succeeded"
        self._persist()
        return dict(job)

    def fail(self, job_id: str, worker_id: str, error: str, now: int) -> dict:
        job = self._find(job_id)
        job["state"] = "queued"
        job["last_error"] = error
        job["available_at"] = now
        self._persist()
        return dict(job)

    def recover_expired(self, now: int) -> int:
        return 0

    def jobs(self) -> list[dict]:
        return [dict(job) for job in self._state["jobs"]]

    def _find(self, job_id: str) -> dict:
        for job in self._state["jobs"]:
            if job["id"] == job_id:
                return job
        raise JobNotFound(job_id)

    def _persist(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.database.write_text(json.dumps(self._state, sort_keys=True), encoding="utf-8")
