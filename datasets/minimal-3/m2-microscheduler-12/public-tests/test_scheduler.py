import unittest

from microscheduler import solve


INSTANCE = {
    "workers": [
        {"id": "w1", "skills": ["cut", "pack"]},
        {"id": "w2", "skills": ["pack"]},
    ],
    "jobs": [
        {"id": "j1", "duration": 3, "release_time": 0, "deadline": 4, "priority": 3, "skill": "cut", "family": "a", "predecessors": []},
        {"id": "j2", "duration": 2, "release_time": 0, "deadline": 6, "priority": 2, "skill": "pack", "family": "b", "predecessors": ["j1"]},
        {"id": "j3", "duration": 4, "release_time": 1, "deadline": 7, "priority": 1, "skill": "pack", "family": "b", "predecessors": []},
    ],
    "setup_time": 1,
}


def assert_valid(test: unittest.TestCase, instance: dict, schedule: list[dict]) -> None:
    jobs = {job["id"]: job for job in instance["jobs"]}
    workers = {worker["id"]: worker for worker in instance["workers"]}
    rows = {row["job_id"]: row for row in schedule}
    test.assertEqual(set(rows), set(jobs))
    for job_id, row in rows.items():
        job = jobs[job_id]
        test.assertIn(job["skill"], workers[row["worker_id"]]["skills"])
        test.assertEqual(row["end"] - row["start"], job["duration"])
        test.assertGreaterEqual(row["start"], job["release_time"])
        for predecessor in job["predecessors"]:
            test.assertLessEqual(rows[predecessor]["end"], row["start"])
    for worker_id in workers:
        assigned = sorted((row for row in schedule if row["worker_id"] == worker_id), key=lambda row: row["start"])
        for previous, current in zip(assigned, assigned[1:]):
            delay = instance["setup_time"] if jobs[previous["job_id"]]["family"] != jobs[current["job_id"]]["family"] else 0
            test.assertGreaterEqual(current["start"], previous["end"] + delay)


class SchedulerTests(unittest.TestCase):
    def test_returns_valid_schedule(self) -> None:
        assert_valid(self, INSTANCE, solve(INSTANCE))

    def test_is_deterministic(self) -> None:
        self.assertEqual(solve(INSTANCE), solve(INSTANCE))


if __name__ == "__main__":
    unittest.main()
