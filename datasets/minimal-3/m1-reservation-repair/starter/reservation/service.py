from __future__ import annotations

import json
from pathlib import Path
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
            self._state = {
                "initial": dict(initial_stock),
                "available": dict(initial_stock),
                "reservations": {},
                "requests": {},
            }
            self._persist()

    def reserve(self, sku: str, quantity: int, request_id: str) -> dict:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if request_id in self._state["requests"]:
            return dict(self._state["requests"][request_id])
        if self._state["available"].get(sku, 0) < quantity:
            result = {"ok": False, "reason": "insufficient_stock"}
            self._state["requests"][request_id] = result
            self._persist()
            return dict(result)

        reservation_id = uuid4().hex
        self._state["available"][sku] -= quantity
        reservation = {
            "id": reservation_id,
            "sku": sku,
            "quantity": quantity,
            "status": "active",
        }
        self._state["reservations"][reservation_id] = reservation
        result = {"ok": True, "reservation": dict(reservation)}
        self._state["requests"][request_id] = result
        self._persist()
        return dict(result)

    def cancel(self, reservation_id: str, request_id: str) -> dict:
        if request_id in self._state["requests"]:
            return dict(self._state["requests"][request_id])
        reservation = self._state["reservations"].get(reservation_id)
        if reservation is None:
            raise ReservationNotFound(reservation_id)

        self._state["available"][reservation["sku"]] += reservation["quantity"]
        reservation["status"] = "cancelled"
        result = {"ok": True, "reservation": dict(reservation)}
        self._state["requests"][request_id] = result
        self._persist()
        return dict(result)

    def available(self, sku: str) -> int:
        return int(self._state["available"].get(sku, 0))

    def reservations(self) -> list[dict]:
        return [dict(item) for item in self._state["reservations"].values()]

    def _persist(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.database.write_text(json.dumps(self._state, sort_keys=True), encoding="utf-8")
