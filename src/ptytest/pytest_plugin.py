"""
Pytest plugin for ptytest.

Provides fixtures and markers for testing interactive terminal applications.

Usage:
    Install ptytest and fixtures are automatically available:

    def test_my_keybinding(tmux_session):
        tmux_session.send_prefix_key('h')
        assert tmux_session.get_pane_count() == 2

    def test_my_cli(pty_session):
        pty_session.send_keys("echo hello")
        assert pty_session.verify_text_appears("hello")
"""

import os

import pytest

from .session import PtySession, TmuxSession


@pytest.fixture
def tmux_session():
    """
    Provide a clean tmux session for testing.

    This fixture:
    - Creates a unique tmux session for each test
    - Uses the user's ~/.tmux.conf configuration
    - Automatically cleans up after the test
    - Ensures test isolation (no interference between tests)

    Example:
        def test_help_pane(tmux_session):
            tmux_session.send_prefix_key('h')
            assert tmux_session.get_pane_count() == 2
    """
    session = TmuxSession(
        use_config=True,
        width=120,
        height=40,
        timeout=5
    )

    yield session
    session.cleanup()


@pytest.fixture
def tmux_session_minimal():
    """
    Provide a tmux session with minimal config (no ~/.tmux.conf).

    Useful for testing tmux basics without user customization.
    """
    session = TmuxSession(
        use_config=False,
        width=120,
        height=40,
        timeout=5
    )

    yield session
    session.cleanup()


@pytest.fixture
def tmux_session_factory():
    """
    Factory fixture for creating multiple tmux sessions.

    Useful when a test needs multiple independent sessions.

    Example:
        def test_multiple_sessions(tmux_session_factory):
            session1 = tmux_session_factory()
            session2 = tmux_session_factory()
            # ... test with both sessions
    """
    sessions = []

    def _create_session(**kwargs):
        session = TmuxSession(**kwargs)
        sessions.append(session)
        return session

    yield _create_session

    for session in sessions:
        session.cleanup()


@pytest.fixture
def pty_session():
    """
    Provide a PtySession with bash for direct process testing.

    This fixture:
    - Creates a PtySession running bash (no tmux)
    - Uses --norc and --noprofile for clean environment
    - Automatically cleans up after the test
    - Ensures test isolation

    Example:
        def test_my_cli(pty_session):
            pty_session.send_keys("echo hello")
            assert pty_session.verify_text_appears("hello")
    """
    session = PtySession(
        command=["bash", "--norc", "--noprofile"],
        width=120,
        height=40,
        timeout=5
    )

    yield session
    session.cleanup()


@pytest.fixture
def pty_session_factory():
    """
    Factory fixture for creating multiple PtySession instances.

    Useful when a test needs multiple independent processes or
    wants to test different CLI applications.

    Example:
        def test_multiple_apps(pty_session_factory):
            bash = pty_session_factory(["bash", "--norc"])
            python = pty_session_factory(["python3", "-u"])
            # ... test with both sessions

        def test_custom_app(pty_session_factory):
            session = pty_session_factory(["fzf"], width=80, height=24)
            # ... test fzf
    """
    sessions = []

    def _create_session(command, **kwargs):
        session = PtySession(command=command, **kwargs)
        sessions.append(session)
        return session

    yield _create_session

    for session in sessions:
        session.cleanup()


def pytest_configure(config):
    """Configure pytest with ptytest markers."""
    config.addinivalue_line(
        "markers",
        "keybinding: marks tests that test keybindings"
    )
    config.addinivalue_line(
        "markers",
        "zle: marks tests for ZLE widgets (zsh line editor)"
    )
    config.addinivalue_line(
        "markers",
        "zaw: marks tests for zaw (zsh anything.el-like widget)"
    )
    config.addinivalue_line(
        "markers",
        "e2e: marks end-to-end workflow tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "interactive: marks tests that require interactive terminal"
    )
    config.addinivalue_line(
        "markers",
        "direct_pty: marks tests using PtySession (no tmux)"
    )
