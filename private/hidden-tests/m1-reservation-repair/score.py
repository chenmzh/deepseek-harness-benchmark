from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Callable


def load_service(submission: Path):
    sys.path.insert(0, str(submission))
    for name in list(sys.modules):
        if name == "reservation" or name.startswith("reservation."):
            del sys.modules[name]
    module = importlib.import_module("reservation")
    return module.InventoryService, module.ReservationNotFound


def case_basic(service_type, _not_found, root: Path) -> None:
    service = service_type(root / "db.json", {"a": 7, "b": 2})
    result = service.reserve("a", 3, "r1")
    assert result["ok"] is True
    assert service.available("a") == 4
    assert len(service.reservations()) == 1


def case_invalid_quantity(service_type, _not_found, root: Path) -> None:
    service = service_type(root / "db.json", {"a": 2})
    for quantity in (0, -1):
        try:
            service.reserve("a", quantity, f"bad-{quantity}")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid quantity accepted")
    assert service.available("a") == 2


def case_reserve_idempotency(service_type, _not_found, root: Path) -> None:
    database = root / "db.json"
    service = service_type(database, {"a": 5})
    first = service.reserve("a", 2, "same")
    restarted = service_type(database)
    second = restarted.reserve("a", 4, "same")
    assert first == second
    assert restarted.available("a") == 3
    assert len(restarted.reservations()) == 1


def case_failed_request_can_retry(service_type, _not_found, root: Path) -> None:
    service = service_type(root / "db.json", {"a": 2})
    failed = service.reserve("a", 3, "retry-me")
    assert failed["ok"] is False
    held = service.reserve("a", 2, "other")
    service.cancel(held["reservation"]["id"], "free-stock")
    retried = service.reserve("a", 2, "retry-me")
    assert retried["ok"] is True
    assert service.available("a") == 0


def case_cancel_idempotency(service_type, _not_found, root: Path) -> None:
    database = root / "db.json"
    service = service_type(database, {"a": 5})
    reservation = service.reserve("a", 3, "r1")["reservation"]
    first = service.cancel(reservation["id"], "c1")
    second = service.cancel(reservation["id"], "c2")
    restarted = service_type(database)
    third = restarted.cancel(reservation["id"], "c3")
    assert first["reservation"]["status"] == "cancelled"
    assert second["reservation"]["status"] == "cancelled"
    assert third["reservation"]["status"] == "cancelled"
    assert restarted.available("a") == 5


def case_unknown_is_unchanged(service_type, not_found, root: Path) -> None:
    service = service_type(root / "db.json", {"a": 4})
    try:
        service.cancel("missing", "c1")
    except not_found:
        pass
    else:
        raise AssertionError("missing reservation did not raise ReservationNotFound")
    assert service.available("a") == 4


def case_invariant_sequence(service_type, _not_found, root: Path) -> None:
    database = root / "db.json"
    service = service_type(database, {"a": 9})
    reservations = []
    for index, quantity in enumerate((1, 2, 3)):
        reservations.append(service.reserve("a", quantity, f"r{index}")["reservation"])
    service.cancel(reservations[1]["id"], "c1")
    service.cancel(reservations[1]["id"], "c2")
    restarted = service_type(database)
    active = sum(
        item["quantity"]
        for item in restarted.reservations()
        if item["status"] == "active"
    )
    assert restarted.available("a") + active == 9


def case_atomic_replace(service_type, _not_found, root: Path) -> None:
    database = root / "nested" / "db.json"
    service = service_type(database, {"a": 3})
    service.reserve("a", 1, "r1")
    parsed = json.loads(database.read_text(encoding="utf-8"))
    assert parsed["available"]["a"] == 2
    leftovers = [p for p in database.parent.iterdir() if p != database]
    assert not leftovers, f"temporary files left behind: {leftovers}"


CAPABILITIES: dict[str, tuple[float, list[Callable]]] = {
    "basic_behavior": (25, [case_basic, case_invalid_quantity]),
    "reserve_idempotency": (25, [case_reserve_idempotency, case_failed_request_can_retry]),
    "cancel_idempotency": (20, [case_cancel_idempotency]),
    "restart_and_invariants": (20, [case_unknown_is_unchanged, case_invariant_sequence]),
    "persistence_hygiene": (10, [case_atomic_replace]),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    critical: list[str] = []
    details: dict[str, dict] = {}
    total = 0.0
    try:
        service_type, not_found = load_service(args.submission.resolve())
    except Exception as exc:
        print(json.dumps({
            "completion_score": 0,
            "critical_failures": [f"public API unavailable: {type(exc).__name__}: {exc}"],
            "capabilities": {},
            "evaluator": {"version": "0.1.0"},
        }))
        return 0

    for name, (weight, cases) in CAPABILITIES.items():
        passed = 0
        failures = []
        for index, case in enumerate(cases):
            with tempfile.TemporaryDirectory() as directory:
                try:
                    case(service_type, not_found, Path(directory))
                    passed += 1
                except Exception as exc:
                    failures.append(f"{case.__name__}: {type(exc).__name__}: {exc}")
        earned = weight * passed / len(cases)
        total += earned
        details[name] = {"earned": earned, "weight": weight, "passed": passed, "total": len(cases), "failures": failures}

    if details["basic_behavior"]["passed"] == 0:
        critical.append("basic reservation behavior is unavailable")
    print(json.dumps({
        "completion_score": round(total, 2),
        "critical_failures": critical,
        "capabilities": details,
        "evaluator": {"version": "0.1.0"},
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
