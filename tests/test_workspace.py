from pathlib import Path
import tempfile
import unittest

from harnessbench.manifest import load_task_manifest
from harnessbench.workspace import WorkspaceError, prepare_workspace


ROOT = Path(__file__).resolve().parents[1]


class WorkspaceTests(unittest.TestCase):
    def test_prepare_excludes_private_evaluator(self) -> None:
        task = ROOT / "datasets" / "minimal-3" / "m1-reservation-repair"
        manifest = load_task_manifest(task)
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "workspace"
            prepare_workspace(manifest, destination)
            self.assertTrue((destination / "TASK.md").is_file())
            self.assertTrue((destination / "reservation").is_dir())
            self.assertFalse((destination / "private").exists())

    def test_prepare_refuses_existing_destination(self) -> None:
        task = ROOT / "datasets" / "minimal-3" / "m1-reservation-repair"
        manifest = load_task_manifest(task)
        with tempfile.TemporaryDirectory() as destination:
            with self.assertRaises(WorkspaceError):
                prepare_workspace(manifest, destination)


if __name__ == "__main__":
    unittest.main()
