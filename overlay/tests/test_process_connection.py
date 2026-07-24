"""
Tests for ProcessConnection, the state machine in process_reader.py that handles:
  - process not found (yet)
  - process found but OpenProcess fails, retried up to max_open_attempts
  - successful attach
  - the attached process dying, and automatically re-searching afterward
  - re-attaching after the process is relaunched

These exercise ProcessConnection directly with injected fakes for the OS
calls and the clock, so they run without Windows, a live game process, or a
GUI.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process_reader import ProcessConnection


class FakeClock:
    """Manually-advanced stand-in for time.monotonic."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, dt):
        self.now += dt


def make_connection(**overrides):
    kwargs = dict(
        process_name="FDNYFirefighter.exe",
        search_interval=1.0,
        max_open_attempts=5,
        get_pid_fn=MagicMock(return_value=None),
        open_process_fn=MagicMock(return_value=None),
        is_alive_fn=MagicMock(return_value=True),
        close_handle_fn=MagicMock(),
        clock=FakeClock(),
    )
    kwargs.update(overrides)
    return ProcessConnection(**kwargs), kwargs


class TestNotFound(unittest.TestCase):
    def test_initial_status_before_any_poll(self):
        conn, _ = make_connection()
        self.assertEqual(conn.state, ProcessConnection.SEARCHING)
        self.assertEqual(conn.status, "process FDNYFirefighter.exe\nnot found")
        self.assertIsNone(conn.proc)

    def test_poll_reports_not_found_when_get_pid_returns_none(self):
        conn, kwargs = make_connection(get_pid_fn=MagicMock(return_value=None))
        conn.poll()
        self.assertEqual(conn.state, ProcessConnection.SEARCHING)
        self.assertEqual(conn.status, "process FDNYFirefighter.exe\nnot found")
        kwargs["open_process_fn"].assert_not_called()


class TestAttach(unittest.TestCase):
    def test_attaches_on_first_successful_open(self):
        conn, _ = make_connection(
            get_pid_fn=MagicMock(return_value=111),
            open_process_fn=MagicMock(return_value="HANDLE-1"),
        )
        conn.poll()
        self.assertEqual(conn.state, ProcessConnection.ATTACHED)
        self.assertEqual(conn.pid, 111)
        self.assertEqual(conn.proc, "HANDLE-1")
        self.assertIsNone(conn.status)
        self.assertEqual(conn.attach_count, 1)

    def test_open_process_succeeds_after_some_failures(self):
        open_process_fn = MagicMock(side_effect=[None, None, "HANDLE-1"])
        conn, _ = make_connection(
            get_pid_fn=MagicMock(return_value=111),
            open_process_fn=open_process_fn,
            max_open_attempts=5,
        )
        conn.poll()
        self.assertEqual(conn.state, ProcessConnection.ATTACHED)
        self.assertEqual(conn.proc, "HANDLE-1")
        self.assertEqual(open_process_fn.call_count, 3)

    def test_gives_up_after_max_open_attempts_and_reports_status(self):
        open_process_fn = MagicMock(return_value=None)
        conn, _ = make_connection(
            get_pid_fn=MagicMock(return_value=111),
            open_process_fn=open_process_fn,
            max_open_attempts=5,
        )
        conn.poll()
        self.assertEqual(conn.state, ProcessConnection.SEARCHING)
        self.assertEqual(conn.status, "unable to open pid of\nFDNYFirefighter.exe")
        self.assertEqual(open_process_fn.call_count, 5)


class TestSearchThrottling(unittest.TestCase):
    def test_does_not_search_again_before_interval_elapses(self):
        clock = FakeClock(start=100.0)
        get_pid_fn = MagicMock(return_value=None)
        conn, _ = make_connection(get_pid_fn=get_pid_fn, clock=clock, search_interval=1.0)

        conn.poll()
        conn.poll()
        conn.poll()
        self.assertEqual(get_pid_fn.call_count, 1)

    def test_searches_again_once_interval_elapses(self):
        clock = FakeClock(start=100.0)
        get_pid_fn = MagicMock(return_value=None)
        conn, _ = make_connection(get_pid_fn=get_pid_fn, clock=clock, search_interval=1.0)

        conn.poll()
        clock.advance(1.0)
        conn.poll()
        self.assertEqual(get_pid_fn.call_count, 2)


class TestDeathAndRecovery(unittest.TestCase):
    def test_attached_process_dying_returns_to_searching_and_closes_handle(self):
        close_handle_fn = MagicMock()
        conn, _ = make_connection(
            get_pid_fn=MagicMock(return_value=111),
            open_process_fn=MagicMock(return_value="HANDLE-1"),
            is_alive_fn=MagicMock(return_value=True),
            close_handle_fn=close_handle_fn,
        )
        conn.poll()  # attaches
        self.assertEqual(conn.state, ProcessConnection.ATTACHED)

        conn._is_alive = MagicMock(return_value=False)
        conn.poll()  # detects death

        self.assertEqual(conn.state, ProcessConnection.SEARCHING)
        self.assertIsNone(conn.proc)
        self.assertIsNone(conn.pid)
        self.assertEqual(conn.status, "process FDNYFirefighter.exe\nnot found")
        close_handle_fn.assert_called_once_with("HANDLE-1")

    def test_search_resumes_immediately_after_death_ignoring_interval(self):
        clock = FakeClock(start=100.0)
        get_pid_fn = MagicMock(side_effect=[111, None])
        conn, _ = make_connection(
            get_pid_fn=get_pid_fn,
            open_process_fn=MagicMock(return_value="HANDLE-1"),
            clock=clock,
            search_interval=1.0,
        )
        conn.poll()  # attaches at t=100
        conn._is_alive = MagicMock(return_value=False)
        conn.poll()  # dies, back to searching at t=100 (no time advanced)
        conn.poll()  # should search again immediately, not wait out the interval
        self.assertEqual(get_pid_fn.call_count, 2)

    def test_relaunched_process_is_reattached_with_incremented_attach_count(self):
        get_pid_fn = MagicMock(side_effect=[111, 222])
        open_process_fn = MagicMock(side_effect=["HANDLE-1", "HANDLE-2"])
        close_handle_fn = MagicMock()
        conn, _ = make_connection(
            get_pid_fn=get_pid_fn,
            open_process_fn=open_process_fn,
            close_handle_fn=close_handle_fn,
        )
        conn.poll()  # first attach
        self.assertEqual(conn.attach_count, 1)

        conn._is_alive = MagicMock(return_value=False)
        conn.poll()  # game exited

        conn.poll()  # relaunched game found and reattached
        self.assertEqual(conn.state, ProcessConnection.ATTACHED)
        self.assertEqual(conn.pid, 222)
        self.assertEqual(conn.proc, "HANDLE-2")
        self.assertEqual(conn.attach_count, 2)
        close_handle_fn.assert_called_once_with("HANDLE-1")


class TestClose(unittest.TestCase):
    def test_close_releases_handle_when_attached(self):
        close_handle_fn = MagicMock()
        conn, _ = make_connection(
            get_pid_fn=MagicMock(return_value=111),
            open_process_fn=MagicMock(return_value="HANDLE-1"),
            close_handle_fn=close_handle_fn,
        )
        conn.poll()
        conn.close()
        close_handle_fn.assert_called_once_with("HANDLE-1")
        self.assertIsNone(conn.proc)

    def test_close_is_a_noop_when_never_attached(self):
        close_handle_fn = MagicMock()
        conn, _ = make_connection(close_handle_fn=close_handle_fn)
        conn.close()
        close_handle_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
