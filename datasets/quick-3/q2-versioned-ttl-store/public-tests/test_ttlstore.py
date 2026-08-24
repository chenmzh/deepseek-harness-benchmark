import tempfile
from pathlib import Path
import unittest

from ttlstore import VersionedTTLStore


class TTLStoreTests(unittest.TestCase):
    def test_put_get_and_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            store = VersionedTTLStore(Path(directory) / "store.json", ttl=5)
            row = store.put("a", {"x": 1}, "r1", 10)
            self.assertEqual(row["version"], 1)
            self.assertEqual(store.get("a", 14)["value"], {"x": 1})
            self.assertIsNone(store.get("a", 15))

    def test_compare_and_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            store = VersionedTTLStore(Path(directory) / "store.json")
            first = store.put("a", 1, "r1", 0)
            second = store.compare_and_swap("a", first["version"], 2, "r2", 1)
            self.assertEqual((second["version"], second["value"]), (2, 2))


if __name__ == "__main__":
    unittest.main()
