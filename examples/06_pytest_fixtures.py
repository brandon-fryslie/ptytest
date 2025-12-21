"""
Pytest Fixtures - Using ptytest's built-in pytest fixtures and markers.

ptytest provides pytest fixtures for common session types, plus markers
for organizing and filtering tests.

Run with: uv run pytest examples/06_pytest_fixtures.py -v
"""

import shutil

import pytest

from ptytest import Keys


# ============================================================================
# Using Built-in Fixtures
# ============================================================================


class TestBuiltinFixtures:
    """Using ptytest's built-in pytest fixtures."""

    def test_pty_session_fixture(self, pty_session):
        """
        The pty_session fixture provides a PtySession with bash.

        This is auto-registered by ptytest's pytest plugin.
        """
        # pty_session is already running bash
        pty_session.send_keys("echo 'using pty_session fixture'")
        assert pty_session.verify_text_appears("using pty_session fixture")

    def test_pty_session_factory(self, pty_session_factory):
        """
        The pty_session_factory fixture creates custom PtySession instances.

        Use this when you need non-default settings.
        """
        # Create a session with custom command
        with pty_session_factory(["python3", "-c", "print('hello')"]) as session:
            assert session.verify_text_appears("hello")

        # Create another with custom size
        with pty_session_factory(["bash", "--norc"], width=80, height=24) as session:
            session.send_keys("stty size")
            assert session.verify_text_appears("24 80")

    @pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux not installed")
    def test_tmux_session_fixture(self, tmux_session):
        """
        The tmux_session fixture provides a TmuxSession with user's config.

        Uses ~/.tmux.conf if present.
        """
        tmux_session.send_keys("echo 'using tmux_session fixture'")
        assert tmux_session.verify_text_appears("using tmux_session fixture")

    @pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux not installed")
    def test_tmux_session_minimal(self, tmux_session_minimal):
        """
        The tmux_session_minimal fixture ignores user's tmux config.

        Useful for tests that depend on default tmux behavior.
        """
        tmux_session_minimal.send_keys("echo 'minimal tmux'")
        assert tmux_session_minimal.verify_text_appears("minimal tmux")

    @pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux not installed")
    def test_tmux_session_factory(self, tmux_session_factory):
        """
        The tmux_session_factory fixture creates custom TmuxSession instances.
        """
        # Create session without config
        with tmux_session_factory(use_config=False) as session:
            session.send_keys("echo 'custom tmux'")
            assert session.verify_text_appears("custom tmux")


# ============================================================================
# Using Markers
# ============================================================================


@pytest.mark.keybinding
class TestKeybindingMarker:
    """Tests marked with @pytest.mark.keybinding."""

    def test_ctrl_c(self, pty_session):
        """Test Ctrl-C interrupt."""
        pty_session.send_keys("sleep 100", literal=True)
        pty_session.send_raw(Keys.ENTER)

        import time
        time.sleep(0.1)

        pty_session.send_raw(Keys.CTRL_C)
        # Should get back to prompt


@pytest.mark.direct_pty
class TestDirectPtyMarker:
    """Tests marked with @pytest.mark.direct_pty (PtySession tests)."""

    def test_pty_basic(self, pty_session):
        """Basic PtySession test."""
        pty_session.send_keys("echo 'direct pty'")
        assert pty_session.verify_text_appears("direct pty")


@pytest.mark.slow
class TestSlowMarker:
    """Tests marked with @pytest.mark.slow."""

    def test_slow_operation(self, pty_session):
        """A test that takes longer."""
        pty_session.send_keys("sleep 1 && echo 'done'")
        assert pty_session.verify_text_appears("done", timeout=3)


@pytest.mark.e2e
class TestE2EMarker:
    """End-to-end tests marked with @pytest.mark.e2e."""

    def test_complete_workflow(self, pty_session):
        """Test a complete workflow."""
        # Create a file
        pty_session.send_keys("echo 'content' > /tmp/test_e2e.txt")
        pty_session.verify_text_appears("$")

        # Read it back
        pty_session.send_keys("cat /tmp/test_e2e.txt")
        assert pty_session.verify_text_appears("content")

        # Clean up
        pty_session.send_keys("rm /tmp/test_e2e.txt")


# ============================================================================
# Running Tests with Markers
# ============================================================================


