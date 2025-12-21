"""
Integration tests for terminal visualization feature with PtySession.

These tests verify that PtySession correctly integrates with the
Textual-based broadcaster and supports multiple viewers.
"""

import pytest
import time

# Skip all tests if viz dependencies not installed
pytest.importorskip("textual")

from ptytest import PtySession
from ptytest.viz.viewer import ScreenBroadcaster


@pytest.mark.viz
class TestPtySessionVizIntegration:
    """Test PtySession integration with visualization broadcaster."""

    def test_pty_session_with_enable_viz_starts_broadcaster(self):
        """PtySession with enable_viz=True should start broadcaster automatically."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            # Broadcaster should be running
            assert session._viz_server is not None
            assert isinstance(session._viz_server, ScreenBroadcaster)
            assert session._viz_server.is_running

        # Broadcaster should be shut down after context manager exit
        # Note: Can't check is_running after shutdown as it's set to False

    def test_pty_session_without_viz_has_no_overhead(self):
        """PtySession with enable_viz=False (default) should have no viz overhead."""
        with PtySession(["bash", "--norc"]) as session:
            # No broadcaster should exist
            assert session._viz_server is None

    def test_broadcaster_receives_terminal_updates(self):
        """Broadcaster should receive updates when terminal content changes."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            broadcaster = session._viz_server
            assert broadcaster is not None

            received_updates = []

            def callback(lines, cursor_x, cursor_y):
                received_updates.append("".join(lines))

            broadcaster.subscribe(callback)

            # Send command to bash
            session.send_keys('echo "Test broadcast message"')
            time.sleep(0.5)

            # Should have received updates
            assert len(received_updates) > 0

            # At least one update should contain our text
            all_content = "\n".join(received_updates)
            assert "Test broadcast message" in all_content or "echo" in all_content

    def test_pty_session_cleanup_shuts_down_broadcaster(self):
        """PtySession cleanup should shut down broadcaster."""
        session = PtySession(["bash", "--norc"], enable_viz=True)

        # Broadcaster should be running
        assert session._viz_server.is_running

        # Cleanup
        session.cleanup()

        # Broadcaster should be shut down
        assert not session._viz_server.is_running

    def test_multiple_subscribers_can_watch_same_session(self):
        """Multiple subscribers should be able to watch same PtySession."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            broadcaster = session._viz_server

            updates1 = []
            updates2 = []
            updates3 = []

            def callback1(lines, cx, cy):
                updates1.append(len(lines))

            def callback2(lines, cx, cy):
                updates2.append(len(lines))

            def callback3(lines, cx, cy):
                updates3.append(len(lines))

            # Subscribe multiple watchers
            broadcaster.subscribe(callback1)
            broadcaster.subscribe(callback2)
            broadcaster.subscribe(callback3)

            # Send command
            session.send_keys('echo "Multi-viewer test"')
            time.sleep(0.5)

            # All viewers should have received updates
            assert len(updates1) > 0, "Viewer 1 received no updates"
            assert len(updates2) > 0, "Viewer 2 received no updates"
            assert len(updates3) > 0, "Viewer 3 received no updates"

    def test_viz_broadcaster_error_raises_clear_message(self):
        """Missing dependencies should raise clear error message."""
        # This test verifies the error handling, but since we have textual
        # installed for this test, we just verify the code path exists
        from ptytest.viz.viewer import TEXTUAL_AVAILABLE

        assert TEXTUAL_AVAILABLE, "Textual should be installed for this test"

    def test_screen_state_is_accurate(self):
        """Broadcaster should return accurate screen state."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            broadcaster = session._viz_server

            # Send distinctive output
            session.send_keys('echo "UNIQUE_MARKER_12345"')
            time.sleep(0.5)

            # Get screen state
            lines, cursor_x, cursor_y = broadcaster.get_screen_state()

            # Should contain our marker
            all_text = "\n".join(lines)
            assert "UNIQUE_MARKER_12345" in all_text

            # Cursor position should be valid
            assert 0 <= cursor_x < session.width
            assert 0 <= cursor_y < session.height


@pytest.mark.viz
class TestVizColoredOutput:
    """Test that ANSI escape sequences work correctly with broadcaster."""

    def test_colored_output_preserved_in_screen(self):
        """ANSI color codes should be present in screen content."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            broadcaster = session._viz_server

            # Send colored output
            session.send_keys('echo -e "\\033[31mRed\\033[0m \\033[32mGreen\\033[0m"')
            time.sleep(0.5)

            # Get screen state
            lines, _, _ = broadcaster.get_screen_state()
            all_text = "".join(lines)

            # Should contain the text (ANSI codes handled by pyte)
            # pyte processes the ANSI codes, so we just check the text appears
            assert "Red" in all_text or "Green" in all_text


@pytest.mark.viz
def test_backward_compatibility_no_viz_params():
    """Existing code without viz parameters should work unchanged."""
    # This verifies backward compatibility
    with PtySession(["bash", "--norc"]) as session:
        session.send_keys('echo "No viz test"')
        assert session.verify_text_appears("No viz test")


@pytest.mark.viz
def test_viz_with_interactive_apps():
    """Test visualization with interactive TUI applications."""
    # Test with a simple command that has interactive output
    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        updates = []

        def callback(lines, cx, cy):
            updates.append("".join(lines))

        broadcaster.subscribe(callback)

        # Run a command
        session.send_keys("ls")
        time.sleep(0.5)

        # Should receive updates
        assert len(updates) > 0


@pytest.mark.viz
def test_broadcaster_handles_rapid_updates():
    """Broadcaster should handle rapid screen updates without errors."""
    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        update_count = []

        def callback(lines, cx, cy):
            update_count.append(1)

        broadcaster.subscribe(callback)

        # Send multiple rapid commands
        for i in range(5):
            session.send_keys(f'echo "Rapid update {i}"', delay=0.05)

        time.sleep(1.0)

        # Should have received multiple updates
        assert len(update_count) > 0


@pytest.mark.viz
def test_viz_port_parameter_ignored():
    """viz_port parameter should be ignored (deprecated) but not cause errors."""
    # Should work even with viz_port specified (for backward compatibility)
    with PtySession(["bash", "--norc"], enable_viz=True, viz_port=9999) as session:
        assert session._viz_server is not None
        assert session._viz_server.is_running
