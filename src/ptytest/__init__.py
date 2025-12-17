"""
ptytest - Real terminal testing framework.

A Python framework for testing interactive terminal applications by sending
real keystrokes and verifying actual terminal output. No mocks, no fakes -
just real process control via PTY.

Example:
    from ptytest import TmuxSession

    def test_my_keybinding():
        with TmuxSession() as session:
            session.send_prefix_key('h')  # Send Ctrl-b h
            assert session.get_pane_count() == 2
            assert "help" in session.get_pane_content()
"""

__version__ = "0.1.0"

from .session import TmuxSession
from .keys import Keys

__all__ = ["TmuxSession", "Keys", "__version__"]
