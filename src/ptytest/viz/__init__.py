"""
Pure-Python terminal visualization for ptytest.

This module provides real-time terminal visualization of PTY sessions using
Textual (TUI framework) and pyte (virtual terminal). Runs entirely in your
terminal - no browser required!

Example:
    from ptytest import PtySession

    # Enable visualization
    with PtySession(['bash'], enable_viz=True) as session:
        session.send_keys('echo hello')
        # Viewers can attach via: ptytest viz
"""

from .viewer import TerminalViewer, ScreenBroadcaster, start_viz_broadcaster

__all__ = ["TerminalViewer", "ScreenBroadcaster", "start_viz_broadcaster"]
