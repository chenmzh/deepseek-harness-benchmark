from pathlib import Path
import tempfile
import unittest

from leasequeue import DurableQueue, LeaseConflict


class QueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "queue.json"
        self.queue = DurableQueue(self.database, max_attempts=3, base_backoff=5)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_enqueue_claim_ack(self) -> None:
        created = self.queue.enqueue({"value": 1}, "key-1")
        claimed = self.queue.claim("worker-a", 10, now=100)
        self.assertEqual(created["id"], claimed["id"])
        acknowledged = self.queue.ack(created["id"], "worker-a")
        self.assertEqual(acknowledged["state"], "succeeded")

    def test_enqueue_is_idempotent(self) -> None:
        first = self.queue.enqueue({"value": 1}, "key-1")
        second = self.queue.enqueue({"value": 999}, "key-1")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.queue.jobs()), 1)

    def test_active_lease_is_exclusive(self) -> None:
        self.queue.enqueue({}, "key-1")
        self.queue.claim("worker-a", 10, now=100)
        self.assertIsNone(self.queue.claim("worker-b", 10, now=105))

    def test_wrong_owner_cannot_ack(self) -> None:
        job = self.queue.enqueue({}, "key-1")
        self.queue.claim("worker-a", 10, now=100)
        with self.assertRaises(LeaseConflict):
            self.queue.ack(job["id"], "worker-b")


if __name__ == "__main__":
    unittest.main()
