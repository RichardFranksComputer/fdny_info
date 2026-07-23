"""Tests for parse_rgb_to_hex, used by the config-driven text_color setting."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from overlay import parse_rgb_to_hex


class TestParseRgbToHex(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_rgb_to_hex("0,255,0"), "#00ff00")

    def test_strips_whitespace_around_components(self):
        self.assertEqual(parse_rgb_to_hex(" 255, 0 , 128 "), "#ff0080")

    def test_wrong_component_count_raises(self):
        with self.assertRaises(ValueError):
            parse_rgb_to_hex("255,0")

    def test_out_of_range_component_raises(self):
        with self.assertRaises(ValueError):
            parse_rgb_to_hex("256,0,0")

    def test_negative_component_raises(self):
        with self.assertRaises(ValueError):
            parse_rgb_to_hex("-1,0,0")

    def test_non_numeric_component_raises(self):
        with self.assertRaises(ValueError):
            parse_rgb_to_hex("r,g,b")


if __name__ == "__main__":
    unittest.main()
