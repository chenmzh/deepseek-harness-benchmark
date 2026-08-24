from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any


class MissingKey(KeyError):
    pass


class VersionConflict(RuntimeError):
    pass


class VersionedTTLStore:
    def __init__(self, database: str | Path, ttl: int = 10):
        if not isinstance(ttl, int) or isinstance(ttl, bool) or ttl <= 0:
            raise ValueError("ttl must be a positive integer")
        self.database = Path(database)
        self.ttl = ttl
        if self.database.exists():
            self._state = json.loads(self.database.read_text(encoding="utf-8"))
        else:
            self._state = {"records": {}, "versions": {}, "requests": {}}
            self._persist()

    @staticmethod
    def _text(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def _now(now: Any) -> None:
        if not isinstance(now, int) or isinstance(now, bool) or now < 0:
            raise ValueError("now must be a non-negative integer")

    @staticmethod
    def _value(value: Any) -> None:
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("value must be JSON-serializable") from exc

    def _persist(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{self.database.name}.", dir=self.database.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(self._state, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.database)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def _expire(self, key: str, now: int) -> bool:
        record = self._state["records"].get(key)
        if record is not None and now >= record["expires_at"]:
            del self._state["records"][key]
            return True
        return False

    def _request(self, request_id: str):
        result = self._state["requests"].get(request_id)
        return deepcopy(result) if result is not None else None

    def _record_success(self, request_id: str, result: Any) -> Any:
        self._state["requests"][request_id] = deepcopy(result)
        self._persist()
        return deepcopy(result)

    def put(self, key: str, value: Any, request_id: str, now: int):
        self._text(key, "key")
        self._text(request_id, "request_id")
        self._now(now)
        self._value(value)
        prior = self._request(request_id)
        if prior is not None:
            return prior
        self._expire(key, now)
        version = int(self._state["versions"].get(key, 0)) + 1
        self._state["versions"][key] = version
        row = {"key": key, "value": deepcopy(value), "version": version, "expires_at": now + self.ttl}
        self._state["records"][key] = row
        return self._record_success(request_id, row)

    def get(self, key: str, now: int):
        self._text(key, "key")
        self._now(now)
        changed = self._expire(key, now)
        if changed:
            self._persist()
        return deepcopy(self._state["records"].get(key))

    def compare_and_swap(self, key: str, expected_version: int, value: Any, request_id: str, now: int):
        self._text(key, "key")
        self._text(request_id, "request_id")
        self._now(now)
        self._value(value)
        prior = self._request(request_id)
        if prior is not None:
            return prior
        expired = self._expire(key, now)
        record = self._state["records"].get(key)
        if record is None:
            if expired:
                self._persist()
            raise MissingKey(key)
        if record["version"] != expected_version:
            raise VersionConflict(key)
        version = int(self._state["versions"][key]) + 1
        self._state["versions"][key] = version
        row = {"key": key, "value": deepcopy(value), "version": version, "expires_at": now + self.ttl}
        self._state["records"][key] = row
        return self._record_success(request_id, row)

    def delete(self, key: str, expected_version: int, request_id: str, now: int):
        self._text(key, "key")
        self._text(request_id, "request_id")
        self._now(now)
        prior = self._request(request_id)
        if prior is not None:
            return prior
        expired = self._expire(key, now)
        record = self._state["records"].get(key)
        if record is None:
            if expired:
                self._persist()
            raise MissingKey(key)
        if record["version"] != expected_version:
            raise VersionConflict(key)
        del self._state["records"][key]
        return self._record_success(request_id, {"key": key, "version": expected_version, "deleted": True})

    def items(self, now: int):
        self._now(now)
        changed = False
        for key in list(self._state["records"]):
            changed = self._expire(key, now) or changed
        if changed:
            self._persist()
        return [deepcopy(self._state["records"][key]) for key in sorted(self._state["records"])]
