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

    from ptytest import PtySession

    def test_my_cli():
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo hello")
            assert session.verify_text_appears("hello")
"""

__version__ = "0.1.0"

from .keys import (
    FzfKeys,
    HtopKeys,
    Keys,
    LazygitKeys,
    LessKeys,
    MacKeys,
    NcduKeys,
    ReadlineKeys,
    TmuxKeys,
    VimKeys,
)
from .neovim import NeovimSession
from .session import BaseSession, PtySession, TmuxSession

__all__ = [
    # Session classes
    "BaseSession",
    "TmuxSession",
    "PtySession",
    "NeovimSession",
    # Key classes - Base
    "Keys",
    "MacKeys",
    "ReadlineKeys",
    # Key classes - Applications
    "FzfKeys",
    "VimKeys",
    "TmuxKeys",
    "LazygitKeys",
    "HtopKeys",
    "LessKeys",
    "NcduKeys",
    # Version
    "__version__",
]
