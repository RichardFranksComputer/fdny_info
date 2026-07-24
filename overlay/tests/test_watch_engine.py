"""
Tests for WatchEngine.calculate_jump_height: baseline tracking, completed-jump
recording, and the Player State 5 (on ladder) guard that freezes tracking so
climbing a ladder isn't misread as a jump, then rebaselines at the
post-ladder height instead of resuming the stale pre-ladder one.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from values import WatchEngine, PLAYER_STATE_ON_LADDER


class TestJumpHeightCalculation(unittest.TestCase):
    def setUp(self):
        self.engine = WatchEngine(watches=[])

    def _feed(self, z_collision_center, z_ground_height, player_state=None):
        self.engine.feeds["z_collision_center"] = z_collision_center
        self.engine.feeds["z_ground_height"] = z_ground_height
        if player_state is not None:
            self.engine.feeds["player_state"] = player_state
        self.engine.calculate_jump_height()

    def test_no_op_until_both_feeds_are_present(self):
        self.engine.feeds["z_collision_center"] = 100.0
        self.engine.calculate_jump_height()
        self.assertIsNone(self.engine.jump_baseline)

    def test_first_reading_establishes_baseline_without_recording_a_jump(self):
        self._feed(100.0, 0.0)
        self.assertEqual(self.engine.jump_baseline, 100.0)
        self.assertEqual(self.engine.current_height_in_jump, 0.0)

    def test_crouched_height_is_not_a_usable_baseline(self):
        self._feed(30.0, 0.0)  # < 50 - crouched
        self.assertIsNone(self.engine.jump_baseline)

    def test_rising_then_landing_records_a_completed_jump(self):
        self._feed(100.0, 0.0)  # baseline
        self._feed(120.0, 0.0)  # rising
        self._feed(100.0, 0.0)  # landed
        self.assertEqual(self.engine.previous_jump, 20.0)
        self.assertEqual(self.engine.current_jump_max, 20.0)

    def test_second_best_jump_tracked_as_previous_jump_max(self):
        self._feed(100.0, 0.0)
        self._feed(130.0, 0.0)
        self._feed(100.0, 0.0)  # completed jump of 30 -> current_jump_max
        self._feed(115.0, 0.0)
        self._feed(100.0, 0.0)  # completed jump of 15 -> previous_jump_max
        self.assertEqual(self.engine.current_jump_max, 30.0)
        self.assertEqual(self.engine.previous_jump_max, 15.0)

    def test_on_ladder_freezes_tracking_despite_large_z_swing(self):
        self._feed(100.0, 0.0)  # baseline
        self._feed(120.0, 0.0)  # rising mid-jump
        self.assertEqual(self.engine.current_height_in_jump, 20.0)

        # A ladder climb can swing Z Collision Center a lot - must be ignored
        # (not tracked as jump progress) while player_state stays 5.
        self._feed(500.0, 0.0, player_state=PLAYER_STATE_ON_LADDER)
        self.assertEqual(self.engine.current_height_in_jump, 20.0)
        self.assertEqual(self.engine.jump_baseline, 100.0)
        self.assertEqual(self.engine.previous_jump, 0.0)

    def test_leaving_ladder_rebaselines_at_post_ladder_height(self):
        self._feed(100.0, 0.0)  # baseline at ground level
        self._feed(120.0, 0.0)  # rising mid-jump (current_height_in_jump = 20)
        self._feed(500.0, 0.0, player_state=PLAYER_STATE_ON_LADDER)  # onto a ladder

        # Stepping off must rebaseline at the post-ladder height (300 here),
        # not resume relative to the stale pre-ladder baseline of 100 - and
        # must not silently record the frozen 20 as a completed jump either.
        self._feed(300.0, 0.0, player_state=0)
        self.assertEqual(self.engine.jump_baseline, 300.0)
        self.assertEqual(self.engine.current_height_in_jump, 0.0)
        self.assertEqual(self.engine.previous_jump, 0.0)

    def test_jump_right_after_leaving_ladder_does_not_include_climb_height(self):
        # Reported bug: climbing a ladder then jumping showed the recorded
        # jump height as (ladder climb height + actual jump height).
        self._feed(100.0, 0.0)  # baseline at ground level
        self._feed(300.0, 0.0, player_state=PLAYER_STATE_ON_LADDER)  # climbing

        # Player State can read something other than 5 (e.g. 3) the instant
        # you jump off the ladder - the guard must not depend on seeing 5
        # for the whole climb, just on having seen it at all before this.
        self._feed(300.0, 0.0, player_state=3)  # steps off at the top
        self._feed(320.0, 0.0, player_state=3)  # jumps - 20 above post-ladder height
        self._feed(300.0, 0.0, player_state=0)  # lands back at the post-ladder height

        self.assertEqual(self.engine.previous_jump, 20.0)


if __name__ == "__main__":
    unittest.main()
