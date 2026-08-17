from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import subprocess
import sys
from typing import Any


HERE = Path(__file__).resolve().parent


def make_instance(family: str, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    count = 6 + seed % 7
    skills = ["cut", "pack", "paint"]
    workers = [
        {"id": "w1", "skills": ["cut", "pack"]},
        {"id": "w2", "skills": ["pack", "paint"]},
        {"id": "w3", "skills": skills},
    ][: 2 + seed % 2]
    covered = sorted({skill for worker in workers for skill in worker["skills"]})
    jobs = []
    for index in range(count):
        duration = rng.randint(1, 5)
        release = rng.randint(0, 3) if family != "tight_deadline" else 0
        deadline = release + duration + rng.randint(1, 8)
        priority = rng.randint(1, 5)
        predecessors: list[str] = []
        if family == "precedence" and index > 1 and rng.random() < 0.65:
            predecessors.append(f"j{rng.randrange(index)}")
        jobs.append({
            "id": f"j{index}",
            "duration": duration,
            "release_time": release,
            "deadline": deadline,
            "priority": priority,
            "skill": rng.choice(covered),
            "family": chr(ord("a") + (index % 3 if family == "setup" else rng.randrange(3))),
            "predecessors": predecessors,
        })
    if family == "skill_bottleneck":
        scarce = workers[0]["skills"][0]
        for job in jobs[::2]:
            job["skill"] = scarce
            job["priority"] += 2
    if family == "tight_deadline":
        for index, job in enumerate(jobs):
            job["deadline"] = 2 + index // len(workers) + job["duration"]
    return {
        "workers": workers,
        "jobs": jobs,
        "setup_time": 3 if family == "setup" else 1,
    }


def run_candidate(submission: Path, instance: dict[str, Any]) -> tuple[list[dict] | None, str | None]:
    try:
        process = subprocess.run(
            [sys.executable, str(HERE / "run_candidate.py"), str(submission)],
            input=json.dumps(instance),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if process.returncode != 0:
        return None, f"candidate exited {process.returncode}: {process.stderr[-300:]}"
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError:
        return None, "candidate returned invalid JSON"
    return value, None


def baseline(instance: dict[str, Any]) -> list[dict]:
    jobs = {job["id"]: job for job in instance["jobs"]}
    workers = {worker["id"]: worker for worker in instance["workers"]}
    pending = set(jobs)
    ends: dict[str, int] = {}
    state = {worker_id: {"end": 0, "family": None} for worker_id in workers}
    result = []
    while pending:
        ready = [jobs[job_id] for job_id in pending if all(item in ends for item in jobs[job_id]["predecessors"])]
        job = min(ready, key=lambda item: (item["deadline"], -item["priority"], item["id"]))
        dependency_end = max((ends[item] for item in job["predecessors"]), default=0)
        choices = []
        for worker_id, worker in workers.items():
            if job["skill"] not in worker["skills"]:
                continue
            setup = instance["setup_time"] if state[worker_id]["family"] not in (None, job["family"]) else 0
            start = max(job["release_time"], dependency_end, state[worker_id]["end"] + setup)
            choices.append((start + job["duration"], start, worker_id))
        end, start, worker_id = min(choices)
        result.append({"job_id": job["id"], "worker_id": worker_id, "start": start, "end": end})
        state[worker_id] = {"end": end, "family": job["family"]}
        ends[job["id"]] = end
        pending.remove(job["id"])
    return result


def validate(instance: dict[str, Any], schedule: Any) -> tuple[bool, str]:
    if not isinstance(schedule, list):
        return False, "schedule is not a list"
    jobs = {job["id"]: job for job in instance["jobs"]}
    workers = {worker["id"]: worker for worker in instance["workers"]}
    if len(schedule) != len(jobs):
        return False, "wrong number of rows"
    try:
        rows = {row["job_id"]: row for row in schedule}
    except (TypeError, KeyError):
        return False, "malformed row"
    if len(rows) != len(schedule) or set(rows) != set(jobs):
        return False, "job IDs are missing or duplicated"
    for job_id, row in rows.items():
        job = jobs[job_id]
        if row.get("worker_id") not in workers:
            return False, f"unknown worker for {job_id}"
        if job["skill"] not in workers[row["worker_id"]]["skills"]:
            return False, f"skill mismatch for {job_id}"
        if type(row.get("start")) is not int or type(row.get("end")) is not int:
            return False, f"non-integer time for {job_id}"
        if row["start"] < job["release_time"] or row["end"] - row["start"] != job["duration"]:
            return False, f"invalid timing for {job_id}"
        for predecessor in job["predecessors"]:
            if rows[predecessor]["end"] > row["start"]:
                return False, f"precedence violation for {job_id}"
    for worker_id in workers:
        assigned = sorted((row for row in schedule if row["worker_id"] == worker_id), key=lambda row: (row["start"], row["job_id"]))
        for previous, current in zip(assigned, assigned[1:]):
            delay = instance["setup_time"] if jobs[previous["job_id"]]["family"] != jobs[current["job_id"]]["family"] else 0
            if current["start"] < previous["end"] + delay:
                return False, f"worker overlap or setup violation on {worker_id}"
    return True, ""


def objectives(instance: dict[str, Any], schedule: list[dict]) -> tuple[int, int, int]:
    jobs = {job["id"]: job for job in instance["jobs"]}
    tardiness = sum(jobs[row["job_id"]]["priority"] * max(0, row["end"] - jobs[row["job_id"]]["deadline"]) for row in schedule)
    makespan = max(row["end"] for row in schedule)
    switches = 0
    for worker in instance["workers"]:
        assigned = sorted((row for row in schedule if row["worker_id"] == worker["id"]), key=lambda row: row["start"])
        switches += sum(jobs[a["job_id"]]["family"] != jobs[b["job_id"]]["family"] for a, b in zip(assigned, assigned[1:]))
    return tardiness, makespan, switches


def lower_bounds(instance: dict[str, Any]) -> tuple[int, int, int]:
    durations = [job["duration"] for job in instance["jobs"]]
    makespan = max(max(durations), math.ceil(sum(durations) / len(instance["workers"])))
    return 0, makespan, 0


def normalized(candidate: int, base: int, target: int) -> float:
    if target >= base:
        return 1.0 if candidate <= target else 0.0
    return max(0.0, min(1.0, (base - candidate) / (base - target)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    instances = [make_instance(family, seed) for family in ("tight_deadline", "skill_bottleneck", "precedence", "setup") for seed in range(11, 17)]
    targets = json.loads((HERE / "targets.json").read_text(encoding="utf-8"))
    if len(targets) != len(instances):
        raise RuntimeError("frozen target count does not match hidden instance count")
    valid_count = 0
    errors = []
    tardiness_q = []
    makespan_q = []
    switch_q = []
    deterministic = True
    for index, instance in enumerate(instances):
        schedule, error = run_candidate(args.submission.resolve(), instance)
        if error:
            errors.append(f"instance {index}: {error}")
            continue
        valid, reason = validate(instance, schedule)
        if not valid:
            errors.append(f"instance {index}: {reason}")
            continue
        valid_count += 1
        candidate_values = objectives(instance, schedule)
        base_values = objectives(instance, baseline(instance))
        target_values = targets[index]["best_known"]
        tardiness_q.append(normalized(candidate_values[0], base_values[0], target_values[0]))
        makespan_q.append(normalized(candidate_values[1], base_values[1], target_values[1]))
        switch_q.append(normalized(candidate_values[2], base_values[2], target_values[2]))
        if index < 3:
            repeated, repeated_error = run_candidate(args.submission.resolve(), instance)
            if repeated_error or repeated != schedule:
                deterministic = False

    count = len(instances)
    feasibility = 40 * valid_count / count
    tardiness_score = 30 * sum(tardiness_q) / count
    makespan_score = 12 * sum(makespan_q) / count
    switch_score = 8 * sum(switch_q) / count
    deterministic_score = 5 if deterministic and valid_count else 0
    api_score = 5 if valid_count == count else 5 * valid_count / count
    total = feasibility + tardiness_score + makespan_score + switch_score + deterministic_score + api_score
    critical = [] if valid_count == count else [f"{count - valid_count} hidden schedules were invalid or unavailable"]
    print(json.dumps({
        "completion_score": round(total, 2),
        "critical_failures": critical,
        "optimizer_quality": round((tardiness_score + makespan_score + switch_score) / 50, 4),
        "capabilities": {
            "feasibility": {"earned": round(feasibility, 2), "weight": 40, "valid": valid_count, "total": count},
            "weighted_tardiness": {"earned": round(tardiness_score, 2), "weight": 30},
            "makespan": {"earned": round(makespan_score, 2), "weight": 12},
            "family_switches": {"earned": round(switch_score, 2), "weight": 8},
            "determinism": {"earned": deterministic_score, "weight": 5},
            "api_contract": {"earned": round(api_score, 2), "weight": 5},
        },
        "notes": errors[:8],
        "evaluator": {"version": "0.1.0", "instances": count, "objective_target": "frozen best-known", "lower_bounds_retained": True},
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
