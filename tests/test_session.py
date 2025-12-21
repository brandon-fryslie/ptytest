"""Tests for TmuxSession and PtySession classes."""

import time

import pytest

from ptytest import FzfKeys, Keys, PtySession, TmuxSession, VimKeys


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
        with pytest.raises(TimeoutError):
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


@pytest.mark.direct_pty
class TestPtySessionBasics:
    """Test basic PtySession functionality."""

    def test_session_creates_and_cleans_up(self):
        """Test that PtySession creates and cleans up properly."""
        session = PtySession(["bash", "--norc", "--noprofile"])
        try:
            assert session.process is not None
            assert session.process.isalive()
        finally:
            session.cleanup()

        # After cleanup, process should be dead
        assert not session.process.isalive()

    def test_context_manager(self):
        """Test context manager properly cleans up."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            assert session.process.isalive()
            process = session.process

        # After context, process should be dead
        assert not process.isalive()

    def test_send_keys_executes(self):
        """Test that send_keys actually runs commands."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            session.send_keys("echo PTY_MARKER")
            assert session.verify_text_appears("PTY_MARKER", timeout=2.0)

    def test_send_keys_literal(self):
        """Test send_keys with literal=True."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            # Send without Enter
            session.send_keys("echo TEST", literal=True)
            time.sleep(0.2)

            # Should see the command but not output
            content = session.get_content()
            assert "echo TEST" in content

            # Now press Enter
            session.send_raw(Keys.ENTER)
            assert session.verify_text_appears("TEST", timeout=2.0)

    def test_get_content(self):
        """Test getting terminal content."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            session.send_keys("echo CONTENT_CHECK")
            time.sleep(0.3)

            content = session.get_content()
            assert isinstance(content, str)
            assert "CONTENT_CHECK" in content

    def test_send_raw(self):
        """Test sending raw escape sequences."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            # Send Ctrl-L (clear screen)
            session.send_raw(Keys.CTRL_L)
            time.sleep(0.2)

            # Verify it doesn't crash - content may or may not be empty
            content = session.get_content()
            assert isinstance(content, str)

    def test_verify_text_appears_timeout(self):
        """Test that verify_text_appears returns False on timeout."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            result = session.verify_text_appears(
                "THIS_TEXT_WILL_NEVER_APPEAR",
                timeout=0.5
            )
            assert result is False

    def test_wait_for_text_raises(self):
        """Test that wait_for_text raises on timeout."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            with pytest.raises(TimeoutError):
                session.wait_for_text(
                    "THIS_TEXT_WILL_NEVER_APPEAR",
                    timeout=0.5
                )


@pytest.mark.direct_pty
class TestPtySessionApplications:
    """Test PtySession with different applications."""

    def test_cat_application(self):
        """Test PtySession with cat (simple echo app)."""
        with PtySession(["cat"]) as session:
            session.send_keys("hello from cat", literal=True)
            session.send_raw(Keys.ENTER)
            time.sleep(0.2)

            content = session.get_content()
            assert "hello from cat" in content

    def test_python_repl(self):
        """Test PtySession with Python REPL."""
        with PtySession(["python3", "-u"]) as session:
            # Wait for Python prompt
            assert session.verify_text_appears(">>>", timeout=2.0)

            # Execute Python command
            session.send_keys("print('PYTHON_TEST')")
            time.sleep(0.3)

            content = session.get_content()
            assert "PYTHON_TEST" in content

    def test_bash_command_chain(self):
        """Test executing multiple commands in bash."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            session.send_keys("echo FIRST")
            assert session.verify_text_appears("FIRST", timeout=2.0)

            session.send_keys("echo SECOND")
            assert session.verify_text_appears("SECOND", timeout=2.0)

            content = session.get_content()
            assert "FIRST" in content
            assert "SECOND" in content


