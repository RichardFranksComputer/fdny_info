"""Loading the game's values-*.py file and WatchEngine, which turns its
WATCHES list into live display text each tick (raw reads and calculated
values alike). No knowledge of overlay.ini/aesthetics - that's overlay.py's
own concern, since nothing here reads any of those settings."""

import glob
import importlib.util
import os
import sys

from process_reader import get_module_base, read_value, resolve_pointer_chain

# =====================================================
# GAME MODULE LOADING
# =====================================================

def get_base_dir():
    """Directory containing the running .exe (frozen) or this script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def find_values_files(base_dir):
    """All values-*.py files next to overlay.ini, e.g. values-fdny.py."""
    return sorted(glob.glob(os.path.join(base_dir, "values-*.py")))

def load_values_module(base_dir=None):
    """Load the one values-*.py file next to the exe/script: WATCHES (what
    to show) plus optional PROCESS_NAME/make_state()/compute() (calculated
    values). Missing file or a broken module degrades to no watches at all
    rather than crashing. Returns (module_or_None, warnings_list)."""
    base_dir = base_dir or get_base_dir()
    warnings = []
    paths = find_values_files(base_dir)

    if not paths:
        warnings.append("no values-*.py file found - no watches configured")
        return None, warnings
    if len(paths) > 1:
        names = ", ".join(os.path.basename(p) for p in paths)
        warnings.append(f"multiple values-*.py files found ({names}) - using {os.path.basename(paths[0])}")

    path = paths[0]
    try:
        spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, warnings
    except Exception as e:
        warnings.append(f"could not load {os.path.basename(path)}: {e}")
        return None, warnings

VALUES_MODULE, MODULE_WARNINGS = load_values_module()

PROCESS_NAME = getattr(VALUES_MODULE, "PROCESS_NAME", "") if VALUES_MODULE else ""
WATCHES = getattr(VALUES_MODULE, "WATCHES", []) if VALUES_MODULE else []

# =====================================================
# WATCH ENGINE
# =====================================================

class WatchEngine:
    """Turns a process handle into display text for every configured watch.
    Calculated values are delegated entirely to `game` (make_state()/
    compute()) - this class knows only that contract, not any game logic."""

    def __init__(self, watches=WATCHES, game=VALUES_MODULE):
        self.watches = watches
        self.game = game
        self.reset_for_new_attach()

    def reset_for_new_attach(self):
        """Cached addresses/derived state from the previous process
        instance are no longer valid."""
        self.module_cache = {}
        self.feeds = {}  # feeds role -> last raw value read for it
        self.state = self.game.make_state() if self.game and hasattr(self.game, "make_state") else {}
        self._computed = {}  # calculated kind -> value, refreshed each update()

    def get_cached_module_base(self, proc, module_name):
        """Get module base with caching to reduce overhead."""
        if module_name not in self.module_cache:
            base = get_module_base(proc, module_name)
            if base:
                self.module_cache[module_name] = base
            return base
        return self.module_cache[module_name]

    def update(self, proc):
        """Return [(label, display_text), ...] in watch order. Raw watches
        are resolved first (populating self.feeds), then the game module's
        compute() runs once so calculated watches reflect this tick's
        feeds, not a stale previous one."""
        texts = [None] * len(self.watches)
        for i, w in enumerate(self.watches):
            if not w.get("calculated"):
                texts[i] = self._resolve_raw(proc, w)

        self._computed = self._compute()

        for i, w in enumerate(self.watches):
            kind = w.get("calculated")
            if kind:
                texts[i] = self._resolve_calculated(kind)

        return list(zip((w["label"] for w in self.watches), texts))

    def _compute(self):
        compute = getattr(self.game, "compute", None) if self.game else None
        if not compute:
            return {}
        try:
            return compute(self.feeds, self.state)
        except Exception as e:
            print(f"Error computing values: {e}")
            return {}

    def _resolve_calculated(self, kind):
        if kind not in self._computed:
            return "<calc?>"
        val = self._computed[kind]
        return f"{val:.3f}" if val is not None else "<wait>"

    def _resolve_raw(self, proc, w):
        """Display text for one raw memory-read watch."""
        try:
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