class TestMarkerUsage:
    """
    How to run tests with markers.

    Run specific markers:
        uv run pytest -m keybinding -v
        uv run pytest -m direct_pty -v
        uv run pytest -m "not slow" -v
        uv run pytest -m "keybinding and direct_pty" -v

    Available markers in ptytest:
        - keybinding: Tests for keybinding functionality
        - zle: Tests for ZLE (Zsh Line Editor) widgets
        - zaw: Tests for zaw (Zsh Anything.el Widget)
        - e2e: End-to-end tests
        - slow: Slow-running tests
        - interactive: Tests requiring interactive input
        - direct_pty: Tests using PtySession directly
    """

    def test_show_markers(self):
        """This test documents available markers."""
        pass


# ============================================================================
# Creating Custom Fixtures
# ============================================================================


@pytest.fixture
def python_session(pty_session_factory):
    """Custom fixture for Python REPL testing."""
    with pty_session_factory(["python3"]) as session:
        session.verify_text_appears(">>>")
        yield session


class TestCustomFixtures:
    """Using custom fixtures built on ptytest."""

    def test_python_repl(self, python_session):
        """Test using custom Python session fixture."""
        python_session.send_keys("1 + 1")
        assert python_session.verify_text_appears("2")


@pytest.fixture
def bash_norc(pty_session_factory):
    """Bash without any config files."""
    with pty_session_factory(["bash", "--norc", "--noprofile"]) as session:
        session.verify_text_appears("$")
        yield session


class TestBashNorc:
    """Tests using clean bash session."""

    def test_clean_env(self, bash_norc):
        """Test with clean bash environment."""
        bash_norc.send_keys("echo $HOME")
        assert bash_norc.verify_text_appears("/")


# ============================================================================
# Fixture Scope
# ============================================================================


class TestSharedSessionConcept:
    """
    Demonstrating class-scoped session pattern.

    NOTE: For class-scoped fixtures, you would typically define them
    directly with PtySession rather than using the function-scoped
    pty_session_factory. Here we just demonstrate the concept.

    Example of a proper class-scoped fixture:

        @pytest.fixture(scope="class")
        def shared_session():
            session = PtySession(["bash", "--norc"])
            session.send_keys("export SHARED_VAR='shared'")
            session.verify_text_appears("$")
            yield session
            session.cleanup()
    """

    def test_shared_session_concept_first(self, pty_session):
        """First test shows shared state concept."""
        pty_session.send_keys("export SHARED_VAR='shared'")
        pty_session.verify_text_appears("$")
        pty_session.send_keys("echo $SHARED_VAR")
        assert pty_session.verify_text_appears("shared")

    def test_shared_session_concept_second(self, pty_session):
        """Second test shows that function-scoped fixtures are isolated."""
        # This is a NEW session (function-scoped), so SHARED_VAR doesn't exist
        pty_session.send_keys("echo ${SHARED_VAR:-not_set}")
        assert pty_session.verify_text_appears("not_set")


# ============================================================================
# Parametrized Tests
# ============================================================================


class TestParametrized:
    """Using pytest.mark.parametrize with ptytest."""

    @pytest.mark.parametrize("command,expected", [
        ("echo hello", "hello"),
        ("echo world", "world"),
        ("echo 123", "123"),
    ])
    def test_echo_commands(self, pty_session, command, expected):
        """Run multiple commands with parametrize."""
        pty_session.send_keys(command)
        assert pty_session.verify_text_appears(expected)

    @pytest.mark.parametrize("key,description", [
        (Keys.CTRL_A, "beginning of line"),
        (Keys.CTRL_E, "end of line"),
        (Keys.CTRL_U, "kill line"),
    ])
    def test_control_keys(self, pty_session, key, description):
        """Test various control keys."""
        pty_session.send_keys("test text", literal=True)
        pty_session.send_raw(key)
        # Key was sent successfully


# ============================================================================
# Skip and XFail
# ============================================================================


class TestConditionalSkips:
    """Using skip and xfail with ptytest."""

    @pytest.mark.skipif(
        shutil.which("fzf") is None,
        reason="fzf not installed"
    )
    def test_fzf_available(self, pty_session_factory):
        """Only runs if fzf is installed."""
        with pty_session_factory(["fzf", "--version"]) as session:
            # fzf --version prints version info and exits
            # Match either "fzf" or version number pattern
            assert session.verify_text_appears(".", timeout=2)  # Match any output

    @pytest.mark.xfail(reason="Known timing issue")
    def test_flaky(self, pty_session):
        """Test that sometimes fails due to timing."""
        pty_session.send_keys("echo flaky")
        # This might fail occasionally
        assert pty_session.verify_text_appears("flaky", timeout=0.1)
