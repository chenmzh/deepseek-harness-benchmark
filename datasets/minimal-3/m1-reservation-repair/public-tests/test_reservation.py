from pathlib import Path
import tempfile
import unittest

from reservation import InventoryService, ReservationNotFound


class ReservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "inventory.json"
        self.service = InventoryService(self.database, {"widget": 5})

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_successful_reserve_request_is_idempotent(self) -> None:
        first = self.service.reserve("widget", 2, "reserve-1")
        second = self.service.reserve("widget", 2, "reserve-1")
        self.assertEqual(first, second)
        self.assertEqual(self.service.available("widget"), 3)

    def test_cancel_restores_stock_once(self) -> None:
        result = self.service.reserve("widget", 2, "reserve-1")
        reservation_id = result["reservation"]["id"]
        self.service.cancel(reservation_id, "cancel-1")
        self.service.cancel(reservation_id, "cancel-2")
        self.assertEqual(self.service.available("widget"), 5)

    def test_state_survives_restart(self) -> None:
        self.service.reserve("widget", 2, "reserve-1")
        restarted = InventoryService(self.database)
        self.assertEqual(restarted.available("widget"), 3)

    def test_unknown_reservation_raises(self) -> None:
        with self.assertRaises(ReservationNotFound):
            self.service.cancel("missing", "cancel-1")


if __name__ == "__main__":
    unittest.main()
