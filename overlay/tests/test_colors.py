"""Tests for parse_hex_color, used by the config-driven text_color setting."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from values import parse_hex_color


class TestParseHexColor(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_hex_color("#00ff00"), "#00ff00")

    def test_strips_whitespace(self):
        self.assertEqual(parse_hex_color(" #ff0080 "), "#ff0080")

    def test_missing_hash_raises(self):
        with self.assertRaises(ValueError):
            parse_hex_color("00ff00")

    def test_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            parse_hex_color("#0f0")

    def test_non_hex_digit_raises(self):
        with self.assertRaises(ValueError):
            parse_hex_color("#gg0000")


if __name__ == "__main__":
    unittest.main()
