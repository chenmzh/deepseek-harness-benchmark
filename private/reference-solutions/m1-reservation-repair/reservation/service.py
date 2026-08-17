from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4


class ReservationNotFound(KeyError):
    pass


class InventoryService:
    def __init__(self, database: str | Path, initial_stock: dict[str, int] | None = None):
        self.database = Path(database)
        if self.database.exists():
            self._state = json.loads(self.database.read_text(encoding="utf-8"))
        else:
            if initial_stock is None:
                raise ValueError("initial_stock is required for a new database")
            if any(type(value) is not int or value < 0 for value in initial_stock.values()):
                raise ValueError("stock values must be non-negative integers")
            self._state = {"initial": dict(initial_stock), "available": dict(initial_stock), "reservations": {}, "requests": {}}
            self._persist()

    def reserve(self, sku: str, quantity: int, request_id: str) -> dict:
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("quantity must be positive")
        if request_id in self._state["requests"]:
            return deepcopy(self._state["requests"][request_id])
        if self._state["available"].get(sku, 0) < quantity:
            return {"ok": False, "reason": "insufficient_stock"}
        reservation_id = uuid4().hex
        reservation = {"id": reservation_id, "sku": sku, "quantity": quantity, "status": "active"}
        self._state["available"][sku] -= quantity
        self._state["reservations"][reservation_id] = reservation
        result = {"ok": True, "reservation": deepcopy(reservation)}
        self._state["requests"][request_id] = result
        self._persist()
        return deepcopy(result)

    def cancel(self, reservation_id: str, request_id: str) -> dict:
        if request_id in self._state["requests"]:
            return deepcopy(self._state["requests"][request_id])
        reservation = self._state["reservations"].get(reservation_id)
        if reservation is None:
            raise ReservationNotFound(reservation_id)
        if reservation["status"] == "active":
            self._state["available"][reservation["sku"]] += reservation["quantity"]
            reservation["status"] = "cancelled"
        result = {"ok": True, "reservation": deepcopy(reservation)}
        self._state["requests"][request_id] = result
        self._persist()
        return deepcopy(result)

    def available(self, sku: str) -> int:
        return int(self._state["available"].get(sku, 0))

    def reservations(self) -> list[dict]:
        return deepcopy(list(self._state["reservations"].values()))

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
