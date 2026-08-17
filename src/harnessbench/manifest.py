from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any


class ManifestError(ValueError):
    """Raised when a dataset or task manifest violates the benchmark contract."""


@dataclass(frozen=True)
class TaskManifest:
    path: Path
    task_id: str
    slug: str
    title: str
    version: str
    language: str
    timeout_seconds: int
    evaluator_timeout_seconds: int
    memory_mb: int
    cpu_count: int
    ship_ready_score: float
    private_scorer: str

    @property
    def task_dir(self) -> Path:
        return self.path.parent


@dataclass(frozen=True)
class DatasetManifest:
    path: Path
    dataset_id: str
    version: str
    title: str
    one_shot: bool
    task_dirs: tuple[str, ...]

    @property
    def dataset_dir(self) -> Path:
        return self.path.parent


def _table(data: dict[str, Any], name: str, source: Path) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ManifestError(f"{source}: missing [{name}] table")
    return value


def _required(table: dict[str, Any], key: str, expected: type, source: Path) -> Any:
    value = table.get(key)
    if not isinstance(value, expected):
        raise ManifestError(
            f"{source}: {key!r} must be {expected.__name__}, got {type(value).__name__}"
        )
    return value


def load_task_manifest(task_dir: str | Path) -> TaskManifest:
    task_dir = Path(task_dir).resolve()
    path = task_dir / "task.toml"
    if not path.is_file():
        raise ManifestError(f"missing task manifest: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    task = _table(data, "task", path)
    limits = _table(data, "limits", path)
    evaluator = _table(data, "evaluator", path)
    manifest = TaskManifest(
        path=path,
        task_id=_required(task, "id", str, path),
        slug=_required(task, "slug", str, path),
        title=_required(task, "title", str, path),
        version=_required(task, "version", str, path),
        language=_required(task, "language", str, path),
        timeout_seconds=_required(limits, "timeout_seconds", int, path),
        evaluator_timeout_seconds=_required(
            limits, "evaluator_timeout_seconds", int, path
        ),
        memory_mb=_required(limits, "memory_mb", int, path),
        cpu_count=_required(limits, "cpu_count", int, path),
        ship_ready_score=float(_required(evaluator, "ship_ready_score", int, path)),
        private_scorer=_required(evaluator, "private_scorer", str, path),
    )
    validate_task_files(manifest)
    return manifest


def validate_task_files(manifest: TaskManifest) -> None:
    required = [
        manifest.task_dir / "TASK.md",
        manifest.task_dir / "starter",
        manifest.task_dir / "public-tests",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ManifestError("missing task assets: " + ", ".join(missing))
    if not 0 <= manifest.ship_ready_score <= 100:
        raise ManifestError(f"{manifest.path}: ship_ready_score must be within 0..100")
    if manifest.timeout_seconds <= 0 or manifest.evaluator_timeout_seconds <= 0:
        raise ManifestError(f"{manifest.path}: timeouts must be positive")


def load_dataset_manifest(dataset_dir: str | Path) -> DatasetManifest:
    dataset_dir = Path(dataset_dir).resolve()
    path = dataset_dir / "dataset.toml"
    if not path.is_file():
        raise ManifestError(f"missing dataset manifest: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    dataset = _table(data, "dataset", path)
    tasks = dataset.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(item, str) for item in tasks):
        raise ManifestError(f"{path}: tasks must be an array of task directory names")
    result = DatasetManifest(
        path=path,
        dataset_id=_required(dataset, "id", str, path),
        version=_required(dataset, "version", str, path),
        title=_required(dataset, "title", str, path),
        one_shot=_required(dataset, "one_shot", bool, path),
        task_dirs=tuple(tasks),
    )
    seen: set[str] = set()
    for task_name in result.task_dirs:
        task = load_task_manifest(result.dataset_dir / task_name)
        if task.task_id in seen:
            raise ManifestError(f"{path}: duplicate task id {task.task_id}")
        seen.add(task.task_id)
    return result
