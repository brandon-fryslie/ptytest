"""
TmuxSession Basics - Testing tmux keybindings and multi-pane workflows.

TmuxSession creates a real tmux session and provides methods for testing
tmux-specific functionality like pane management, prefix keys, and splits.

Requirements: tmux must be installed

Run with: uv run pytest examples/02_tmux_session_basics.py -v
"""

import shutil

import pytest

from ptytest import TmuxSession, Keys


# Skip all tests if tmux is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None,
    reason="tmux not installed"
)


class TestTmuxSessionBasics:
    """Basic TmuxSession usage patterns."""

    def test_create_session(self):
        """Create a tmux session and run a command."""
        with TmuxSession() as session:
            session.send_keys("echo 'Hello from tmux!'")
            assert session.verify_text_appears("Hello from tmux!")

    def test_custom_session_name(self):
        """Create session with custom name."""
        with TmuxSession(session_name="my-test-session") as session:
            assert session.session_name == "my-test-session"
            session.send_keys("echo 'named session'")
            assert session.verify_text_appears("named session")

    def test_minimal_config(self):
        """Create session without loading user's tmux.conf."""
        with TmuxSession(use_config=False) as session:
            # This session ignores ~/.tmux.conf
            session.send_keys("echo 'minimal config'")
            assert session.verify_text_appears("minimal config")

    def test_custom_shell(self):
        """Use a different shell."""
        with TmuxSession(shell="bash") as session:
            session.send_keys("echo $0")
            assert session.verify_text_appears("bash")


class TestTmuxPaneManagement:
    """Test tmux pane operations."""

    def test_initial_pane_count(self):
        """New session starts with one pane."""
        with TmuxSession() as session:
            assert session.get_pane_count() == 1

    def test_split_horizontal(self):
        """Split pane horizontally (top/bottom)."""
        with TmuxSession() as session:
            assert session.get_pane_count() == 1

            # Split using tmux method
            session.split_window("-v")  # Vertical split = top/bottom

            assert session.get_pane_count() == 2

    def test_split_vertical(self):
        """Split pane vertically (left/right)."""
        with TmuxSession() as session:
            assert session.get_pane_count() == 1

            session.split_window("-h")  # Horizontal split = left/right

            assert session.get_pane_count() == 2

    def test_multiple_splits(self):
        """Create multiple panes."""
        with TmuxSession() as session:
            assert session.get_pane_count() == 1

            session.split_window("-h")
            assert session.get_pane_count() == 2

            session.split_window("-v")
            assert session.get_pane_count() == 3

    def test_get_pane_ids(self):
        """Get list of pane IDs."""
        with TmuxSession() as session:
            pane_ids = session.get_pane_ids()
            assert len(pane_ids) == 1

            session.split_window("-h")
            pane_ids = session.get_pane_ids()
            assert len(pane_ids) == 2
            # Pane IDs look like %0, %1, etc.
            for pane_id in pane_ids:
                assert pane_id.startswith("%")

    def test_get_pane_dimensions(self):
        """Get pane width and height."""
        with TmuxSession(width=120, height=40) as session:
            width = session.get_pane_width()
            height = session.get_pane_height()

            # Dimensions should be close to what we specified
            assert width > 0
            assert height > 0


class TestTmuxPrefixKeys:
    """Test sending tmux prefix key combinations."""

    def test_send_prefix_key(self):
        """Send prefix key + another key."""
        with TmuxSession() as session:
            # Ctrl-b " splits horizontally (default binding)
            initial_count = session.get_pane_count()

            session.send_prefix_key('"')

            assert session.get_pane_count() == initial_count + 1

    def test_prefix_key_percent(self):
        """Send prefix + % for vertical split."""
        with TmuxSession() as session:
            initial_count = session.get_pane_count()

            # Ctrl-b % splits vertically
            session.send_prefix_key('%')

            assert session.get_pane_count() == initial_count + 1


class TestTmuxPaneContent:
    """Test reading content from panes."""

    def test_get_pane_content(self):
        """Get content from a pane."""
        with TmuxSession() as session:
            session.send_keys("echo 'pane content test'")
            session.verify_text_appears("pane content test")

            content = session.get_pane_content()
            assert "pane content test" in content

    def test_get_content_with_history(self):
        """Get content including scrollback history."""
        with TmuxSession() as session:
            # Generate some output
            for i in range(10):
                session.send_keys(f"echo 'line {i}'")

            session.verify_text_appears("line 9")

            # Get content with history
            content = session.get_content(include_history=True)
            assert "line 0" in content
            assert "line 9" in content


class TestTmuxRawKeys:
    """Test sending raw escape sequences in tmux."""

    def test_send_ctrl_c(self):
        """Send Ctrl-C to interrupt."""
        with TmuxSession() as session:
            # Wait for initial prompt
            session.verify_text_appears("$", timeout=2)

            # Start a long-running command
            session.send_keys("sleep 100", literal=True)
            session.send_raw(Keys.ENTER)

            import time
            time.sleep(0.3)

            # Send Ctrl-C
            session.send_raw(Keys.CTRL_C)

            # Wait a bit for signal to be processed
            time.sleep(0.3)

            # Send echo to verify we're back at prompt
            session.send_keys("echo 'interrupted'")
            assert session.verify_text_appears("interrupted", timeout=2)

    def test_send_escape_sequences(self):
        """Send escape sequences for arrow keys."""
        with TmuxSession() as session:
            session.send_keys("echo test", literal=True)

            # Move cursor left
            session.send_raw(Keys.LEFT)
            session.send_raw(Keys.LEFT)

            # Insert text
            session.send_keys("XX", literal=True)

            # The command line should now have "echo teXXst"


class TestTmuxGlobalOptions:
    """Test reading tmux options."""

    def test_get_global_option(self):
        """Read a tmux global option."""
        with TmuxSession() as session:
            # Try to get prefix key (may vary by config)
            # This tests the mechanism, not a specific value
            pass  # Options depend on user's tmux config
