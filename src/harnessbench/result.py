from __future__ import annotations

from copy import deepcopy
from typing import Any


class ResultError(ValueError):
    """Raised when operational metadata is incomplete or inconsistent."""


REQUIRED_METADATA = {
    "benchmark_version": str,
    "dataset": str,
    "harness_id": str,
    "session_id": str,
    "status": str,
    "wall_time_seconds": (int, float),
    "usage": dict,
    "tooling": dict,
}

REQUIRED_USAGE = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "credits",
)

REQUIRED_TOOLING = (
    "tool_calls",
    "failed_tool_calls",
    "test_cycles",
    "human_interventions",
)


def assemble_run_result(evaluation: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    for key, expected in REQUIRED_METADATA.items():
        if key not in metadata or not isinstance(metadata[key], expected):
            raise ResultError(f"metadata.{key} is missing or has the wrong type")
    if metadata["status"] not in {
        "completed",
        "timeout",
        "harness_failed",
        "invalid",
        "infrastructure_invalidated",
    }:
        raise ResultError("metadata.status is not recognized")
    if metadata["wall_time_seconds"] < 0:
        raise ResultError("metadata.wall_time_seconds must be non-negative")
    for key in REQUIRED_USAGE:
        if key not in metadata["usage"]:
            raise ResultError(f"metadata.usage.{key} is missing")
    for key in REQUIRED_TOOLING:
        if key not in metadata["tooling"]:
            raise ResultError(f"metadata.tooling.{key} is missing")
    if "task_id" not in evaluation or "completion_score" not in evaluation:
        raise ResultError("evaluation is missing task_id or completion_score")

    result = deepcopy(metadata)
    protected = {
        "schema_version",
        "evaluated_at",
        "task_id",
        "task_version",
        "submission_sha256",
        "completion_score",
        "ship_ready",
        "critical_failures",
        "capabilities",
        "evaluator",
        "optimizer_quality",
        "notes",
    }
    for key in protected:
        if key in evaluation:
            result[key] = deepcopy(evaluation[key])
    result["schema_version"] = "0.1"
    return result
