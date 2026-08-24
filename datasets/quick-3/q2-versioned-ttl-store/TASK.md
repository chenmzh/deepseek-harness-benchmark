# Complete the versioned TTL store

Finish the dependency-free JSON-backed `ttlstore.VersionedTTLStore` without changing its public API.

## API

```python
VersionedTTLStore(database, ttl=10)
put(key, value, request_id, now)
get(key, now)
compare_and_swap(key, expected_version, value, request_id, now)
delete(key, expected_version, request_id, now)
items(now)
```

`now` is a caller-supplied non-negative integer. The implementation must not read the wall clock.

## Required behavior

- `ttl` is a positive integer. Keys and request IDs are non-empty strings.
- Values must be JSON-serializable. Public results must not share mutable values with caller inputs or internal state.
- `put` creates or replaces a key, increments that key's persistent version, and sets `expires_at = now + ttl`.
- A record is live only while `now < expires_at`. `get` returns `None` for an expired or missing key.
- Expiration removes the live record but does not reset the key's version history. `items(now)` purges expired records and returns live records sorted by key.
- `compare_and_swap` requires a live key with exactly `expected_version`; otherwise raise `MissingKey` or `VersionConflict`. A success increments the version and refreshes expiry.
- `delete` requires a live key with exactly `expected_version`, removes it, and returns `{"key": key, "version": expected_version, "deleted": True}`.
- Successful mutating requests are idempotent by `request_id`, including after restart. Repeating one returns its original result and makes no new change, even if other arguments differ.
- Failed requests do not consume their request ID and may be retried later.
- All state, version history, and successful request results survive restart.
- Each state change atomically replaces the JSON database. A successful operation leaves no temporary files.

Use only Python 3.11+ standard-library modules. Do not modify the public tests.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```
