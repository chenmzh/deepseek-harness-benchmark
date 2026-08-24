from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys


def load_api(submission: Path):
    sys.path.insert(0, str(submission))
    for name in list(sys.modules):
        if name == "configmerge" or name.startswith("configmerge."):
            del sys.modules[name]
    module = importlib.import_module("configmerge")
    return module.resolve, module.ConfigError


def basic(resolve, _error):
    assert resolve() == {}
    assert resolve({"a": 1}, {"a": 2}, {"b": 3}) == {"a": 2, "b": 3}
    assert resolve({"a": {"x": 1}}, {"a": 4}) == {"a": 4}


def recursive(resolve, _error):
    assert resolve(
        {"service": {"host": "a", "tls": {"enabled": False, "ca": "x"}}},
        {"service": {"tls": {"enabled": True}}},
    ) == {"service": {"host": "a", "tls": {"enabled": True, "ca": "x"}}}


def deletion(resolve, _error):
    assert resolve(
        {"a": 1, "nested": {"keep": 2, "drop": 3}},
        {"a": None, "nested": {"drop": None, "missing": None}},
    ) == {"nested": {"keep": 2}}


def isolation_and_validation(resolve, error):
    lower = {"nested": {"items": [1, {"x": 2}]}}
    result = resolve(lower)
    result["nested"]["items"][1]["x"] = 99
    assert lower["nested"]["items"][1]["x"] == 2
    for bad in ({"": 1}, {"a": {1: "x"}}, {"a": [object()]}, []):
        try:
            resolve(bad)
        except error:
            pass
        else:
            raise AssertionError(f"invalid layer accepted: {bad!r}")


CAPABILITIES = {
    "precedence_and_replacement": (25, basic),
    "recursive_merge": (25, recursive),
    "deletion_semantics": (25, deletion),
    "isolation_and_validation": (25, isolation_and_validation),
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
    for name, (weight, case) in CAPABILITIES.items():
        failures = []
        try:
            case(*api)
            earned = float(weight)
        except Exception as exc:
            earned = 0.0
            failures.append(f"{case.__name__}: {type(exc).__name__}: {exc}")
        total += earned
        details[name] = {"earned": earned, "weight": weight, "passed": int(not failures), "total": 1, "failures": failures}
    critical = [] if details["precedence_and_replacement"]["passed"] else ["basic configuration resolution is unavailable"]
    print(json.dumps({"completion_score": round(total, 2), "critical_failures": critical, "capabilities": details, "evaluator": {"version": "0.1.0"}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
