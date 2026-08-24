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
        if name == "ttlstore" or name.startswith("ttlstore."):
            del sys.modules[name]
    module = importlib.import_module("ttlstore")
    return module.VersionedTTLStore, module.MissingKey, module.VersionConflict


def basic(store_type, _missing, _conflict, root):
    store = store_type(root / "s.json", ttl=5)
    row = store.put("b", {"x": [1]}, "r1", 10)
    assert row == {"key": "b", "value": {"x": [1]}, "version": 1, "expires_at": 15}
    assert store.get("b", 14) == row
    assert [item["key"] for item in store.items(14)] == ["b"]


def expiry_and_versions(store_type, missing, _conflict, root):
    store = store_type(root / "s.json", ttl=2)
    assert store.put("a", 1, "r1", 0)["version"] == 1
    assert store.get("a", 2) is None
    second = store.put("a", 2, "r2", 3)
    assert second["version"] == 2 and second["expires_at"] == 5
    try:
        store.compare_and_swap("a", 2, 3, "late", 5)
    except missing:
        pass
    else:
        raise AssertionError("CAS accepted an expired record")
    assert store.put("a", 4, "late", 6)["version"] == 3


def cas(store_type, _missing, conflict, root):
    store = store_type(root / "s.json")
    first = store.put("a", 1, "p", 0)
    try:
        store.compare_and_swap("a", first["version"] + 1, 2, "c", 1)
    except conflict:
        pass
    else:
        raise AssertionError("stale version accepted")
    updated = store.compare_and_swap("a", first["version"], 2, "c", 1)
    assert updated["version"] == 2 and updated["value"] == 2


def idempotency(store_type, _missing, _conflict, root):
    database = root / "s.json"
    store = store_type(database)
    first = store.put("a", {"x": 1}, "same", 0)
    restarted = store_type(database)
    assert restarted.put("other", 999, "same", 50) == first
    assert restarted.get("other", 50) is None
    try:
        restarted.compare_and_swap("a", 99, 2, "retry", 1)
    except Exception:
        pass
    else:
        raise AssertionError("invalid CAS unexpectedly succeeded")
    assert restarted.compare_and_swap("a", 1, 2, "retry", 1)["version"] == 2


def deletion(store_type, missing, conflict, root):
    store = store_type(root / "s.json")
    row = store.put("a", 1, "p", 0)
    try:
        store.delete("a", row["version"] + 1, "bad", 1)
    except conflict:
        pass
    else:
        raise AssertionError("delete accepted stale version")
    result = store.delete("a", row["version"], "good", 1)
    assert result == {"key": "a", "version": 1, "deleted": True}
    assert store.delete("missing", 99, "good", 20) == result
    try:
        store.delete("a", 1, "new", 2)
    except missing:
        pass
    else:
        raise AssertionError("missing key was deleted")


def isolation_and_validation(store_type, _missing, _conflict, root):
    store = store_type(root / "s.json")
    value = {"nested": [1]}
    row = store.put("a", value, "r", 0)
    value["nested"].append(2)
    row["value"]["nested"].append(3)
    assert store.get("a", 0)["value"] == {"nested": [1]}
    for call in (
        lambda: store_type(root / "bad.json", ttl=0),
        lambda: store.put("", 1, "x", 0),
        lambda: store.put("x", object(), "x", 0),
        lambda: store.get("x", -1),
    ):
        try:
            call()
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("invalid input accepted")


def persistence(store_type, _missing, _conflict, root):
    database = root / "nested" / "s.json"
    store = store_type(database)
    row = store.put("a", 1, "p", 0)
    original_inode = database.stat().st_ino
    store.compare_and_swap("a", 1, 2, "c", 1)
    assert database.stat().st_ino != original_inode, "database was overwritten in place"
    restarted = store_type(database)
    assert row["version"] == 1
    assert restarted.get("a", 1)["version"] == 2
    assert [path for path in database.parent.iterdir() if path != database] == []
    json.loads(database.read_text(encoding="utf-8"))


CAPABILITIES = {
    "basic_store": (20, [basic]),
    "expiry_and_version_history": (15, [expiry_and_versions]),
    "compare_and_swap": (15, [cas]),
    "request_idempotency": (15, [idempotency]),
    "delete_semantics": (10, [deletion]),
    "isolation_and_input_contract": (10, [isolation_and_validation]),
    "restart_and_atomic_persistence": (15, [persistence]),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    try:
        api = load_api(args.submission.resolve())
    except Exception as exc:
        print(json.dumps({"completion_score": 0, "critical_failures": [f"public API unavailable: {type(exc).__name__}: {exc}"], "capabilities": {}, "evaluator": {"version": "0.1.0"}}))
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
    critical = [] if details["basic_store"]["passed"] else ["basic TTL store behavior is unavailable"]
    print(json.dumps({"completion_score": round(total, 2), "critical_failures": critical, "capabilities": details, "evaluator": {"version": "0.1.0"}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
