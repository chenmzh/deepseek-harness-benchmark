from pathlib import Path
import shutil
import tempfile
import unittest

from harnessbench.evaluation import _required_capability_failures, evaluate_submission
from harnessbench.manifest import load_task_manifest


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "minimal-3"
PRIVATE = ROOT / "private" / "hidden-tests"
REFERENCES = ROOT / "private" / "reference-solutions"


class EvaluationTests(unittest.TestCase):
    def score(self, task_dir: str, reference_dir: str) -> dict:
        manifest = load_task_manifest(DATASET / task_dir)
        return evaluate_submission(manifest, REFERENCES / reference_dir, PRIVATE)

    def test_required_capability_must_receive_full_weight(self) -> None:
        capabilities = {"durability": {"earned": 14, "weight": 15}}
        failures = _required_capability_failures(("durability",), capabilities)
        self.assertEqual(failures, ["required capability incomplete: durability (14/15)"])

    def test_missing_required_capability_is_failure(self) -> None:
        failures = _required_capability_failures(("durability",), {})
        self.assertEqual(failures, ["required capability unavailable: durability"])

    def score_non_atomic_mutation(self, task_dir: str, source: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            mutation = Path(directory) / "submission"
            shutil.copytree(REFERENCES / task_dir, mutation)
            implementation = mutation / source
            text = implementation.read_text(encoding="utf-8")
            marker = "        descriptor, temporary = tempfile.mkstemp("
            replacement = (
                "        self.database.write_text("
                "json.dumps(self._state, sort_keys=True), encoding=\"utf-8\")\n"
                "        return\n"
                + marker
            )
            self.assertIn(marker, text)
            implementation.write_text(text.replace(marker, replacement, 1), encoding="utf-8")
            manifest = load_task_manifest(DATASET / task_dir)
            return evaluate_submission(manifest, mutation, PRIVATE)

    def test_m1_non_atomic_high_score_mutation_fails_required_capability(self) -> None:
        result = self.score_non_atomic_mutation(
            "m1-reservation-repair", "reservation/service.py"
        )
        self.assertEqual(result["completion_score"], 90.0, result)
        self.assertFalse(result["ship_ready"], result)
        self.assertIn(
            "required capability incomplete: persistence_hygiene (0/10)",
            result["critical_failures"],
        )

    def test_m3_non_atomic_threshold_mutation_fails_required_capability(self) -> None:
        result = self.score_non_atomic_mutation(
            "m3-durable-lease-queue", "leasequeue/queue.py"
        )
        self.assertEqual(result["completion_score"], 85.0, result)
        self.assertFalse(result["ship_ready"], result)
        self.assertIn(
            "required capability incomplete: restart_and_persistence (0/15)",
            result["critical_failures"],
        )

    def test_m1_reference_is_ship_ready(self) -> None:
        result = self.score("m1-reservation-repair", "m1-reservation-repair")
        self.assertTrue(result["ship_ready"], result)

    def test_m2_reference_is_ship_ready(self) -> None:
        result = self.score("m2-microscheduler-12", "m2-microscheduler-12")
        self.assertFalse(result["critical_failures"], result)
        self.assertTrue(result["ship_ready"], result)
        self.assertEqual(result["optimizer_quality"], 1.0, result)

    def test_m3_reference_is_ship_ready(self) -> None:
        result = self.score("m3-durable-lease-queue", "m3-durable-lease-queue")
        self.assertTrue(result["ship_ready"], result)


if __name__ == "__main__":
    unittest.main()
