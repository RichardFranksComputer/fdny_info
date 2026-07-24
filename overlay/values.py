"""overlay.ini parsing plus WatchEngine, which turns watch definitions into
live display text each tick (raw reads and calculated values alike)."""

import configparser
import math
import os
import re
import sys

from process_reader import get_module_base, read_value, resolve_pointer_chain

# =====================================================
# CONFIG
# =====================================================
# All settings, including WATCHES, live in overlay.ini (see load_config()).

_DEFAULT_GENERAL = {
    "process_name": "FDNYFirefighter.exe",
    "refresh_ms": 33,
    "text_color": "#00ff00",  # the original hardcoded "lime"
    "window_width": 300,
    "font_size": 12,
    "column_padding": 5,
    "label_column_fraction": 0.73,  # rest goes to the value column
    "line_padding": 6,  # extra breathing room per row beyond the raw font metrics
    "alpha": 0.55,  # whole-window blend, used by both the Tk and Win32 layers
}

def get_base_dir():
    """Directory containing the running .exe (frozen) or this script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(get_base_dir(), "overlay.ini")

def parse_int(value):
    """Parse a decimal or 0x-prefixed hex string, e.g. '40' or '0x00103A78'."""
    return int(value.strip(), 0)

def parse_hex_color(value):
    """Validate a Tk '#rrggbb' hex color string."""
    value = value.strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"expected '#rrggbb', got {value!r}")
    return value

def load_config(path=CONFIG_PATH):
    """Load general settings + WATCHES from overlay.ini at `path`. Falls back to
    defaults and skips bad [watch:...] sections rather than crashing.
    Returns (general_dict, watches_list, warnings_list)."""
    warnings = []
    general = dict(_DEFAULT_GENERAL)
    watches = []

    parser = configparser.ConfigParser()
    try:
        read_ok = parser.read(path)
    except configparser.Error as e:
        warnings.append(f"could not parse {os.path.basename(path)}: {e}")
        return general, watches, warnings

    if not read_ok:
        warnings.append(f"{os.path.basename(path)} not found - using built-in defaults")
        return general, watches, warnings

    if parser.has_section("general"):
        g = parser["general"]
        general["process_name"] = g.get("process_name", general["process_name"])
        general["refresh_ms"] = g.getint("refresh_ms", fallback=general["refresh_ms"])
        general["text_color"] = g.get("text_color", general["text_color"])
        general["window_width"] = g.getint("window_width", fallback=general["window_width"])
        general["font_size"] = g.getint("font_size", fallback=general["font_size"])
        general["column_padding"] = g.getint("column_padding", fallback=general["column_padding"])
        general["label_column_fraction"] = g.getfloat("label_column_fraction", fallback=general["label_column_fraction"])
        general["line_padding"] = g.getint("line_padding", fallback=general["line_padding"])
        general["alpha"] = g.getfloat("alpha", fallback=general["alpha"])

    for section in parser.sections():
        if not section.startswith("watch:"):
            continue
        label = section[len("watch:"):]
        s = parser[section]
        try:
            calculated = s.get("calculated", "").strip()
            if calculated:
                watches.append({"label": label, "module": None, "base": None, "offsets": [], "calculated": calculated})
                continue

            module = s.get("module")
            base = parse_int(s.get("base"))
            offsets_raw = s.get("offsets", "").strip()
            offsets = [parse_int(o) for o in offsets_raw.split(",") if o.strip()] if offsets_raw else []
            value_type = s.get("type", "float")
            feeds = s.get("feeds", "").strip() or None

            watches.append({
                "label": label,
                "module": module,
                "base": base,
                "offsets": offsets,
                "type": value_type,
                "feeds": feeds,
            })
        except Exception as e:
            warnings.append(f"skipped watch '{label}': {e}")

    return general, watches, warnings

CONFIG_GENERAL, WATCHES, CONFIG_WARNINGS = load_config()

PROCESS_NAME = CONFIG_GENERAL["process_name"]
REFRESH_MS = CONFIG_GENERAL["refresh_ms"]
FONT_SIZE = CONFIG_GENERAL["font_size"]
WINDOW_WIDTH = CONFIG_GENERAL["window_width"]
COLUMN_PADDING = CONFIG_GENERAL["column_padding"]
LABEL_COLUMN_FRACTION = CONFIG_GENERAL["label_column_fraction"]
LINE_PADDING = CONFIG_GENERAL["line_padding"]
ALPHA = CONFIG_GENERAL["alpha"]

try:
    TEXT_COLOR = parse_hex_color(CONFIG_GENERAL["text_color"])
except ValueError as e:
    CONFIG_WARNINGS.append(f"invalid text_color {CONFIG_GENERAL['text_color']!r}: {e}; using default")
    TEXT_COLOR = _DEFAULT_GENERAL["text_color"]

# =====================================================
# WATCH ENGINE
# =====================================================

PLAYER_STATE_ON_LADDER = 5

class WatchEngine:
    """Turns a process handle into display text for every configured watch.
    No Tkinter - overlay.py owns rendering, this owns values."""

    def __init__(self, watches=WATCHES):
        self.watches = watches
        self.reset_for_new_attach()

        # calculated kind -> zero-arg getter
        self._calculated_text = {
            "speed": self._speed_text,
            "previous_jump": lambda: f"{self.previous_jump:.3f}",
            "previous_jump_max": lambda: f"{self.previous_jump_max:.3f}",
            "current_jump_max": lambda: f"{self.current_jump_max:.3f}",
        }

    def reset_for_new_attach(self):
        """Cached addresses/derived state from the previous process
        instance are no longer valid."""
        self.module_cache = {}
        self.feeds = {}  # feeds role -> last raw value read for it

        self.current_height_in_jump = 0.0
        self.previous_jump = 0.0
        self.previous_jump_max = 0.0  # 2nd-best jump of all time
        self.current_jump_max = 0.0  # best jump of all time
        self.jump_baseline = None  # standing height at start of jump
        self._pending_ladder_rebaseline = False  # see calculate_jump_height

    def get_cached_module_base(self, proc, module_name):
        """Get module base with caching to reduce overhead."""
        if module_name not in self.module_cache:
            base = get_module_base(proc, module_name)
            if base:
                self.module_cache[module_name] = base
            return base
        return self.module_cache[module_name]

    def _speed_text(self):
        vx, vy = self.feeds.get("velocity_x"), self.feeds.get("velocity_y")
        if vx is None or vy is None:
            return "<wait>"
        return f"{math.sqrt(vx**2 + vy**2):.3f}"  # shout out to nyddesson for the original idea on this

    def update(self, proc):
        """Return [(label, display_text), ...] in watch order."""
        results = [(w["label"], self._resolve(proc, w)) for w in self.watches]
        self.calculate_jump_height()
        return results

    def _resolve(self, proc, w):
        """Display text for one watch: a calculated value or a raw read."""
        try:
            kind = w.get("calculated")
            if kind:
                getter = self._calculated_text.get(kind)
                return getter() if getter else "<calc?>"

            mod = self.get_cached_module_base(proc, w["module"])
            if not mod:
                return "<module?>"

            addr = (mod + w["base"]) & 0xFFFFFFFF
            if w.get("offsets"):
                addr = resolve_pointer_chain(proc, addr, w["offsets"])
                if not addr:
                    return "<ptr?>"

            value_type = w.get("type", "float")
            val = read_value(proc, addr, value_type)
            if val is None:
                return "<read?>"

            role = w.get("feeds")
            if role:
                self.feeds[role] = val
            return f"{val:.3f}" if value_type in ("float", "double") else f"{val}"

        except Exception as e:
            print(f"Error reading {w['label']}: {e}")
            return "<err>"

    def calculate_jump_height(self):
        """Tracks Previous/Current Jump Max from Z Collision Center vs Z
        Ground Height. Skipped while on a ladder (climbing reads like a
        jump); _pending_ladder_rebaseline forces a fresh baseline on the
        next reading after leaving one, instead of using the stale one."""
        if self.feeds.get("player_state") == PLAYER_STATE_ON_LADDER:
            self._pending_ladder_rebaseline = True
            return

        z_collision_center = self.feeds.get("z_collision_center")
        z_ground_height = self.feeds.get("z_ground_height")
        if z_collision_center is None or z_ground_height is None:
            return

        current_height = z_collision_center - z_ground_height
        if current_height < 50:  # crouched - not a usable baseline
            return

        if self.jump_baseline is None or self._pending_ladder_rebaseline:
            self._pending_ladder_rebaseline = False
            self.jump_baseline = current_height
            self.current_height_in_jump = 0.0
            return

        relative_height = current_height - self.jump_baseline

        if abs(relative_height) < 5:  # landed
            if self.current_height_in_jump > 0:
                completed = self.current_height_in_jump
                self.previous_jump = completed
                if completed > self.current_jump_max:
                    self.previous_jump_max = self.current_jump_max
                    self.current_jump_max = completed
                elif completed > self.previous_jump_max:
                    self.previous_jump_max = completed
                self.current_height_in_jump = 0.0
            self.jump_baseline = current_height
            return

        self.current_height_in_jump = max(self.current_height_in_jump, relative_height)
