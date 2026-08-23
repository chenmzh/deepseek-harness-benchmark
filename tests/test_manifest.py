from pathlib import Path
import tempfile
import unittest

from harnessbench.manifest import ManifestError, load_dataset_manifest, load_task_manifest


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_minimal_dataset_is_valid(self) -> None:
        dataset = load_dataset_manifest(ROOT / "datasets" / "minimal-3")
        self.assertEqual(dataset.dataset_id, "minimal-3")
        self.assertEqual(dataset.version, "0.2.0")
        self.assertEqual(len(dataset.task_dirs), 3)

    def test_required_capabilities_are_loaded(self) -> None:
        m1 = load_task_manifest(ROOT / "datasets" / "minimal-3" / "m1-reservation-repair")
        m3 = load_task_manifest(ROOT / "datasets" / "minimal-3" / "m3-durable-lease-queue")
        self.assertEqual(m1.required_capabilities, ("persistence_hygiene",))
        self.assertEqual(m3.required_capabilities, ("restart_and_persistence",))

    def test_missing_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ManifestError):
                load_dataset_manifest(directory)


if __name__ == "__main__":
    unittest.main()