class TestExtendedKeys:
    """Test extended Keys class features."""

    def test_shift_arrow_keys(self):
        """Test Shift+Arrow key constants."""
        assert Keys.SHIFT_UP == '\x1b[1;2A'
        assert Keys.SHIFT_DOWN == '\x1b[1;2B'
        assert Keys.SHIFT_LEFT == '\x1b[1;2D'
        assert Keys.SHIFT_RIGHT == '\x1b[1;2C'

    def test_ctrl_arrow_keys(self):
        """Test Ctrl+Arrow key constants."""
        assert Keys.CTRL_UP == '\x1b[1;5A'
        assert Keys.CTRL_DOWN == '\x1b[1;5B'
        assert Keys.CTRL_LEFT == '\x1b[1;5D'
        assert Keys.CTRL_RIGHT == '\x1b[1;5C'

    def test_alt_arrow_keys(self):
        """Test Alt+Arrow key constants."""
        assert Keys.ALT_UP == '\x1b[1;3A'
        assert Keys.ALT_DOWN == '\x1b[1;3B'
        assert Keys.ALT_LEFT == '\x1b[1;3D'
        assert Keys.ALT_RIGHT == '\x1b[1;3C'

    def test_shift_function_keys(self):
        """Test Shift+Function key constants."""
        assert Keys.SHIFT_F1 == '\x1b[1;2P'
        assert Keys.SHIFT_F5 == '\x1b[15;2~'
        assert Keys.SHIFT_F12 == '\x1b[24;2~'

    def test_common_chars(self):
        """Test common character constants."""
        assert Keys.SPACE == ' '
        assert Keys.SLASH == '/'
        assert Keys.QUESTION == '?'
        assert Keys.COLON == ':'

    def test_shift_tab(self):
        """Test Shift+Tab (backtab) constant."""
        assert Keys.SHIFT_TAB == '\x1b[Z'

    def test_vim_command_helper(self):
        """Test vim_command helper method."""
        assert Keys.vim_command('wq') == '\x1b:wq\r'
        assert Keys.vim_command('set number') == '\x1b:set number\r'

    def test_vim_mode_helpers(self):
        """Test vim mode helper methods."""
        assert Keys.vim_insert() == 'i'
        assert Keys.vim_normal() == '\x1b'


class TestFzfKeys:
    """Test FzfKeys class."""

    def test_fzf_navigation_keys(self):
        """Test fzf navigation key bindings."""
        assert FzfKeys.UP == Keys.UP
        assert FzfKeys.DOWN == Keys.DOWN
        assert FzfKeys.CTRL_K == Keys.CTRL_K
        assert FzfKeys.CTRL_J == Keys.CTRL_J

    def test_fzf_selection_keys(self):
        """Test fzf selection key bindings."""
        assert FzfKeys.TAB == Keys.TAB
        assert FzfKeys.SHIFT_TAB == Keys.SHIFT_TAB
        assert FzfKeys.ENTER == Keys.ENTER

    def test_fzf_action_keys(self):
        """Test fzf action key bindings."""
        assert FzfKeys.CTRL_T == Keys.CTRL_T
        assert FzfKeys.CTRL_A == Keys.CTRL_A

    def test_fzf_cancel_keys(self):
        """Test fzf cancel key bindings."""
        assert FzfKeys.ESC == Keys.ESCAPE
        assert FzfKeys.CTRL_C == Keys.CTRL_C


class TestVimKeys:
    """Test VimKeys class."""

    def test_vim_mode_switching(self):
        """Test vim mode switching keys."""
        assert VimKeys.INSERT == 'i'
        assert VimKeys.INSERT_APPEND == 'a'
        assert VimKeys.NORMAL == Keys.ESCAPE
        assert VimKeys.VISUAL == 'v'

    def test_vim_navigation(self):
        """Test vim navigation keys."""
        assert VimKeys.LEFT == 'h'
        assert VimKeys.DOWN == 'j'
        assert VimKeys.UP == 'k'
        assert VimKeys.RIGHT == 'l'
        assert VimKeys.WORD_FORWARD == 'w'
        assert VimKeys.LINE_START == '0'
        assert VimKeys.LINE_END == '$'

    def test_vim_editing(self):
        """Test vim editing keys."""
        assert VimKeys.DELETE_CHAR == 'x'
        assert VimKeys.DELETE_LINE == 'dd'
        assert VimKeys.YANK_LINE == 'yy'
        assert VimKeys.UNDO == 'u'

    def test_vim_command_methods(self):
        """Test vim command helper methods."""
        assert VimKeys.write() == '\x1b:w\r'
        assert VimKeys.quit() == '\x1b:q\r'
        assert VimKeys.write_quit() == '\x1b:wq\r'
        assert VimKeys.quit_force() == '\x1b:q!\r'
