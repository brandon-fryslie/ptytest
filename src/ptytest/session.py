"""
TmuxSession: Real tmux session management for automated testing.

This module provides the TmuxSession class which manages real tmux processes
for testing interactive terminal applications. Tests cannot be gamed with
mocks - they verify actual tmux/terminal behavior.

Key Design Principles:
1. Use real tmux subprocess (via pexpect), NOT mocks
2. Send actual keystroke bytes (Ctrl-b h = '\\x02h')
3. Verify observable outcomes (pane count, content, status bar)
4. Enforce cleanup (no orphaned sessions)
5. Provide helpful error messages when tests fail
"""

import os
import time
import subprocess
import pexpect
from typing import Optional, List

from .keys import Keys


class TmuxSession:
    """
    Manages a real tmux session for testing.

    This class spawns an actual tmux process and allows sending
    real keystrokes, verifying pane states, and capturing output.

    Example:
        with TmuxSession() as session:
            # Send Ctrl-b h
            session.send_prefix_key('h')

            # Verify help pane appeared
            assert session.get_pane_count() == 2

            # Verify content
            content = session.get_pane_content()
            assert "PANES" in content

    Attributes:
        session_name: Unique name for this tmux session
        config_file: Path to tmux config file
        width: Terminal width in characters
        height: Terminal height in characters
        timeout: Default timeout for operations
    """

    PREFIX_KEY = Keys.CTRL_B  # Ctrl-b as default tmux prefix

    def __init__(
        self,
        session_name: Optional[str] = None,
        config_file: Optional[str] = None,
        width: int = 120,
        height: int = 40,
        timeout: int = 5,
        shell: Optional[str] = None,
    ):
        """
        Create and attach to a real tmux session.

        Args:
            session_name: Unique session name (auto-generated if None)
            config_file: Path to tmux config (defaults to ~/.tmux.conf)
            width: Terminal width in characters
            height: Terminal height in characters
            timeout: Default timeout for operations in seconds
            shell: Shell to use (defaults to user's default shell)
        """
        self.session_name = session_name or f"ptytest-{os.getpid()}-{int(time.time())}"
        self.config_file = config_file or os.path.expanduser("~/.tmux.conf")
        self.width = width
        self.height = height
        self.timeout = timeout
        self.shell = shell
        self.process: Optional[pexpect.spawn] = None
        self._is_cleaned_up = False

        # Ensure no existing session with this name
        self._kill_existing_session()

        # Start tmux session
        self._start_session()

    def _kill_existing_session(self):
        """Kill any existing session with our name (cleanup from failed tests)."""
        subprocess.run(
            ["tmux", "kill-session", "-t", self.session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _start_session(self):
        """
        Spawn a real tmux session.

        Creates a DETACHED session first, then attaches to it with pexpect.
        This ensures the shell inside tmux initializes properly and can accept
        commands via send-keys, while still allowing raw keystroke injection
        via pexpect for testing keybindings.
        """
        # Step 1: Create a DETACHED tmux session
        cmd = [
            "tmux",
            "-f", self.config_file,
            "new-session",
            "-d",  # DETACHED
            "-s", self.session_name,
            "-x", str(self.width),
            "-y", str(self.height),
        ]

        if self.shell:
            cmd.extend([self.shell])

        subprocess.run(cmd, check=True)

        # Wait for session to be fully created
        time.sleep(0.3)

        # Verify session exists
        if not self._session_exists():
            raise RuntimeError(f"Failed to create tmux session: {self.session_name}")

        # Wait for shell to be ready
        self._wait_for_shell_ready()

        # Step 2: Attach to the session with pexpect
        self.process = pexpect.spawn(
            "tmux",
            ["-f", self.config_file, "attach", "-t", self.session_name],
            encoding='utf-8',
            timeout=self.timeout,
            dimensions=(self.height, self.width)
        )

        # Wait for attach to complete
        time.sleep(0.2)

    def _wait_for_shell_ready(self, max_attempts: int = 10):
        """
        Wait for the shell inside tmux to be ready to accept commands.
        """
        marker = f"__PTYTEST_READY_{os.getpid()}__"

        for attempt in range(max_attempts):
            subprocess.run(
                ["tmux", "send-keys", "-t", self.session_name, f"echo {marker}", "C-m"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(0.15)

            content = self.get_pane_content(include_history=False)
            lines = content.split('\n')

            for line in lines:
                if marker in line and 'echo' not in line:
                    subprocess.run(
                        ["tmux", "send-keys", "-t", self.session_name, "clear", "C-m"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    time.sleep(0.1)
                    return

            time.sleep(0.1)

    def _session_exists(self) -> bool:
        """Check if our tmux session exists."""
        result = subprocess.run(
            ["tmux", "has-session", "-t", self.session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0

    def send_prefix_key(self, key: str, delay: float = 0.15):
        """
        Send tmux prefix + key (default: Ctrl-b + key).

        This sends ACTUAL bytes to the tmux process, triggering
        the real keybinding handlers. Cannot be faked with mocks.

        Args:
            key: The key to press after prefix (e.g., 'h' for Ctrl-b h)
            delay: Delay after keystroke for tmux to process (seconds)

        Example:
            session.send_prefix_key('h')  # Sends Ctrl-b h
            session.send_prefix_key('o')  # Sends Ctrl-b o
        """
        if not self.process:
            raise RuntimeError("Session not started")

        self.process.send(self.PREFIX_KEY)
        time.sleep(0.05)
        self.process.send(key)
        time.sleep(delay)

    def send_raw(self, sequence: str, delay: float = 0.15):
        """
        Send raw bytes/escape sequences to the shell inside tmux.

        This sends ACTUAL bytes directly to the pexpect process, which
        reaches the shell (zsh/bash) inside tmux. Use this for testing
        ZLE widgets and shell keybindings.

        Args:
            sequence: Raw string to send (can include escape sequences)
            delay: Delay after sending for processing (seconds)

        Example:
            # Send Option+Shift+D (ESC D) to trigger zaw-rad-dev
            session.send_raw('\\x1bD')

            # Send Ctrl-R for reverse history search
            session.send_raw('\\x12')

            # Send Ctrl-X Ctrl-E for edit-command-line
            session.send_raw('\\x18\\x05')
        """
        if not self.process:
            raise RuntimeError("Session not started")

        self.process.send(sequence)
        time.sleep(delay)

    def send_keys(self, keys: str, delay: float = 0.15, literal: bool = False):
        """
        Send keys to the currently active pane using tmux send-keys.

        This is more reliable than using pexpect for complex commands.

        Args:
            keys: Keys to send
            delay: Delay after sending (seconds)
            literal: If True, send keys without executing (no Enter key).
                    If False (default), execute the command by adding Enter.
        """
        cmd = ["tmux", "send-keys", "-t", self.session_name]

        if literal:
            cmd.extend(["-l", keys])
        else:
            cmd.extend([keys, "C-m"])

        subprocess.run(cmd, check=True)
        time.sleep(delay)

    def split_window(self, direction: str = "-h", target_pane: Optional[int] = None):
        """
        Split a pane in the session.

        Args:
            direction: "-h" for horizontal (left/right), "-v" for vertical (top/bottom)
            target_pane: Pane number to split (None = current pane)
        """
        target = f"{self.session_name}:{target_pane}" if target_pane else self.session_name

        result = subprocess.run(
            ["tmux", "split-window", direction, "-t", target],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to split window: {result.stderr}")

        time.sleep(0.2)

    def get_pane_count(self) -> int:
        """
        Get the number of panes in the session.

        Returns:
            Number of panes currently in the session
        """
        result = subprocess.run(
            ["tmux", "list-panes", "-t", self.session_name, "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=True
        )
        panes = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return len(panes)

    def get_pane_ids(self) -> List[str]:
        """Get list of pane IDs in the session."""
        result = subprocess.run(
            ["tmux", "list-panes", "-t", self.session_name, "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []

    def get_pane_content(self, pane_id: Optional[str] = None, include_history: bool = True) -> str:
        """
        Capture the visible content of a pane.

        Args:
            pane_id: Specific pane ID (e.g., "%1"), or None for current pane
            include_history: If True, capture scrollback history (last 1000 lines).

        Returns:
            Text content of the pane
        """
        target = pane_id if pane_id else self.session_name

        if include_history:
            cmd = ["tmux", "capture-pane", "-t", target, "-p", "-S", "-1000"]
        else:
            cmd = ["tmux", "capture-pane", "-t", target, "-p"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def get_pane_height(self, pane_id: Optional[str] = None) -> int:
        """Get the height of a pane in lines."""
        target = pane_id if pane_id else self.session_name

        result = subprocess.run(
            ["tmux", "display-message", "-t", target, "-p", "#{pane_height}"],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())

    def get_pane_width(self, pane_id: Optional[str] = None) -> int:
        """Get the width of a pane in columns."""
        target = pane_id if pane_id else self.session_name

        result = subprocess.run(
            ["tmux", "display-message", "-t", target, "-p", "#{pane_width}"],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())

    def get_status_bar(self) -> str:
        """
        Capture the status bar content.

        Returns:
            Status bar text
        """
        result = subprocess.run(
            ["tmux", "display-message", "-t", self.session_name, "-p",
             "#{status-left}#{status-right}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def verify_text_appears(self, text: str, timeout: float = 2.0, pane_id: Optional[str] = None) -> bool:
        """
        Wait for text to appear in a pane.

        Args:
            text: Text to search for
            timeout: How long to wait (seconds)
            pane_id: Specific pane to check, or None for current pane

        Returns:
            True if text appears within timeout, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            content = self.get_pane_content(pane_id)
            if text in content:
                return True
            time.sleep(0.1)
        return False

    def wait_for_text(self, text: str, timeout: float = 2.0, pane_id: Optional[str] = None):
        """
        Wait for text to appear, raising AssertionError if not found.

        Args:
            text: Text to search for
            timeout: How long to wait (seconds)
            pane_id: Specific pane to check

        Raises:
            AssertionError: If text doesn't appear within timeout
        """
        if not self.verify_text_appears(text, timeout, pane_id):
            content = self.get_pane_content(pane_id)
            raise AssertionError(
                f"Text '{text}' did not appear within {timeout}s.\n"
                f"Pane content:\n{content}"
            )

    def get_global_option(self, option: str) -> str:
        """Get a tmux global option value."""
        result = subprocess.run(
            ["tmux", "show", "-gv", option],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def set_global_option(self, option: str, value: str):
        """Set a tmux global option."""
        subprocess.run(
            ["tmux", "set", "-g", option, value],
            check=True
        )

    def cleanup(self):
        """
        Clean up the tmux session.

        MUST be called to prevent orphaned sessions.
        Use try/finally or context manager to ensure this is called.
        """
        if self._is_cleaned_up:
            return

        self._is_cleaned_up = True

        if self.process:
            try:
                self.process.close(force=True)
            except:
                pass

        subprocess.run(
            ["tmux", "kill-session", "-t", self.session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.cleanup()
        return False

    def __del__(self):
        """Destructor - ensure cleanup on garbage collection."""
        self.cleanup()
