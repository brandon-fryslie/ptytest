"""Tests for pytest plugin fixtures."""

import pytest

from ptytest import PtySession, TmuxSession


@pytest.mark.direct_pty
class TestPtySessionFixtures:
    """Test pty_session fixtures."""

    def test_pty_session_fixture(self, pty_session):
        """Test that pty_session fixture works."""
        assert isinstance(pty_session, PtySession)
        assert pty_session.process.isalive()

        pty_session.send_keys("echo FIXTURE_TEST")
        assert pty_session.verify_text_appears("FIXTURE_TEST")

    def test_pty_session_factory_fixture(self, pty_session_factory):
        """Test that pty_session_factory fixture works."""
        # Create bash session
        bash = pty_session_factory(["bash", "--norc", "--noprofile"])
        assert isinstance(bash, PtySession)
        assert bash.process.isalive()

        # Create cat session
        cat = pty_session_factory(["cat"])
        assert isinstance(cat, PtySession)
        assert cat.process.isalive()

        # Both should work independently
        bash.send_keys("echo FROM_BASH")
        assert bash.verify_text_appears("FROM_BASH")

        cat.send_keys("from cat", literal=True)
        cat.send_raw("\r")
        assert cat.verify_text_appears("from cat")


class TestTmuxSessionFixtures:
    """Test that tmux fixtures still work (backward compatibility)."""

    def test_tmux_session_fixture(self, tmux_session):
        """Test that tmux_session fixture still works."""
        assert isinstance(tmux_session, TmuxSession)
        assert tmux_session._session_exists()

        tmux_session.send_keys("echo TMUX_FIXTURE")
        assert tmux_session.verify_text_appears("TMUX_FIXTURE")

    def test_tmux_session_factory_fixture(self, tmux_session_factory):
        """Test that tmux_session_factory fixture still works."""
        session1 = tmux_session_factory()
        session2 = tmux_session_factory()

        assert isinstance(session1, TmuxSession)
        assert isinstance(session2, TmuxSession)
        assert session1.session_name != session2.session_name
