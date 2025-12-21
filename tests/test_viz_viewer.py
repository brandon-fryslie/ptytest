"""
Tests for the visualization viewer using ptytest.

These tests verify that the Textual-based viewer works correctly.
"""

import time
import threading

import pytest

from ptytest import PtySession, Keys
from ptytest.viz import ScreenBroadcaster, TerminalViewer


class TestScreenBroadcasterUnit:
    """Unit tests for ScreenBroadcaster."""

    def test_broadcaster_starts_and_stops(self):
        """Broadcaster can start and shutdown cleanly."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session)
            assert not broadcaster.is_running

            broadcaster.start()
            assert broadcaster.is_running

            broadcaster.shutdown()
            assert not broadcaster.is_running

    def test_broadcaster_gets_screen_state(self):
        """Broadcaster can retrieve current screen state."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")
            session.send_keys("echo 'TEST_OUTPUT_12345'")
            session.verify_text_appears("TEST_OUTPUT_12345")

            broadcaster = ScreenBroadcaster(session)
            lines, cursor_x, cursor_y = broadcaster.get_screen_state()

            assert isinstance(lines, list)
            assert len(lines) > 0
            # The output should be somewhere in the screen
            content = "\n".join(lines)
            assert "TEST_OUTPUT_12345" in content

    def test_broadcaster_notifies_subscribers(self):
        """Broadcaster notifies subscribers when screen changes."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session, update_interval=0.05)
            broadcaster.start()

            updates = []
            def on_update(lines, cursor_x, cursor_y):
                updates.append((lines, cursor_x, cursor_y))

            broadcaster.subscribe(on_update)

            try:
                # Generate some output
                session.send_keys("echo 'SUBSCRIBER_TEST'")
                session.verify_text_appears("SUBSCRIBER_TEST")

                # Wait for broadcaster to pick up change
                time.sleep(0.2)

                # Should have received at least one update
                assert len(updates) > 0

                # Verify content is in one of the updates
                found = False
                for lines, _, _ in updates:
                    if "SUBSCRIBER_TEST" in "\n".join(lines):
                        found = True
                        break
                assert found, "Expected 'SUBSCRIBER_TEST' in subscriber updates"

            finally:
                broadcaster.shutdown()

    def test_broadcaster_unsubscribe(self):
        """Can unsubscribe from broadcaster."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session, update_interval=0.05)
            broadcaster.start()

            updates = []
            def on_update(lines, cursor_x, cursor_y):
                updates.append(1)

            broadcaster.subscribe(on_update)

            try:
                session.send_keys("echo 'before'")
                session.verify_text_appears("before")
                time.sleep(0.15)

                count_before = len(updates)

                # Unsubscribe
                broadcaster.unsubscribe(on_update)

                # Generate more output
                session.send_keys("echo 'after'")
                session.verify_text_appears("after")
                time.sleep(0.15)

                count_after = len(updates)

                # Should not have received more updates after unsubscribe
                assert count_after == count_before

            finally:
                broadcaster.shutdown()


class TestTerminalViewerUnit:
    """Unit tests for TerminalViewer."""

    def test_viewer_can_be_created(self):
        """TerminalViewer can be instantiated."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            try:
                viewer = TerminalViewer(broadcaster, session_name="test")
                assert viewer is not None
                assert viewer.session_name == "test"
            finally:
                broadcaster.shutdown()

    def test_viewer_runs_and_quits(self):
        """TerminalViewer can run and be quit programmatically."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            viewer = TerminalViewer(broadcaster, session_name="test")

            # Run viewer in background thread
            viewer_error = []
            def run_viewer():
                try:
                    viewer.run()
                except Exception as e:
                    viewer_error.append(e)

            thread = threading.Thread(target=run_viewer, daemon=True)
            thread.start()

            # Give it time to start
            time.sleep(0.5)

            # Quit the viewer
            viewer.exit()

            # Wait for thread to finish
            thread.join(timeout=2)

            broadcaster.shutdown()

            # Check no errors occurred
            if viewer_error:
                pytest.fail(f"Viewer raised error: {viewer_error[0]}")


class TestPtySessionVizIntegration:
    """Integration tests for PtySession with visualization."""

    def test_enable_viz_creates_broadcaster(self):
        """enable_viz=True creates a broadcaster on the session."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            session.verify_text_appears("$")

            assert session._viz_server is not None
            assert isinstance(session._viz_server, ScreenBroadcaster)
            assert session._viz_server.is_running

    def test_viz_disabled_by_default(self):
        """Visualization is disabled by default."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")
            assert session._viz_server is None

    def test_viz_with_commands(self):
        """Visualization works while running commands."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            session.verify_text_appears("$")

            broadcaster = session._viz_server

            # Run some commands
            session.send_keys("echo 'VIZ_TEST_1'")
            session.verify_text_appears("VIZ_TEST_1")

            session.send_keys("echo 'VIZ_TEST_2'")
            session.verify_text_appears("VIZ_TEST_2")

            # Verify broadcaster can still get screen state
            lines, _, _ = broadcaster.get_screen_state()
            content = "\n".join(lines)
            assert "VIZ_TEST_2" in content
