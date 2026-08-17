import unittest

from harnessbench.result import ResultError, assemble_run_result


class ResultTests(unittest.TestCase):
    def metadata(self) -> dict:
        return {
            "benchmark_version": "0.1.0",
            "dataset": "minimal-3",
            "harness_id": "h1",
            "session_id": "s1",
            "status": "completed",
            "wall_time_seconds": 10,
            "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 2, "reasoning_tokens": 3, "credits": None},
            "tooling": {"tool_calls": 4, "failed_tool_calls": 0, "test_cycles": 1, "human_interventions": 0},
        }

    def test_evaluator_fields_cannot_be_overridden(self) -> None:
        metadata = self.metadata()
        metadata["completion_score"] = 999
        result = assemble_run_result({"task_id": "M1", "completion_score": 80, "ship_ready": False}, metadata)
        self.assertEqual(result["completion_score"], 80)

    def test_missing_usage_is_rejected(self) -> None:
        metadata = self.metadata()
        del metadata["usage"]["reasoning_tokens"]
        with self.assertRaises(ResultError):
            assemble_run_result({"task_id": "M1", "completion_score": 80}, metadata)


if __name__ == "__main__":
    unittest.main()
