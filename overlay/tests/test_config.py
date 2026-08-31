"""Tests for load_config (overlay.py): [general] parsing. overlay.ini is
assumed present/complete - a missing file, section, or key raises rather
than falling back to defaults."""

import configparser
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from overlay import load_config

FULL_INI = (
    "[general]\n"
    "refresh_ms = 16\n"
    "text_color = #ff00ff\n"
    "window_width = 640\n"
    "font_size = 20\n"
    "column_padding = 10\n"
    "label_column_fraction = 0.5\n"
    "line_padding = 4\n"
    "alpha = 0.9\n"
)


def write_ini(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestMissingOrBrokenFile(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(configparser.NoSectionError):
            load_config("does_not_exist.ini")

    def test_unparseable_file_raises(self):
        path = write_ini("[general\nthis is not valid ini")
        try:
            with self.assertRaises(configparser.Error):
                load_config(path)
        finally:
            os.unlink(path)

    def test_missing_general_section_raises(self):
        path = write_ini("[unrelated]\nfoo = bar\n")
        try:
            with self.assertRaises(configparser.NoSectionError):
                load_config(path)
        finally:
            os.unlink(path)

    def test_missing_key_raises(self):
        path = write_ini("[general]\nrefresh_ms = 16\n")
        try:
            with self.assertRaises(configparser.NoOptionError):
                load_config(path)
        finally:
            os.unlink(path)


class TestGeneralSection(unittest.TestCase):
    def test_parses_all_keys(self):
        path = write_ini(FULL_INI)
        try:
            general = load_config(path)
            self.assertEqual(general, {
                "refresh_ms": 16,
                "text_color": "#ff00ff",
                "window_width": 640,
                "font_size": 20,
                "column_padding": 10,
                "label_column_fraction": 0.5,
                "line_padding": 4,
                "alpha": 0.9,
            })
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
