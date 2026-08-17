from pathlib import Path
import tempfile
import unittest

from harnessbench.manifest import ManifestError, load_dataset_manifest


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_minimal_dataset_is_valid(self) -> None:
        dataset = load_dataset_manifest(ROOT / "datasets" / "minimal-3")
        self.assertEqual(dataset.dataset_id, "minimal-3")
        self.assertEqual(len(dataset.task_dirs), 3)

    def test_missing_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ManifestError):
                load_dataset_manifest(directory)


if __name__ == "__main__":
    unittest.main()
