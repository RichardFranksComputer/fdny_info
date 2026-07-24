"""
Tests for WatchEngine's calculated-value plumbing: it delegates entirely to
a game module's make_state()/compute() and only handles dispatch/formatting
("<calc?>" for a kind the module never returns, "<wait>" for a None value,
otherwise 3-decimal formatting) plus raw-watch reads. A fake game module is
used here so these tests stay independent of any one game's own logic - see
test_values_fdny.py for FDNY's actual compute() (speed, jump-height).
"""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from watch_engine import WatchEngine


def fake_game(computed=None, state=None):
    """A minimal game module stand-in: make_state() returns `state` (or {}),
    compute() always returns `computed` (or {}) regardless of feeds."""
    game = types.SimpleNamespace()
    game.make_state = lambda: dict(state or {})
    game.compute = lambda feeds, state: dict(computed or {})
    return game


class TestCalculatedDispatch(unittest.TestCase):
    def test_known_kind_is_formatted_to_three_decimals(self):
        watches = [{"label": "Speed", "calculated": "speed"}]
        engine = WatchEngine(watches=watches, game=fake_game({"speed": 12.3456}))
        self.assertEqual(engine.update(proc=None), [("Speed", "12.346")])

    def test_unknown_kind_shows_calc_placeholder(self):
        watches = [{"label": "Mystery", "calculated": "mystery"}]
        engine = WatchEngine(watches=watches, game=fake_game({}))
        self.assertEqual(engine.update(proc=None), [("Mystery", "<calc?>")])

    def test_none_value_shows_wait_placeholder(self):
        watches = [{"label": "Speed", "calculated": "speed"}]
        engine = WatchEngine(watches=watches, game=fake_game({"speed": None}))
        self.assertEqual(engine.update(proc=None), [("Speed", "<wait>")])

    def test_no_game_module_shows_calc_placeholder(self):
        watches = [{"label": "Speed", "calculated": "speed"}]
        engine = WatchEngine(watches=watches, game=None)
        self.assertEqual(engine.update(proc=None), [("Speed", "<calc?>")])

    def test_compute_receives_feeds_populated_by_raw_watches_this_tick(self):
        seen = {}

        def compute(feeds, state):
            seen.update(feeds)
            return {"speed": 1.0}

        game = types.SimpleNamespace(make_state=lambda: {}, compute=compute)
        watches = [{"label": "Speed", "calculated": "speed"}]
        engine = WatchEngine(watches=watches, game=game)
        engine.feeds["velocity_x"] = 3.0  # simulate a raw watch having fed this
        engine.update(proc=None)
        self.assertEqual(seen.get("velocity_x"), 3.0)

    def test_compute_error_falls_back_to_calc_placeholder(self):
        def compute(feeds, state):
            raise ValueError("boom")

        game = types.SimpleNamespace(make_state=lambda: {}, compute=compute)
        watches = [{"label": "Speed", "calculated": "speed"}]
        engine = WatchEngine(watches=watches, game=game)
        self.assertEqual(engine.update(proc=None), [("Speed", "<calc?>")])

    def test_reset_for_new_attach_rebuilds_state_from_game(self):
        game = fake_game(state={"count": 1})
        engine = WatchEngine(watches=[], game=game)
        engine.state["count"] = 99
        engine.reset_for_new_attach()
        self.assertEqual(engine.state, {"count": 1})


if __name__ == "__main__":
    unittest.main()
