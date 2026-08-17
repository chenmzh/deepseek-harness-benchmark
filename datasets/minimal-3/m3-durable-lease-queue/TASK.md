# Complete the durable lease queue

Finish the dependency-free JSON-backed queue exposed as `leasequeue.DurableQueue`. Preserve the documented public API.

## API

```python
DurableQueue(database, max_attempts=3, base_backoff=5)
enqueue(payload, idempotency_key)
claim(worker_id, lease_seconds, now)
ack(job_id, worker_id)
fail(job_id, worker_id, error, now)
recover_expired(now)
jobs()
```

`now` and `lease_seconds` are non-negative integer seconds supplied by the caller. Do not read the wall clock internally.

## Required behavior

- `enqueue` returns a job. Reusing an idempotency key returns the original job and never enqueues twice.
- `claim` returns the oldest eligible queued job or `None`. It records the lease owner and `lease_until = now + lease_seconds`.
- A queued job is eligible only when `available_at <= now`.
- A leased job cannot be claimed by another worker before its lease expires.
- `claim` must recover expired leases before choosing work.
- `ack` and `fail` are accepted only from the current lease owner; otherwise raise `LeaseConflict`.
- `ack` transitions a leased job to `succeeded` and is idempotent for the same worker.
- Each claim increments `attempts`.
- `fail` records the error. When attempts remain, it requeues the job with `available_at = now + base_backoff * 2 ** (attempts - 1)`. Otherwise it moves to `dead`.
- An expired lease follows the same retry/dead-letter rule using its `lease_until` as the failure time.
- Queue state and idempotency keys survive restart.
- Persistence must atomically replace the old JSON file and must not leave temporary files after a successful operation.

Validate positive lease durations and non-empty worker and idempotency IDs. Keep deterministic FIFO ordering for jobs with equal eligibility.

Use only Python 3.11+ standard-library modules. Do not modify public tests.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```

Implement the queue, run relevant checks, and briefly report what changed and what you verified.
