from __future__ import annotations

from typing import Any


def solve(instance: dict[str, Any]) -> list[dict[str, int | str]]:
    """Return a valid deterministic baseline schedule.

    The baseline chooses the earliest-deadline ready job and assigns it to the
    capable worker that can finish it first. It is intentionally myopic.
    """
    jobs = {job["id"]: job for job in instance["jobs"]}
    workers = {worker["id"]: worker for worker in instance["workers"]}
    pending = set(jobs)
    ends: dict[str, int] = {}
    state = {
        worker_id: {"available": 0, "family": None}
        for worker_id in workers
    }
    schedule: list[dict[str, int | str]] = []
    setup_time = int(instance["setup_time"])

    while pending:
        ready = [
            jobs[job_id]
            for job_id in pending
            if all(predecessor in ends for predecessor in jobs[job_id]["predecessors"])
        ]
        if not ready:
            raise ValueError("predecessor graph is cyclic")
        job = min(ready, key=lambda item: (item["deadline"], -item["priority"], item["id"]))
        predecessor_end = max((ends[item] for item in job["predecessors"]), default=0)
        choices = []
        for worker_id, worker in workers.items():
            if job["skill"] not in worker["skills"]:
                continue
            switch = setup_time if state[worker_id]["family"] not in (None, job["family"]) else 0
            start = max(
                int(job["release_time"]),
                predecessor_end,
                int(state[worker_id]["available"]) + switch,
            )
            choices.append((start + int(job["duration"]), start, worker_id))
        end, start, worker_id = min(choices)
        schedule.append({
            "job_id": job["id"],
            "worker_id": worker_id,
            "start": start,
            "end": end,
        })
        state[worker_id] = {"available": end, "family": job["family"]}
        ends[job["id"]] = end
        pending.remove(job["id"])
    return schedule
