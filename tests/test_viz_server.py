"""
Unit tests for terminal visualization functionality.

These tests verify the Textual-based viewer, screen broadcaster,
and multi-viewer support without requiring browser.
"""

import pytest
import time
import threading

# Skip all tests if viz dependencies not installed
pytest.importorskip("textual")

from ptytest import PtySession
from ptytest.viz.viewer import ScreenBroadcaster, TerminalViewer


@pytest.mark.viz
class TestScreenBroadcaster:
    """Test screen broadcaster lifecycle and subscription management."""

    def test_broadcaster_starts_and_stops(self):
        """Broadcaster should start and stop cleanly."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)

            # Start
            broadcaster.start()
            assert broadcaster.is_running

            # Stop
            broadcaster.shutdown()
            assert not broadcaster.is_running

    def test_broadcaster_get_screen_state(self):
        """Broadcaster should return screen state thread-safely."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys('echo "test content"')
            time.sleep(0.3)

            broadcaster = ScreenBroadcaster(session)
            lines, cursor_x, cursor_y = broadcaster.get_screen_state()

            # Should get list of lines
            assert isinstance(lines, list)
            assert len(lines) > 0

            # Should get cursor position
            assert isinstance(cursor_x, int)
            assert isinstance(cursor_y, int)
            assert cursor_x >= 0
            assert cursor_y >= 0

    def test_broadcaster_subscribe_and_unsubscribe(self):
        """Broadcaster should support subscribe/unsubscribe."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)

            received_updates = []

            def callback(lines, cursor_x, cursor_y):
                received_updates.append((lines, cursor_x, cursor_y))

            # Subscribe
            broadcaster.subscribe(callback)
            broadcaster.start()

            # Send some output
            session.send_keys('echo "Hello broadcaster"')
            time.sleep(0.5)

            # Should have received updates
            assert len(received_updates) > 0

            # Unsubscribe
            broadcaster.unsubscribe(callback)
            old_count = len(received_updates)

            # Send more output
            session.send_keys('echo "After unsubscribe"')
            time.sleep(0.3)

            # Should not receive new updates
            assert len(received_updates) == old_count

            broadcaster.shutdown()

    def test_broadcaster_multiple_subscribers(self):
        """Broadcaster should support multiple subscribers."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)

            updates1 = []
            updates2 = []
            updates3 = []

            def callback1(lines, cx, cy):
                updates1.append(len(lines))

            def callback2(lines, cx, cy):
                updates2.append(len(lines))

            def callback3(lines, cx, cy):
                updates3.append(len(lines))

            # Subscribe all
            broadcaster.subscribe(callback1)
            broadcaster.subscribe(callback2)
            broadcaster.subscribe(callback3)

            broadcaster.start()

            # Send output
            session.send_keys('echo "Multi-subscriber test"')
            time.sleep(0.5)

            # All should receive updates
            assert len(updates1) > 0
            assert len(updates2) > 0
            assert len(updates3) > 0

            broadcaster.shutdown()

    def test_broadcaster_handles_subscriber_errors(self):
        """Broadcaster should not crash if a subscriber raises exception."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)

            good_updates = []

            def bad_callback(lines, cx, cy):
                raise RuntimeError("Subscriber error!")

            def good_callback(lines, cx, cy):
                good_updates.append(lines)

            # Subscribe both (bad one first)
            broadcaster.subscribe(bad_callback)
            broadcaster.subscribe(good_callback)

            broadcaster.start()

            # Send output
            session.send_keys('echo "Error handling test"')
            time.sleep(0.5)

            # Good subscriber should still receive updates despite bad one
            assert len(good_updates) > 0

            broadcaster.shutdown()


@pytest.mark.viz
class TestScreenBroadcasterThreadSafety:
    """Test thread safety of screen broadcaster."""

    def test_concurrent_screen_reads(self):
        """Multiple threads should be able to read screen state safely."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            results = []

            def reader():
                for _ in range(10):
                    lines, cx, cy = broadcaster.get_screen_state()
                    results.append(len(lines))
                    time.sleep(0.01)

            # Start multiple reader threads
            threads = [threading.Thread(target=reader) for _ in range(5)]
            for t in threads:
                t.start()

            # Send some output while threads are reading
            session.send_keys('echo "Concurrent read test"')

            for t in threads:
                t.join()

            # All readers should have completed without errors
            assert len(results) == 50  # 10 reads * 5 threads

            broadcaster.shutdown()


@pytest.mark.viz
class TestTerminalViewer:
    """Test TerminalViewer widget creation and basic functionality."""

    def test_viewer_can_be_created(self):
        """TerminalViewer should be creatable with a broadcaster."""
        with PtySession(["bash", "--norc"]) as session:
            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            # Should be able to create viewer (not run it)
            viewer = TerminalViewer(broadcaster, session_name="test-session")
            assert viewer is not None
            assert viewer.session_name == "test-session"
            assert viewer.broadcaster is broadcaster

            broadcaster.shutdown()

    @pytest.mark.skip(reason="Cannot run interactive Textual app in pytest without special setup")
    def test_viewer_displays_screen_content(self):
        """Viewer should display screen content when run."""
        # This test would require running the Textual app which is interactive
        # In practice, this would be tested manually or with Textual's test framework
        pass


@pytest.mark.viz
def test_broadcaster_cleanup_on_session_end():
    """Broadcaster should handle session cleanup gracefully."""
    session = PtySession(["bash", "--norc"])
    broadcaster = ScreenBroadcaster(session)
    broadcaster.start()

    assert broadcaster.is_running

    # Close session
    session.cleanup()

    # Broadcaster should still be running but will stop getting updates
    time.sleep(0.3)

    # Shutdown broadcaster
    broadcaster.shutdown()
    assert not broadcaster.is_running
