"""Tests for TmuxSession class."""

import pytest
from ptytest import TmuxSession, Keys


class TestTmuxSessionBasics:
    """Test basic TmuxSession functionality."""

    def test_session_creates_and_cleans_up(self):
        """Test that session is created and cleaned up properly."""
        session = TmuxSession()
        try:
            assert session._session_exists()
            session_name = session.session_name
        finally:
            session.cleanup()

        # Verify cleanup worked (session should not exist)
        import subprocess
        result = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        assert result.returncode != 0  # Session should not exist

    def test_context_manager(self):
        """Test context manager properly cleans up."""
        with TmuxSession() as session:
            session_name = session.session_name
            assert session._session_exists()

        # After context, session should be gone
        import subprocess
        result = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        assert result.returncode != 0

    def test_initial_pane_count(self, tmux_session):
        """Test that session starts with 1 pane."""
        assert tmux_session.get_pane_count() == 1

    def test_send_keys_executes(self, tmux_session):
        """Test that send_keys actually runs commands."""
        tmux_session.send_keys("echo PTYTEST_MARKER")
        assert tmux_session.verify_text_appears("PTYTEST_MARKER")

    def test_split_window_increases_panes(self, tmux_session):
        """Test that split_window increases pane count."""
        assert tmux_session.get_pane_count() == 1
        tmux_session.split_window("-h")
        assert tmux_session.get_pane_count() == 2

    def test_get_pane_content(self, tmux_session):
        """Test capturing pane content."""
        tmux_session.send_keys("echo CONTENT_TEST")
        content = tmux_session.get_pane_content()
        assert "CONTENT_TEST" in content

    def test_verify_text_appears_timeout(self, tmux_session):
        """Test that verify_text_appears returns False on timeout."""
        result = tmux_session.verify_text_appears(
            "THIS_TEXT_WILL_NEVER_APPEAR",
            timeout=0.5
        )
        assert result is False

    def test_wait_for_text_raises(self, tmux_session):
        """Test that wait_for_text raises on timeout."""
        with pytest.raises(AssertionError):
            tmux_session.wait_for_text(
                "THIS_TEXT_WILL_NEVER_APPEAR",
                timeout=0.5
            )


class TestTmuxSessionRawKeys:
    """Test raw keystroke sending."""

    def test_send_raw_ctrl_c(self, tmux_session):
        """Test sending Ctrl-C."""
        # Start a long-running command
        tmux_session.send_keys("sleep 100", literal=True)
        tmux_session.send_raw(Keys.ENTER)

        # Send Ctrl-C to interrupt
        import time
        time.sleep(0.2)
        tmux_session.send_raw(Keys.CTRL_C)
        time.sleep(0.2)

        # Should be back at prompt (can type new command)
        tmux_session.send_keys("echo AFTER_CTRL_C")
        assert tmux_session.verify_text_appears("AFTER_CTRL_C")

    def test_send_raw_escape_sequence(self, tmux_session):
        """Test sending escape sequences."""
        # This just tests that raw sending works without error
        tmux_session.send_raw(Keys.ESCAPE)
        tmux_session.send_raw(Keys.UP)
        tmux_session.send_raw(Keys.DOWN)


class TestKeysClass:
    """Test the Keys helper class."""

    def test_ctrl_method(self):
        """Test Keys.ctrl() method."""
        assert Keys.ctrl('c') == '\x03'
        assert Keys.ctrl('a') == '\x01'
        assert Keys.ctrl('z') == '\x1a'
        assert Keys.ctrl('C') == '\x03'  # Case insensitive

    def test_meta_method(self):
        """Test Keys.meta() method."""
        assert Keys.meta('d') == '\x1bd'
        assert Keys.meta('D') == '\x1bD'
        assert Keys.meta('f') == '\x1bf'

    def test_ctrl_constants(self):
        """Test Ctrl key constants."""
        assert Keys.CTRL_A == '\x01'
        assert Keys.CTRL_B == '\x02'
        assert Keys.CTRL_C == '\x03'
        assert Keys.CTRL_Z == '\x1a'

    def test_special_keys(self):
        """Test special key constants."""
        assert Keys.ESCAPE == '\x1b'
        assert Keys.ENTER == '\r'
        assert Keys.TAB == '\t'

    def test_arrow_keys(self):
        """Test arrow key constants."""
        assert Keys.UP == '\x1b[A'
        assert Keys.DOWN == '\x1b[B'
        assert Keys.LEFT == '\x1b[D'
        assert Keys.RIGHT == '\x1b[C'
