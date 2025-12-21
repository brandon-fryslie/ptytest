"""
Basic examples of ptytest usage.

Run with: pytest examples/ -v
"""

import time

import pytest

from ptytest import Keys


class TestBasicUsage:
    """Basic ptytest usage examples."""

    def test_send_shell_command(self, tmux_session):
        """Test sending a shell command and verifying output."""
        # Send a command
        tmux_session.send_keys("echo 'Hello, ptytest!'")

        # Verify the output
        assert tmux_session.verify_text_appears("Hello, ptytest!")

    def test_pane_management(self, tmux_session):
        """Test splitting and counting panes."""
        # Start with 1 pane
        assert tmux_session.get_pane_count() == 1

        # Split horizontally
        tmux_session.split_window("-h")
        assert tmux_session.get_pane_count() == 2

        # Split vertically
        tmux_session.split_window("-v")
        assert tmux_session.get_pane_count() == 3

    def test_raw_keystrokes(self, tmux_session):
        """Test sending raw escape sequences."""
        # Type some text (literal, no Enter)
        tmux_session.send_keys("hello world", literal=True)
        time.sleep(0.1)

        # Verify text is in the buffer
        content = tmux_session.get_pane_content()
        assert "hello world" in content

        # Send Ctrl-U to clear the line
        tmux_session.send_raw(Keys.CTRL_U)
        time.sleep(0.1)

    def test_get_pane_dimensions(self, tmux_session):
        """Test getting pane dimensions."""
        height = tmux_session.get_pane_height()
        width = tmux_session.get_pane_width()

        # Dimensions should be reasonable (exact values can vary by 1)
        assert 38 <= height <= 41
        assert 118 <= width <= 121


@pytest.mark.keybinding
class TestTmuxKeybindings:
    """Examples of testing tmux keybindings."""

    def test_prefix_key(self, tmux_session):
        """Test sending tmux prefix + key."""
        # Send Ctrl-b t (clock mode)
        tmux_session.send_prefix_key('t')
        time.sleep(0.5)

        # Clock mode shows the time
        content = tmux_session.get_pane_content()
        # Any change from empty prompt indicates it worked
        assert len(content.strip()) > 0

        # Press any key to exit clock mode
        tmux_session.send_raw('q')


class TestKeyConstants:
    """Examples using the Keys class."""

    def test_ctrl_keys(self, tmux_session):
        """Test various Ctrl key combinations."""
        # Type something
        tmux_session.send_keys("some text here", literal=True)
        time.sleep(0.1)

        # Ctrl-A moves to beginning of line
        tmux_session.send_raw(Keys.CTRL_A)

        # Ctrl-K kills to end of line
        tmux_session.send_raw(Keys.CTRL_K)
        time.sleep(0.1)

    def test_meta_keys(self, tmux_session):
        """Test Meta/Alt key combinations."""
        # Meta-f moves forward one word
        tmux_session.send_keys("hello world test", literal=True)
        tmux_session.send_raw(Keys.CTRL_A)  # Go to start
        tmux_session.send_raw(Keys.meta('f'))  # Forward one word
        time.sleep(0.1)

    def test_arrow_keys(self, tmux_session):
        """Test arrow key navigation."""
        # Send arrow keys
        tmux_session.send_raw(Keys.UP)
        tmux_session.send_raw(Keys.DOWN)
        tmux_session.send_raw(Keys.LEFT)
        tmux_session.send_raw(Keys.RIGHT)


class TestContextManager:
    """Examples using TmuxSession as context manager."""

    def test_with_statement(self):
        """Test using with statement for automatic cleanup."""
        from ptytest import TmuxSession

        with TmuxSession() as session:
            session.send_keys("echo test")
            assert session.verify_text_appears("test")
        # Session automatically cleaned up here

    def test_factory_fixture(self, tmux_session_factory):
        """Test creating multiple sessions with factory."""
        session1 = tmux_session_factory(width=80, height=24)
        session2 = tmux_session_factory(width=120, height=40)

        assert session1.get_pane_width() == 80
        assert session2.get_pane_width() == 120
        # Both sessions cleaned up automatically
