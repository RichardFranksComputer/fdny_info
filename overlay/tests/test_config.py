"""
Tests for overlay.ini loading (load_config / parse_int): general settings
parsing, watch-section parsing (normal and calculated), hex/decimal offsets,
and the fallback behavior when the file is missing or a section is malformed
so a bad hand-edit degrades gracefully instead of crashing the overlay.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from overlay import load_config, parse_int, _DEFAULT_GENERAL


def write_ini(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestParseInt(unittest.TestCase):
    def test_hex(self):
        self.assertEqual(parse_int("0x00103A78"), 0x00103A78)

    def test_decimal(self):
        self.assertEqual(parse_int("40"), 40)

    def test_strips_whitespace(self):
        self.assertEqual(parse_int("  0x10  "), 16)


class TestMissingOrBrokenFile(unittest.TestCase):
    def test_missing_file_falls_back_to_defaults_with_warning(self):
        general, watches, warnings = load_config("does_not_exist.ini")
        self.assertEqual(general, _DEFAULT_GENERAL)
        self.assertEqual(watches, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("not found", warnings[0])

    def test_unparseable_file_falls_back_to_defaults_with_warning(self):
        path = write_ini("[general\nthis is not valid ini")
        try:
            general, watches, warnings = load_config(path)
            self.assertEqual(general, _DEFAULT_GENERAL)
            self.assertEqual(watches, [])
            self.assertEqual(len(warnings), 1)
        finally:
            os.unlink(path)


class TestGeneralSection(unittest.TestCase):
    def test_overrides_only_provided_keys(self):
        path = write_ini("[general]\nprocess_name = Foo.exe\nrefresh_ms = 16\n")
        try:
            general, _, warnings = load_config(path)
            self.assertEqual(general["process_name"], "Foo.exe")
            self.assertEqual(general["refresh_ms"], 16)
            # untouched keys keep their defaults
            self.assertEqual(general["anchor_corner"], _DEFAULT_GENERAL["anchor_corner"])
            self.assertEqual(warnings, [])
        finally:
            os.unlink(path)

    def test_missing_general_section_uses_defaults(self):
        path = write_ini("[watch:Speed]\ncalculated = true\n")
        try:
            general, _, _ = load_config(path)
            self.assertEqual(general, _DEFAULT_GENERAL)
        finally:
            os.unlink(path)


class TestWatchSections(unittest.TestCase):
    def test_normal_watch_with_offsets(self):
        path = write_ini(
            "[watch:Vel X]\n"
            "module = FDNYFirefighter.exe\n"
            "base = 0x00103A78\n"
            "offsets = 0x30,0x104\n"
            "type = float\n"
        )
        try:
            _, watches, warnings = load_config(path)
            self.assertEqual(warnings, [])
            self.assertEqual(watches, [{
                "label": "Vel X",
                "module": "FDNYFirefighter.exe",
                "base": 0x00103A78,
                "offsets": [0x30, 0x104],
                "type": "float",
            }])
        finally:
            os.unlink(path)

    def test_watch_with_blank_offsets(self):
        path = write_ini(
            "[watch:Z Collision Center]\n"
            "module = genesis.dll\n"
            "base = 0x362EE8\n"
            "offsets =\n"
            "type = float\n"
        )
        try:
            _, watches, warnings = load_config(path)
            self.assertEqual(warnings, [])
            self.assertEqual(watches[0]["offsets"], [])
        finally:
            os.unlink(path)

    def test_calculated_watch_needs_no_other_keys(self):
        path = write_ini("[watch:Speed]\ncalculated = true\n")
        try:
            _, watches, warnings = load_config(path)
            self.assertEqual(warnings, [])
            self.assertEqual(watches, [{
                "label": "Speed", "module": None, "base": None,
                "offsets": [], "calculated": True,
            }])
        finally:
            os.unlink(path)

    def test_watch_order_matches_file_order(self):
        path = write_ini(
            "[watch:B]\ncalculated = true\n"
            "[watch:A]\ncalculated = true\n"
        )
        try:
            _, watches, _ = load_config(path)
            self.assertEqual([w["label"] for w in watches], ["B", "A"])
        finally:
            os.unlink(path)

    def test_malformed_watch_is_skipped_with_warning_but_others_still_load(self):
        path = write_ini(
            "[watch:Good]\n"
            "module = TestGame.exe\n"
            "base = 0x10\n"
            "offsets = 0x4\n"
            "type = float\n"
            "\n"
            "[watch:Bad]\n"
            "module = TestGame.exe\n"
            "base = not_a_number\n"
            "type = float\n"
        )
        try:
            _, watches, warnings = load_config(path)
            self.assertEqual(len(watches), 1)
            self.assertEqual(watches[0]["label"], "Good")
            self.assertEqual(len(warnings), 1)
            self.assertIn("Bad", warnings[0])
        finally:
            os.unlink(path)

    def test_sections_not_prefixed_with_watch_are_ignored(self):
        path = write_ini("[unrelated]\nfoo = bar\n")
        try:
            _, watches, warnings = load_config(path)
            self.assertEqual(watches, [])
            self.assertEqual(warnings, [])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
