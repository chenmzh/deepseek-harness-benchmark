import unittest

from configmerge import resolve


class ConfigMergeTests(unittest.TestCase):
    def test_higher_layer_wins(self):
        self.assertEqual(resolve({"port": 80}, {"port": 8080}), {"port": 8080})

    def test_nested_mappings_merge(self):
        result = resolve(
            {"server": {"host": "localhost", "port": 80}},
            {"server": {"port": 8080}},
        )
        self.assertEqual(result, {"server": {"host": "localhost", "port": 8080}})


if __name__ == "__main__":
    unittest.main()
