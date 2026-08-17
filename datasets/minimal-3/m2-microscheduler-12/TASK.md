# Improve MicroScheduler-12

Implement `microscheduler.solve(instance)` so it returns a strong deterministic schedule for every valid instance. The starter contains a legal but deliberately weak greedy solver.

## Input

An instance is a dictionary with:

- `workers`: objects with unique `id` and a non-empty list of `skills`;
- `jobs`: objects with unique `id`, positive integer `duration`, non-negative `release_time`, integer `deadline`, positive integer `priority`, one required `skill`, a `family`, and a list of predecessor job IDs;
- `setup_time`: the non-negative delay required when a worker switches between different job families.

Instances contain 6–12 jobs and 2–3 workers. The predecessor graph is acyclic and every job has at least one capable worker.

## Output

Return a list containing exactly one record per job:

```python
{
    "job_id": "j1",
    "worker_id": "w1",
    "start": 0,
    "end": 3,
}
```

Jobs are non-preemptive. A schedule is valid only when:

- each worker executes at most one job at a time;
- the worker has the job's required skill;
- `end - start` equals the job duration;
- a job starts no earlier than its release time;
- every predecessor ends before the dependent job starts;
- switching family on the same worker leaves at least `setup_time` between jobs.

## Optimization order

Among valid schedules, improve these objectives in order:

1. weighted tardiness: `sum(priority * max(0, end - deadline))`;
2. makespan: the latest job end;
3. number of family switches.

Do not special-case the public examples. The result must be deterministic for identical input and each instance must complete within two seconds. Use only the Python standard library and preserve the public API.

## Public verification

```bash
python -m unittest discover -s public-tests -v
```

Implement the solver, run relevant checks, and briefly describe the strategy and its complexity.
