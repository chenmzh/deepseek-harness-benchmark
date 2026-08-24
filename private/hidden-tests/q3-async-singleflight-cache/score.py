from __future__ import annotations

import argparse
import asyncio
import importlib
import json
from pathlib import Path
import sys


def load_api(submission: Path):
    sys.path.insert(0, str(submission))
    for name in list(sys.modules):
        if name == "singleflight" or name.startswith("singleflight."):
            del sys.modules[name]
    return importlib.import_module("singleflight").AsyncCache


async def settle_until(predicate, steps=20):
    for _ in range(steps):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("async operation did not reach the expected state")


async def basic(cache_type):
    calls = []

    async def loader(key):
        calls.append(key)
        return {"key": key, "items": []}

    cache = cache_type(loader, 5, 2)
    first = await cache.get("a", 0)
    second = await cache.get("a", 4.9)
    first["items"].append(1)
    second["items"].append(2)
    assert await cache.get("a", 4.9) == {"key": "a", "items": []}
    assert calls == ["a"]
    for bad in (-1, True, "1"):
        try:
            cache_type(loader, bad, 0)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("invalid ttl accepted")


async def coalescing(cache_type):
    gates = {"a": asyncio.Event(), "b": asyncio.Event()}
    calls = []

    async def loader(key):
        calls.append(key)
        await gates[key].wait()
        return key.upper()

    cache = cache_type(loader, 10, 0)
    a1 = asyncio.create_task(cache.get("a", 0))
    a2 = asyncio.create_task(cache.get("a", 1))
    b1 = asyncio.create_task(cache.get("b", 0))
    await settle_until(lambda: len(calls) == 2)
    assert sorted(calls) == ["a", "b"]
    gates["a"].set()
    gates["b"].set()
    assert await asyncio.gather(a1, a2, b1) == ["A", "A", "B"]
    assert calls.count("a") == 1


async def stale_refresh(cache_type):
    gate = asyncio.Event()
    calls = 0

    async def loader(_key):
        nonlocal calls
        calls += 1
        if calls == 2:
            await gate.wait()
        return calls

    cache = cache_type(loader, 5, 5)
    assert await cache.get("a", 0) == 1
    assert await cache.get("a", 5) == 1
    assert await cache.get("a", 6) == 1
    await asyncio.sleep(0)
    assert calls == 2
    gate.set()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert await cache.get("a", 9) == 2


async def errors_and_cancellation(cache_type):
    gate = asyncio.Event()
    calls = 0

    async def loader(_key):
        nonlocal calls
        calls += 1
        await gate.wait()
        if calls == 1:
            raise RuntimeError("boom")
        return "ok"

    cache = cache_type(loader, 1, 0)
    first = asyncio.create_task(cache.get("a", 0))
    second = asyncio.create_task(cache.get("a", 0))
    first.cancel()
    gate.set()
    try:
        await first
    except asyncio.CancelledError:
        pass
    try:
        await second
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("loader error did not propagate")
    gate.clear()
    retry = asyncio.create_task(cache.get("a", 1))
    await asyncio.sleep(0)
    gate.set()
    assert await retry == "ok"
    assert calls == 2


async def stale_error(cache_type):
    calls = 0

    async def loader(_key):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("refresh failed")
        return "old"

    cache = cache_type(loader, 2, 3)
    assert await cache.get("a", 0) == "old"
    assert await cache.get("a", 2) == "old"
    await asyncio.sleep(0)
    assert await cache.get("a", 4) == "old"
    try:
        await cache.get("a", 5)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expired stale value survived refresh failure")


async def invalidation(cache_type):
    gates = [asyncio.Event(), asyncio.Event()]
    calls = 0

    async def loader(_key):
        nonlocal calls
        index = calls
        calls += 1
        await gates[index].wait()
        return index

    cache = cache_type(loader, 10, 0)
    old = asyncio.create_task(cache.get("a", 0))
    await settle_until(lambda: calls == 1)
    cache.invalidate("a")
    gates[0].set()
    assert await old == 0
    new = asyncio.create_task(cache.get("a", 1))
    await settle_until(lambda: calls == 2)
    assert calls == 2
    gates[1].set()
    assert await new == 1
    cache.clear()
    assert calls == 2


CAPABILITIES = {
    "fresh_cache_and_isolation": (20, [basic]),
    "coalescing": (20, [coalescing]),
    "stale_while_revalidate": (20, [stale_refresh]),
    "error_and_cancellation": (20, [errors_and_cancellation, stale_error]),
    "invalidation_generation": (20, [invalidation]),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    try:
        cache_type = load_api(args.submission.resolve())
    except Exception as exc:
        print(json.dumps({"completion_score": 0, "critical_failures": [f"public API unavailable: {type(exc).__name__}: {exc}"], "capabilities": {}, "evaluator": {"version": "0.1.0"}}))
        return 0
    total = 0.0
    details = {}
    for name, (weight, cases) in CAPABILITIES.items():
        passed = 0
        failures = []
        for case in cases:
            try:
                asyncio.run(case(cache_type))
                passed += 1
            except Exception as exc:
                failures.append(f"{case.__name__}: {type(exc).__name__}: {exc}")
        earned = weight * passed / len(cases)
        total += earned
        details[name] = {"earned": earned, "weight": weight, "passed": passed, "total": len(cases), "failures": failures}
    critical = [] if details["fresh_cache_and_isolation"]["passed"] else ["basic async cache behavior is unavailable"]
    print(json.dumps({"completion_score": round(total, 2), "critical_failures": critical, "capabilities": details, "evaluator": {"version": "0.1.0"}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
