"""
Tests for overlay.ini loading (load_config, in overlay.py): [general]
aesthetic-settings parsing, and the fallback behavior when the file is
missing or malformed so a bad hand-edit degrades gracefully instead of
crashing the overlay.

Watch/process definitions no longer live in overlay.ini - see
test_values_fdny.py for the values-*.py module contract, and
test_watch_engine.py for the engine that loads it.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from overlay import load_config, _DEFAULT_GENERAL


def write_ini(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestMissingOrBrokenFile(unittest.TestCase):
    def test_missing_file_falls_back_to_defaults_with_warning(self):
        general, warnings = load_config("does_not_exist.ini")
        self.assertEqual(general, _DEFAULT_GENERAL)
        self.assertEqual(len(warnings), 1)
        self.assertIn("not found", warnings[0])

    def test_unparseable_file_falls_back_to_defaults_with_warning(self):
        path = write_ini("[general\nthis is not valid ini")
        try:
            general, warnings = load_config(path)
            self.assertEqual(general, _DEFAULT_GENERAL)
            self.assertEqual(len(warnings), 1)
        finally:
            os.unlink(path)


class TestGeneralSection(unittest.TestCase):
    def test_overrides_only_provided_keys(self):
        path = write_ini("[general]\nrefresh_ms = 16\nfont_size = 20\n")
        try:
            general, warnings = load_config(path)
            self.assertEqual(general["refresh_ms"], 16)
            self.assertEqual(general["font_size"], 20)
            # untouched keys keep their defaults
            self.assertEqual(general["text_color"], _DEFAULT_GENERAL["text_color"])
            self.assertEqual(general["alpha"], _DEFAULT_GENERAL["alpha"])
            self.assertEqual(warnings, [])
        finally:
            os.unlink(path)

    def test_missing_general_section_uses_defaults(self):
        path = write_ini("[unrelated]\nfoo = bar\n")
        try:
            general, _ = load_config(path)
            self.assertEqual(general, _DEFAULT_GENERAL)
        finally:
            os.unlink(path)

    def test_window_layout_keys(self):
        path = write_ini(
            "[general]\n"
            "window_width = 640\n"
            "column_padding = 10\n"
            "label_column_fraction = 0.5\n"
            "line_padding = 4\n"
            "alpha = 0.9\n"
        )
        try:
            general, warnings = load_config(path)
            self.assertEqual(general["window_width"], 640)
            self.assertEqual(general["column_padding"], 10)
            self.assertEqual(general["label_column_fraction"], 0.5)
            self.assertEqual(general["line_padding"], 4)
            self.assertEqual(general["alpha"], 0.9)
            self.assertEqual(warnings, [])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
