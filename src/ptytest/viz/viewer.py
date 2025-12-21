"""
Textual-based terminal viewer for ptytest sessions.

This module provides a pure-Python, in-terminal viewer that displays the
current state of a pyte screen in real-time. Multiple viewers can watch
the same session simultaneously.

Architecture:
- ScreenBroadcaster: Manages screen state and notifies subscribers
- TerminalViewer: Textual widget that displays pyte screen content
- Communication via thread-safe queue or shared state
"""

import threading
import time
from queue import Queue, Empty
from typing import List, Optional, Callable
from threading import Lock

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Static
    from textual.reactive import reactive
    from rich.text import Text
    from rich.console import RenderableType

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = None
    Static = None


class ScreenBroadcaster:
    """
    Broadcasts pyte screen updates to multiple viewers.

    This class maintains a reference to a PtySession's screen and allows
    multiple viewers to subscribe to updates. It's thread-safe and supports
    both polling and callback-based notification.

    Example:
        broadcaster = ScreenBroadcaster(pty_session)
        broadcaster.start()

        # Viewers can subscribe
        def on_update(lines):
            print(lines)
        broadcaster.subscribe(on_update)
    """

    def __init__(self, pty_session, update_interval: float = 0.1):
        """
        Initialize the screen broadcaster.

        Args:
            pty_session: PtySession instance to broadcast from
            update_interval: How often to check for updates (seconds)
        """
        if not TEXTUAL_AVAILABLE:
            raise ImportError(
                "Visualization dependencies not installed. "
                "Install with: uv pip install ptytest[viz]"
            )

        self.session = pty_session
        self.update_interval = update_interval
        self._subscribers: List[Callable] = []
        self._subscribers_lock = Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: List[str] = []

    def subscribe(self, callback: Callable[[List[str], int, int], None]):
        """
        Subscribe to screen updates.

        Args:
            callback: Function called with (lines, cursor_x, cursor_y) on updates
        """
        with self._subscribers_lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """
        Unsubscribe from screen updates.

        Args:
            callback: The callback to remove
        """
        with self._subscribers_lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def get_screen_state(self) -> tuple[List[str], int, int]:
        """
        Get current screen state (thread-safe).

        Returns:
            Tuple of (lines, cursor_x, cursor_y)
        """
        with self.session.screen_lock:
            lines = list(self.session.screen.display)
            cursor_x = self.session.screen.cursor.x
            cursor_y = self.session.screen.cursor.y
            return lines, cursor_x, cursor_y

    def start(self):
        """Start broadcasting screen updates in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._broadcast_loop, daemon=True, name="ptytest-viz-broadcaster"
        )
        self._thread.start()

    def _broadcast_loop(self):
        """Background thread that notifies subscribers of screen changes."""
        while self._running:
            try:
                lines, cursor_x, cursor_y = self.get_screen_state()

                # Only notify if content changed
                if lines != self._last_content:
                    self._last_content = lines.copy()

                    # Notify all subscribers
                    with self._subscribers_lock:
                        for callback in self._subscribers:
                            try:
                                callback(lines, cursor_x, cursor_y)
                            except Exception:
                                # Don't let one subscriber break others
                                pass

                time.sleep(self.update_interval)
            except Exception:
                # Session might be closed
                break

    def shutdown(self):
        """Stop broadcasting and clean up."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        # Clear subscribers
        with self._subscribers_lock:
            self._subscribers.clear()

    @property
    def is_running(self) -> bool:
        """Check if broadcaster is running."""
        return self._running


