"""
PtySession Basics - Testing any interactive CLI application.

PtySession spawns processes directly via PTY (pseudo-terminal) and maintains
a virtual screen using pyte. No tmux required.

Run with: uv run pytest examples/01_pty_session_basics.py -v
"""

import pytest

from ptytest import PtySession, Keys


class TestPtySessionBasics:
    """Basic PtySession usage patterns."""

    def test_spawn_bash_and_run_command(self):
        """Spawn bash and run a simple command."""
        with PtySession(["bash", "--norc", "--noprofile"]) as session:
            # Send a command (Enter is added automatically)
            session.send_keys("echo 'Hello from ptytest!'")

            # Verify the output appears
            assert session.verify_text_appears("Hello from ptytest!")

    def test_send_keys_literal(self):
        """Send keys without automatic Enter."""
        with PtySession(["bash", "--norc"]) as session:
            # literal=True means don't add Enter
            session.send_keys("partial", literal=True)

            # The text should be in the buffer but not executed
            content = session.get_content()
            assert "partial" in content

    def test_send_raw_escape_sequences(self):
        """Send raw escape sequences and control characters."""
        with PtySession(["bash", "--norc"]) as session:
            # Type some text
            session.send_keys("hello world", literal=True)

            # Send Ctrl-A to go to beginning of line
            session.send_raw(Keys.CTRL_A)

            # Send Ctrl-K to kill to end of line
            session.send_raw(Keys.CTRL_K)

            # Line should be empty now
            # (Note: the killed text is in the kill ring)

    def test_get_screen_content(self):
        """Access the virtual terminal screen."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo line1; echo line2; echo line3")
            session.verify_text_appears("line3")

            # Get full screen content
            content = session.get_content()
            assert "line1" in content
            assert "line2" in content
            assert "line3" in content

            # Get screen as list of lines
            lines = session.get_screen()
            assert isinstance(lines, list)

    def test_wait_for_text_with_timeout(self):
        """Wait for text with custom timeout."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("sleep 0.5 && echo 'delayed output'")

            # This should succeed
            assert session.verify_text_appears("delayed output", timeout=3)

    def test_wait_for_text_raises_on_timeout(self):
        """wait_for_text raises TimeoutError if text doesn't appear."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo 'something else'")

            with pytest.raises(TimeoutError):
                session.wait_for_text("this will never appear", timeout=0.5)

    def test_custom_terminal_size(self):
        """Specify custom terminal dimensions."""
        with PtySession(["bash", "--norc"], width=80, height=24) as session:
            # The terminal is 80x24
            session.send_keys("stty size")
            # Output should show "24 80" (rows columns)
            assert session.verify_text_appears("24 80")

    def test_custom_environment(self):
        """Pass custom environment variables."""
        custom_env = {"MY_VAR": "custom_value", "PATH": "/usr/bin:/bin"}

        with PtySession(["bash", "--norc"], env=custom_env) as session:
            session.send_keys("echo $MY_VAR")
            assert session.verify_text_appears("custom_value")

    def test_custom_working_directory(self):
        """Start session in a specific directory."""
        with PtySession(["bash", "--norc"], cwd="/tmp") as session:
            session.send_keys("pwd")
            assert session.verify_text_appears("/tmp")


class TestPtySessionWithPython:
    """Test Python interpreter with PtySession."""

    def test_python_repl(self):
        """Interact with Python REPL."""
        with PtySession(["python3"]) as session:
            # Wait for the prompt
            assert session.verify_text_appears(">>>", timeout=3)

            # Run some Python code
            session.send_keys("2 + 2")
            assert session.verify_text_appears("4")

            # Run a print statement
            session.send_keys("print('PTYTEST_OUTPUT')")
            assert session.verify_text_appears("PTYTEST_OUTPUT")

            # Exit Python
            session.send_keys("exit()")


class TestPtySessionWithCat:
    """Test interactive cat with PtySession."""

    def test_cat_stdin(self):
        """Test interactive input with cat."""
        with PtySession(["cat"]) as session:
            # Type some text
            session.send_keys("Hello")
            # cat echoes input
            assert session.verify_text_appears("Hello")

            session.send_keys("World")
            assert session.verify_text_appears("World")

            # Send EOF to end cat
            session.send_raw(Keys.CTRL_D)


class TestPtySessionControlCharacters:
    """Test control character handling."""

    def test_ctrl_c_interrupt(self):
        """Test Ctrl-C to interrupt a process."""
        with PtySession(["bash", "--norc"]) as session:
            # Start a long-running command
            session.send_keys("sleep 100", literal=True)
            session.send_raw(Keys.ENTER)

            # Wait a moment then interrupt
            import time
            time.sleep(0.2)
            session.send_raw(Keys.CTRL_C)

            # Should get back to prompt
            assert session.verify_text_appears("$", timeout=2)

    def test_ctrl_l_clear_screen(self):
        """Test Ctrl-L to clear screen."""
        with PtySession(["bash", "--norc"]) as session:
            # Put some content on screen
            session.send_keys("echo 'line 1'; echo 'line 2'; echo 'line 3'")
            session.verify_text_appears("line 3")

            # Clear screen
            session.send_raw(Keys.CTRL_L)

            import time
            time.sleep(0.2)

            # Old content should be scrolled away or cleared


class TestPtySessionArrowKeys:
    """Test arrow key navigation."""

    @pytest.mark.skip(reason="Requires readline history setup")
    def test_arrow_key_history(self):
        """Test arrow keys for command history."""
        with PtySession(["bash", "--norc"]) as session:
            # Run some commands
            session.send_keys("echo first")
            session.send_keys("echo second")
            session.send_keys("echo third")

            # Press up arrow to go back in history
            session.send_raw(Keys.UP)
            session.send_raw(Keys.UP)

            # Should show "echo second" in the command line
            content = session.get_content()
            # History navigation depends on readline config
