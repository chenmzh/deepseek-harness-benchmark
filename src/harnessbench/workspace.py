from __future__ import annotations

from pathlib import Path
import shutil

from .manifest import TaskManifest


class WorkspaceError(RuntimeError):
    """Raised when preparing an isolated task workspace fails safely."""


def prepare_workspace(manifest: TaskManifest, destination: str | Path) -> Path:
    destination = Path(destination).resolve()
    if destination.exists():
        raise WorkspaceError(f"destination already exists: {destination}")

    destination.mkdir(parents=True)
    try:
        starter = manifest.task_dir / "starter"
        for child in starter.iterdir():
            target = destination / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)
        shutil.copy2(manifest.task_dir / "TASK.md", destination / "TASK.md")
        shutil.copytree(
            manifest.task_dir / "public-tests", destination / "public-tests"
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination
