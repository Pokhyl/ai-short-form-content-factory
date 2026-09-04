from __future__ import annotations

import unittest

from prototype.v4.selftest_media_contract import parse_media_selections


class SelfTestMediaContractTests(unittest.TestCase):
    def test_accepts_documented_wrapper(self):
        self.assertEqual(
            parse_media_selections({"selections": {"S1A": "A", "S1B": None}}, ["S1A", "S1B"]),
            {"S1A": "A", "S1B": None},
        )

    def test_accepts_direct_mapping_from_model(self):
        self.assertEqual(
            parse_media_selections({"S1A": "A", "S1B": "B"}, ["S1A", "S1B"]),
            {"S1A": "A", "S1B": "B"},
        )

    def test_rejects_missing_key(self):
        with self.assertRaisesRegex(ValueError, "keys mismatch"):
            parse_media_selections({"S1A": "A"}, ["S1A", "S1B"])

    def test_rejects_extra_key(self):
        with self.assertRaisesRegex(ValueError, "keys mismatch"):
            parse_media_selections({"S1A": "A", "S1B": "B", "X": "C"}, ["S1A", "S1B"])

    def test_rejects_non_string_value(self):
        with self.assertRaisesRegex(ValueError, "invalid media selection"):
            parse_media_selections({"S1A": 123}, ["S1A"])


if __name__ == "__main__":
    unittest.main()
