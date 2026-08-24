# Complete the async single-flight cache

Finish `singleflight.AsyncCache` without changing its public API. The cache wraps an async `loader(key)` callable. Time is supplied explicitly to `get`; do not read the wall clock.

## API

```python
AsyncCache(loader, ttl, stale_ttl)
await cache.get(key, now)
cache.invalidate(key)
cache.clear()
```

## Required behavior

- `ttl` and `stale_ttl` are non-negative numbers. Reject booleans, negative values, and non-numbers.
- A successful load started at `now` is fresh while `now < fresh_until`, where `fresh_until = load_start_now + ttl`.
- It is stale while `fresh_until <= now < stale_until`, where `stale_until = fresh_until + stale_ttl`.
- A fresh `get` returns the cached value without loading.
- A stale `get` returns the stale value immediately and starts one background refresh for that key.
- A miss or fully expired entry waits for a load.
- Concurrent loads for the same key are coalesced. Different keys may load concurrently.
- Loader failures on a miss or expired entry propagate to all current waiters and are not cached.
- A background refresh failure leaves the stale value usable until its original `stale_until`.
- Cancelling one waiter must not cancel a shared load needed by other waiters.
- `invalidate(key)` removes the entry. A load or refresh started before invalidation must not repopulate it when it finishes.
- `clear()` applies the same rule to every current entry and in-flight load.
- Mutable returned values must not share state with the cached value or with another caller's result.

Use only Python 3.11+ standard-library modules. Do not modify the public tests.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```