class TerminalDisplay(Static):
    """
    Textual widget that displays a pyte terminal screen.

    This widget renders the screen content with ANSI colors and cursor
    position. It's read-only (no keyboard input to the PTY).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cursor_x = 0
        self._cursor_y = 0

    def update_screen(self, lines: List[str], cursor_x: int, cursor_y: int):
        """
        Update the displayed screen content.

        Args:
            lines: List of screen lines
            cursor_x: Cursor column
            cursor_y: Cursor row
        """
        self._cursor_x = cursor_x
        self._cursor_y = cursor_y

        if not lines:
            self.update(Text("Waiting for terminal output...", style="dim"))
            return

        # Build Rich Text from screen lines
        output_lines: List[Text] = []
        for i, line in enumerate(lines):
            # Parse ANSI escape sequences
            text = Text.from_ansi(line)

            # Show cursor if on this line
            if i == self._cursor_y and 0 <= self._cursor_x < len(line):
                # Insert cursor style (reverse video)
                text.stylize("reverse", self._cursor_x, self._cursor_x + 1)

            output_lines.append(text)

        # Combine all lines
        result = Text()
        for i, text_line in enumerate(output_lines):
            result.append(text_line)
            if i < len(output_lines) - 1:
                result.append("\n")

        # Update the Static widget's content
        self.update(result)


class TerminalViewer(App):
    """
    Textual app for viewing a ptytest session in real-time.

    This app displays the current state of a PtySession's screen with
    colors, cursor position, and automatic updates. It's read-only - no
    keyboard input is sent to the PTY.

    Example:
        broadcaster = ScreenBroadcaster(pty_session)
        broadcaster.start()

        viewer = TerminalViewer(broadcaster)
        viewer.run()
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
    }

    #terminal {
        padding: 1 2;
        height: 1fr;
    }

    #footer {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, broadcaster: ScreenBroadcaster, session_name: str = "ptytest"):
        """
        Initialize the viewer.

        Args:
            broadcaster: ScreenBroadcaster instance to watch
            session_name: Name to display in header
        """
        super().__init__()
        self.broadcaster = broadcaster
        self.session_name = session_name
        self._terminal_display: Optional[TerminalDisplay] = None

    def compose(self) -> ComposeResult:
        """Build the UI."""
        yield Static(
            f"[bold]ptytest viewer[/bold] - {self.session_name}",
            id="header",
        )
        yield TerminalDisplay(id="terminal")
        yield Static(
            "[dim]Press [bold]q[/bold] to quit | [bold]r[/bold] to refresh | Read-only mode[/dim]",
            id="footer",
        )

    def on_mount(self) -> None:
        """Called when app starts."""
        self._terminal_display = self.query_one("#terminal", TerminalDisplay)

        # Subscribe to broadcaster (called from background thread)
        self.broadcaster.subscribe(self._on_screen_update_from_thread)

        # Initial update (we're in main thread, call directly)
        lines, cursor_x, cursor_y = self.broadcaster.get_screen_state()
        self._terminal_display.update_screen(lines, cursor_x, cursor_y)

    def _on_screen_update_from_thread(self, lines: List[str], cursor_x: int, cursor_y: int):
        """Called from broadcaster background thread when screen content changes."""
        if self._terminal_display:
            # Use call_from_thread for thread-safe updates from background thread
            self.call_from_thread(self._terminal_display.update_screen, lines, cursor_x, cursor_y)

    def action_refresh(self) -> None:
        """Force refresh the screen."""
        lines, cursor_x, cursor_y = self.broadcaster.get_screen_state()
        # We're in main thread, call directly
        if self._terminal_display:
            self._terminal_display.update_screen(lines, cursor_x, cursor_y)

    def action_quit(self) -> None:
        """Quit the viewer."""
        self.exit()

    def on_unmount(self) -> None:
        """Called when app is closing."""
        # Unsubscribe from broadcaster
        if hasattr(self, "_on_screen_update_from_thread"):
            self.broadcaster.unsubscribe(self._on_screen_update_from_thread)


def start_viz_broadcaster(session) -> ScreenBroadcaster:
    """
    Start a screen broadcaster for a PtySession.

    Args:
        session: PtySession instance

    Returns:
        Running ScreenBroadcaster instance

    Raises:
        ImportError: If viz dependencies not installed
    """
    broadcaster = ScreenBroadcaster(session)
    broadcaster.start()
    return broadcaster
