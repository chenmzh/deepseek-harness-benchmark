from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .manifest import TaskManifest


class EvaluationError(RuntimeError):
    """Raised when a private evaluator cannot produce a trustworthy result."""


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".git/") or "__pycache__" in relative.split("/"):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _required_capability_failures(
    required: tuple[str, ...], capabilities: Any
) -> list[str]:
    if not isinstance(capabilities, dict):
        return [f"required capability unavailable: {name}" for name in required]

    failures: list[str] = []
    for name in required:
        detail = capabilities.get(name)
        if not isinstance(detail, dict):
            failures.append(f"required capability unavailable: {name}")
            continue
        earned = detail.get("earned")
        weight = detail.get("weight")
        if not isinstance(earned, (int, float)) or not isinstance(weight, (int, float)):
            failures.append(f"required capability has invalid score metadata: {name}")
            continue
        if earned < weight:
            failures.append(f"required capability incomplete: {name} ({earned:g}/{weight:g})")
    return failures


def evaluate_submission(
    manifest: TaskManifest,
    submission: str | Path,
    private_root: str | Path,
) -> dict[str, Any]:
    submission = Path(submission).resolve()
    private_root = Path(private_root).resolve()
    if not submission.is_dir():
        raise EvaluationError(f"submission is not a directory: {submission}")

    scorer = (private_root / manifest.private_scorer).resolve()
    try:
        scorer.relative_to(private_root)
    except ValueError as exc:
        raise EvaluationError("private scorer escapes private root") from exc
    if not scorer.is_file():
        raise EvaluationError(f"missing private scorer: {scorer}")

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [sys.executable, str(scorer), "--submission", str(submission)],
        cwd=private_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=manifest.evaluator_timeout_seconds,
        check=False,
    )
    if process.returncode != 0:
        raise EvaluationError(
            f"scorer exited {process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    try:
        score = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"scorer returned invalid JSON: {process.stdout!r}") from exc

    completion = float(score.get("completion_score", -1))
    if not 0 <= completion <= 100:
        raise EvaluationError("completion_score must be within 0..100")
    critical = score.get("critical_failures", [])
    if not isinstance(critical, list) or not all(isinstance(item, str) for item in critical):
        raise EvaluationError("critical_failures must be a list of strings")

    capabilities = score.get("capabilities", {})
    critical = [*critical, *_required_capability_failures(manifest.required_capabilities, capabilities)]

    result: dict[str, Any] = {
        "schema_version": "0.1",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": manifest.task_id,
        "task_version": manifest.version,
        "submission_sha256": tree_digest(submission),
        "completion_score": completion,
        "ship_ready": completion >= manifest.ship_ready_score and not critical,
        "critical_failures": critical,
        "capabilities": capabilities,
        "evaluator": score.get("evaluator", {}),
    }
    for key in ("optimizer_quality", "notes"):
        if key in score:
            result[key] = score[key]
    return result
