from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class State:
    scheduled: frozenset[str]
    worker_end: tuple[int, ...]
    worker_family: tuple[str | None, ...]
    job_end: tuple[int, ...]
    rows: tuple[tuple[str, str, int, int], ...]
    tardiness: int
    switches: int


def solve(instance: dict[str, Any]) -> list[dict[str, int | str]]:
    workers = sorted(instance["workers"], key=lambda item: item["id"])
    jobs = sorted(instance["jobs"], key=lambda item: item["id"])
    by_id = {job["id"]: job for job in jobs}
    job_index = {job["id"]: index for index, job in enumerate(jobs)}
    beam = [State(frozenset(), (0,) * len(workers), (None,) * len(workers), (-1,) * len(jobs), (), 0, 0)]
    width = 450

    for _ in jobs:
        candidates: dict[tuple, State] = {}
        for state in beam:
            ready = [
                job for job in jobs
                if job["id"] not in state.scheduled
                and all(item in state.scheduled for item in job["predecessors"])
            ]
            for job in ready:
                dependency_end = max((state.job_end[job_index[item]] for item in job["predecessors"]), default=0)
                for worker_pos, worker in enumerate(workers):
                    if job["skill"] not in worker["skills"]:
                        continue
                    switched = state.worker_family[worker_pos] not in (None, job["family"])
                    start = max(
                        job["release_time"],
                        dependency_end,
                        state.worker_end[worker_pos] + (instance["setup_time"] if switched else 0),
                    )
                    end = start + job["duration"]
                    worker_end = list(state.worker_end)
                    worker_end[worker_pos] = end
                    worker_family = list(state.worker_family)
                    worker_family[worker_pos] = job["family"]
                    job_end = list(state.job_end)
                    job_end[job_index[job["id"]]] = end
                    next_state = State(
                        state.scheduled | {job["id"]},
                        tuple(worker_end),
                        tuple(worker_family),
                        tuple(job_end),
                        state.rows + ((job["id"], worker["id"], start, end),),
                        state.tardiness + job["priority"] * max(0, end - job["deadline"]),
                        state.switches + int(switched),
                    )
                    signature = (next_state.scheduled, next_state.worker_end, next_state.worker_family, next_state.job_end)
                    previous = candidates.get(signature)
                    if previous is None or rank(previous, jobs, job_index) > rank(next_state, jobs, job_index):
                        candidates[signature] = next_state
        beam = sorted(candidates.values(), key=lambda state: rank(state, jobs, job_index))[:width]

    best = min(beam, key=lambda state: (state.tardiness, max(state.worker_end), state.switches, state.rows))
    return [
        {"job_id": job_id, "worker_id": worker_id, "start": start, "end": end}
        for job_id, worker_id, start, end in best.rows
    ]


def rank(state: State, jobs: list[dict], job_index: dict[str, int]) -> tuple:
    optimistic_tardiness = state.tardiness
    for job in jobs:
        if job["id"] in state.scheduled:
            continue
        dependency_end = max(
            (state.job_end[job_index[item]] for item in job["predecessors"] if state.job_end[job_index[item]] >= 0),
            default=0,
        )
        earliest_end = max(job["release_time"], dependency_end) + job["duration"]
        optimistic_tardiness += job["priority"] * max(0, earliest_end - job["deadline"])
    return (optimistic_tardiness, state.tardiness, max(state.worker_end), state.switches, state.rows)
