from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile


def load_api(submission: Path):
    sys.path.insert(0, str(submission))
    for name in list(sys.modules):
        if name == "leasequeue" or name.startswith("leasequeue."):
            del sys.modules[name]
    module = importlib.import_module("leasequeue")
    return module.DurableQueue, module.JobNotFound, module.LeaseConflict


def basic(queue_type, _missing, _conflict, root: Path) -> None:
    queue = queue_type(root / "q.json")
    first = queue.enqueue({"x": 1}, "k1")
    second = queue.enqueue({"x": 2}, "k2")
    claimed = queue.claim("a", 10, 100)
    assert claimed["id"] == first["id"] and claimed["attempts"] == 1
    assert claimed["lease_until"] == 110
    assert queue.ack(first["id"], "a")["state"] == "succeeded"
    assert queue.claim("a", 10, 100)["id"] == second["id"]


def idempotency(queue_type, _missing, conflict, root: Path) -> None:
    database = root / "q.json"
    queue = queue_type(database)
    first = queue.enqueue({"x": 1}, "stable")
    restarted = queue_type(database)
    assert restarted.enqueue({"x": 999}, "stable")["id"] == first["id"]
    assert len(restarted.jobs()) == 1
    restarted.claim("a", 5, 0)
    acknowledged = restarted.ack(first["id"], "a")
    assert restarted.ack(first["id"], "a") == acknowledged
    try:
        restarted.ack(first["id"], "b")
    except conflict:
        pass
    else:
        raise AssertionError("ack by a different worker was accepted")


def lease_semantics(queue_type, _missing, conflict, root: Path) -> None:
    queue = queue_type(root / "q.json", max_attempts=3, base_backoff=5)
    job = queue.enqueue({}, "k")
    queue.claim("a", 10, 100)
    assert queue.claim("b", 10, 109) is None
    for operation in (
        lambda: queue.ack(job["id"], "b"),
        lambda: queue.fail(job["id"], "b", "bad", 101),
    ):
        try:
            operation()
        except conflict:
            pass
        else:
            raise AssertionError("wrong lease owner was accepted")
    assert queue.claim("b", 10, 110) is None
    assert queue.claim("b", 10, 114) is None
    retried = queue.claim("b", 10, 115)
    assert retried["id"] == job["id"] and retried["attempts"] == 2


def retry_and_dead_letter(queue_type, _missing, _conflict, root: Path) -> None:
    queue = queue_type(root / "q.json", max_attempts=2, base_backoff=3)
    job = queue.enqueue({}, "k")
    queue.claim("a", 5, 0)
    failed = queue.fail(job["id"], "a", "first", 1)
    assert failed["state"] == "queued" and failed["available_at"] == 4
    assert queue.claim("a", 5, 3) is None
    assert queue.claim("a", 5, 4)["attempts"] == 2
    dead = queue.fail(job["id"], "a", "second", 5)
    assert dead["state"] == "dead" and dead["last_error"] == "second"
    assert queue.claim("a", 5, 100) is None


def persistence(queue_type, _missing, _conflict, root: Path) -> None:
    database = root / "nested" / "q.json"
    queue = queue_type(database)
    original_inode = database.stat().st_ino
    job = queue.enqueue({"nested": [1, 2]}, "k")
    assert database.stat().st_ino != original_inode, "database was overwritten in place"
    queue.claim("a", 5, 10)
    restarted = queue_type(database)
    row = next(item for item in restarted.jobs() if item["id"] == job["id"])
    assert row["state"] == "leased" and row["lease_owner"] == "a"
    json.loads(database.read_text(encoding="utf-8"))
    assert [path for path in database.parent.iterdir() if path != database] == []


def validation(queue_type, _missing, _conflict, root: Path) -> None:
    queue = queue_type(root / "q.json")
    for call in (
        lambda: queue.enqueue({}, ""),
        lambda: queue.claim("", 2, 0),
        lambda: queue.claim("a", 0, 0),
    ):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input was accepted")


CAPABILITIES = {
    "basic_state_machine": (25, [basic]),
    "lease_semantics": (20, [lease_semantics]),
    "idempotency": (15, [idempotency]),
    "retry_and_dead_letter": (15, [retry_and_dead_letter]),
    "restart_and_persistence": (15, [persistence]),
    "input_contract": (10, [validation]),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    try:
        api = load_api(args.submission.resolve())
    except Exception as exc:
        print(json.dumps({"completion_score": 0, "critical_failures": [f"public API unavailable: {type(exc).__name__}: {exc}"], "capabilities": {}, "evaluator": {"version": "0.2.0"}}))
        return 0

    total = 0.0
    details = {}
    for name, (weight, cases) in CAPABILITIES.items():
        passed = 0
        failures = []
        for case in cases:
            with tempfile.TemporaryDirectory() as directory:
                try:
                    case(*api, Path(directory))
                    passed += 1
                except Exception as exc:
                    failures.append(f"{case.__name__}: {type(exc).__name__}: {exc}")
        earned = weight * passed / len(cases)
        total += earned
        details[name] = {"earned": earned, "weight": weight, "passed": passed, "total": len(cases), "failures": failures}
    critical = []
    if details["basic_state_machine"]["passed"] == 0:
        critical.append("basic queue state machine is unavailable")
    if details["lease_semantics"]["passed"] == 0:
        critical.append("lease exclusivity is unavailable")
    print(json.dumps({"completion_score": round(total, 2), "critical_failures": critical, "capabilities": details, "evaluator": {"version": "0.2.0"}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
