"""
Session classes for managing interactive CLI testing.

This module provides:
- BaseSession: Abstract base class for all session types
- TmuxSession: Real tmux session management for automated testing
- PtySession: Direct PTY process management for testing any CLI

Key Design Principles:
1. Use real processes (via pexpect), NOT mocks
2. Send actual keystroke bytes
3. Verify observable outcomes
4. Enforce cleanup (no orphaned processes)
5. Provide helpful error messages when tests fail
"""

import os
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import pexpect
import pyte
from ptydriver import PtyProcess as PtyProcessDriver


class BaseSession(ABC):
    """
    Abstract base class for terminal session management.

    All session types (TmuxSession, PtySession, etc.) inherit from this
    class and implement the core methods for sending keys and reading content.

    The session can be used as a context manager for automatic cleanup:
        with SomeSession(...) as session:
            session.send_keys("test")
    """

    def __init__(self, timeout: int = 5):
        """
        Initialize base session.

        Args:
            timeout: Default timeout in seconds for operations
        """
        self.timeout = timeout
        self._is_cleaned_up = False

    @abstractmethod
    def send_keys(self, keys: str, delay: float = 0.15, literal: bool = False):
        """
        Send keys to the session.

        Args:
            keys: Keys to send
            delay: Delay after sending for processing
            literal: If True, send keys as-is without Enter
        """
        pass

    @abstractmethod
    def send_raw(self, sequence: str, delay: float = 0.15):
        """
        Send raw byte sequences or escape codes.

        Args:
            sequence: Raw string to send (can include escape sequences)
            delay: Delay after sending
        """
        pass

    @abstractmethod
    def get_content(self, include_history: bool = True) -> str:
        """
        Get visible terminal content.

        Args:
            include_history: Whether to include scrollback history

        Returns:
            Text content of the terminal
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up session resources. Must be called to prevent leaks."""
        pass

    def verify_text_appears(
        self,
        text: str,
        timeout: Optional[float] = None,
        include_history: bool = True,
    ) -> bool:
        """
        Wait for text to appear in terminal content.

        Args:
            text: Text to wait for
            timeout: Max seconds to wait (None = use default)
            include_history: Whether to search scrollback history

        Returns:
            True if text appears within timeout, False otherwise
        """
        timeout = timeout if timeout is not None else self.timeout
        start = time.time()

        while time.time() - start < timeout:
            content = self.get_content(include_history=include_history)
            if text in content:
                return True
            time.sleep(0.1)

        return False

    def wait_for_text(
        self,
        text: str,
        timeout: Optional[float] = None,
        include_history: bool = True,
    ):
        """
        Wait for text to appear, raising TimeoutError if it doesn't.

        Args:
            text: Text to wait for
            timeout: Max seconds to wait (None = use default)
            include_history: Whether to search scrollback history

        Raises:
            TimeoutError: If text doesn't appear within timeout
        """
        if not self.verify_text_appears(text, timeout, include_history):
            content = self.get_content(include_history=include_history)
            raise TimeoutError(
                f"Text '{text}' did not appear within {timeout}s.\n"
                f"Current content:\n{content}"
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.cleanup()
        return False


class TmuxSession(BaseSession):
    """
    Manages a real tmux session for testing tmux keybindings and ZLE widgets.

    This class creates a detached tmux session, attaches to it via pexpect,
    and provides methods to send keys and read pane content.

    Example:
        with TmuxSession() as session:
            session.send_prefix_key('h')  # Send Ctrl-b h
            assert session.get_pane_count() == 2

    Attributes:
        session_name: Unique tmux session name
        width: Terminal width in characters
        height: Terminal height in characters
        timeout: Default timeout for operations
    """

    def __init__(
        self,
        session_name: Optional[str] = None,
        width: int = 120,
        height: int = 40,
        timeout: int = 5,
        use_config: bool = True,
        shell: str = "zsh",
    ):
        """
        Create a new tmux session for testing.

        Args:
            session_name: Unique session name (auto-generated if None)
            width: Terminal width in characters
            height: Terminal height in characters
            timeout: Default timeout for operations in seconds
            use_config: Whether to load user's ~/.tmux.conf
            shell: Shell to use (default: zsh)
        """
        super().__init__(timeout=timeout)

        # Generate unique session name if not provided
        if session_name is None:
            import uuid

            session_name = f"ptytest-{uuid.uuid4().hex[:8]}"

        self.session_name = session_name
        self.width = width
        self.height = height
        self.use_config = use_config
        self.shell = shell

        # Create detached session
        cmd = ["tmux"]
        if not use_config:
            cmd.append("-f/dev/null")  # Don't load config

        cmd.extend(
            [
                "new-session",
                "-d",  # Detached
                "-s",
                session_name,  # Session name
                "-x",
                str(width),  # Width
                "-y",
                str(height),  # Height
                shell,
            ]
        )

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create tmux session: {e.stderr}") from e

        # Attach to session via pexpect
        attach_cmd = f"tmux attach-session -t {session_name}"
        self.process = pexpect.spawn(
            "/bin/bash", ["-c", attach_cmd], dimensions=(height, width), timeout=timeout
        )

        # Wait for shell to be ready
        time.sleep(0.5)

    def send_prefix_key(self, key: str, delay: float = 0.15):
        """
        Send tmux prefix (Ctrl-b) + key combination.

        Example:
            session.send_prefix_key('h')  # Sends Ctrl-b h

        Args:
            key: Key to send after prefix
            delay: Delay after sending for processing
        """
        # Send Ctrl-b (tmux default prefix)
        self.process.send("\x02")  # Ctrl-b
        time.sleep(0.05)  # Brief pause between prefix and key
        self.process.send(key)
        time.sleep(delay)

    def send_raw(self, sequence: str, delay: float = 0.15):
        """
        Send raw byte sequences or escape codes to tmux.

        Args:
            sequence: Raw string to send (can include escape sequences)
            delay: Delay after sending for processing
        """
        self.process.send(sequence)
        time.sleep(delay)

    def send_keys(self, keys: str, delay: float = 0.15, literal: bool = False):
        """
        Send keys to the tmux session.

        Args:
            keys: Keys to send
            delay: Delay after sending (seconds)
            literal: If True, send keys as-is (no Enter).
                    If False (default), append Enter key.
        """
        self.process.send(keys)
        if not literal:
            self.process.send("\r")
        time.sleep(delay)

    def get_pane_content(self, pane_id: Optional[str] = None) -> str:
        """
        Get the visible content of a pane using tmux capture-pane.

        Args:
            pane_id: Pane identifier (None = current pane)

        Returns:
            Text content of the pane
        """
        cmd = ["tmux", "capture-pane", "-p", "-t", self.session_name]
        if pane_id:
            cmd.extend(["-t", pane_id])

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout

    def get_content(self, include_history: bool = True) -> str:
        """
        Get visible terminal content.

        Args:
            include_history: If True, include scrollback history

        Returns:
            Text content of the current pane
        """
        cmd = ["tmux", "capture-pane", "-p", "-t", self.session_name]
        if include_history:
            cmd.append("-S")
            cmd.append("-")  # Start from history beginning

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout

    def get_pane_count(self) -> int:
        """
        Get the number of panes in the current window.

        Returns:
            Number of panes
        """
        cmd = ["tmux", "list-panes", "-t", self.session_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    def get_pane_ids(self) -> List[str]:
        """
        Get list of pane IDs in the current window.

        Returns:
            List of pane IDs (e.g., ['%0', '%1'])
        """
        cmd = ["tmux", "list-panes", "-t", self.session_name, "-F", "#{pane_id}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip().split("\n") if result.stdout.strip() else []

    def split_window(self, direction: str = "-h"):
        """
        Split the current window into panes.

        Args:
            direction: Split direction ('-h' = horizontal/side-by-side,
                                      '-v' = vertical/top-bottom)
        """
        cmd = ["tmux", "split-window", direction, "-t", self.session_name]
        subprocess.run(cmd, check=True, capture_output=True)
        time.sleep(0.2)  # Let split settle

    def get_pane_height(self, pane_id: Optional[str] = None) -> int:
        """
        Get height of a pane in lines.

        Args:
            pane_id: Pane identifier (None = current pane)

        Returns:
            Height in lines
        """
        target = pane_id if pane_id else self.session_name
        cmd = ["tmux", "display-message", "-p", "-t", target, "#{pane_height}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return int(result.stdout.strip()) if result.stdout.strip() else 0

    def get_pane_width(self, pane_id: Optional[str] = None) -> int:
        """
        Get width of a pane in characters.

        Args:
            pane_id: Pane identifier (None = current pane)

        Returns:
            Width in characters
        """
        target = pane_id if pane_id else self.session_name
        cmd = ["tmux", "display-message", "-p", "-t", target, "#{pane_width}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return int(result.stdout.strip()) if result.stdout.strip() else 0

    def get_global_option(self, option: str) -> str:
        """
        Get a tmux global option value.

        Args:
            option: Option name (e.g., '@help_pane_id')

        Returns:
            Option value as string
        """
        cmd = ["tmux", "show-option", "-gv", option]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip()

    def _session_exists(self) -> bool:
        """
        Check if our tmux session exists.

        Returns:
            True if session exists, False otherwise
        """
        result = subprocess.run(
            ["tmux", "has-session", "-t", self.session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0

    def cleanup(self):
        """
        Clean up the tmux session and process.

        Kills the tmux session and closes the pexpect process.
        MUST be called to prevent orphaned processes and sessions.
        """
        if self._is_cleaned_up:
            return

        self._is_cleaned_up = True

        # Kill tmux session
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", self.session_name],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

        # Close pexpect process
        if hasattr(self, "process"):
            try:
                if self.process.isalive():
                    self.process.terminate(force=True)
                self.process.close()
            except Exception:
                pass

    def __del__(self):
        """Destructor - ensure cleanup on garbage collection."""
        self.cleanup()


class PtySession(BaseSession):
    """
    Manages a direct PTY process for testing any interactive CLI application.

    This class spawns CLI processes directly via pexpect and maintains a
    virtual terminal screen using pyte. No tmux required.

    Example:
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo hello")
            assert session.verify_text_appears("hello")

        # Test fzf
        with PtySession(["fzf"]) as session:
            session.send_keys("test", literal=True)
            assert session.verify_text_appears("test")

        # With terminal visualization
        with PtySession(["bash"], enable_viz=True) as session:
            session.send_keys("ls -la")
            # Viewers can attach via: ptytest viz (in another terminal)

    Attributes:
        command: Command and arguments to execute
        width: Terminal width in characters
        height: Terminal height in characters
        timeout: Default timeout for operations
    """

    def __init__(
        self,
        command: List[str],
        width: int = 120,
        height: int = 40,
        timeout: int = 5,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        enable_viz: bool = False,
        viz_port: int = 8080,
    ):
        """
        Create a PTY session for direct process testing.

        Args:
            command: Command and arguments to execute (e.g., ["bash", "--norc"])
            width: Terminal width in characters
            height: Terminal height in characters
            timeout: Default timeout for operations in seconds
            env: Environment variables (None = inherit from parent)
            cwd: Working directory (None = current directory)
            enable_viz: Enable terminal visualization (requires ptytest[viz])
            viz_port: Deprecated (not used with Textual-based viz)

        Raises:
            ImportError: If enable_viz=True but viz dependencies not installed
        """
        super().__init__(timeout=timeout)
        self.command = command
        self.width = width
        self.height = height
        self.env = env
        self.cwd = cwd

        # Initialize attributes that cleanup() depends on
        self._viz_server = None

        # Visualization support (broadcaster for Textual viewers)
        if enable_viz:
            try:
                from .viz import start_viz_broadcaster
                self._viz_server = start_viz_broadcaster(self)
                print(f"Visualization broadcaster started. Viewers can attach via: ptytest viz")
            except ImportError as e:
                raise ImportError(
                    "Visualization dependencies not installed. "
                    "Install with: uv pip install ptytest[viz]"
                ) from e

        # Spawn process using ptydriver's PtyProcess
        self._pty_process = PtyProcessDriver(
            command=command,
            width=width,
            height=height,
            timeout=timeout,
            env=env,
            cwd=cwd
        )

        # Get the screen from the underlying PtyProcess
        self.screen = self._pty_process.screen
        self.stream = self._pty_process.stream
        self.screen_lock = self._pty_process.screen_lock

        # Give process time to start
        time.sleep(0.1)

    @property
    def process(self):
        """Get the process with compatibility layer."""
        class PtyProcessCompat:
            """Compatibility layer for PtyProcess from ptydriver."""

            def __init__(self, ptyprocess):
                self._ptyprocess = ptyprocess

            def isalive(self):
                """Legacy compatibility method."""
                return self._ptyprocess.is_alive()

            def send(self, text):
                """Legacy send method."""
                return self._ptyprocess.send(text, press_enter=True)

            def sendline(self, text):
                """Legacy sendline method."""
                return self._ptyprocess.send(text)

            def write(self, text):
                """Legacy write method."""
                return self._ptyprocess.send_raw(text)

            def __getattr__(self, name):
                """Delegate all other attributes to the underlying PtyProcess."""
                return getattr(self._ptyprocess, name)

        return PtyProcessCompat(self._pty_process)

    def send_raw(self, sequence: str, delay: float = 0.15):
        """
        Send raw byte sequences or escape codes to the process.

        Args:
            sequence: Raw string to send (can include escape sequences)
            delay: Delay after sending for processing (seconds)
        """
        if not self._pty_process or not self._pty_process.is_alive():
            raise RuntimeError("Process not running")

        self._pty_process.send_raw(sequence, delay=delay)

    def send_keys(self, keys: str, delay: float = 0.15, literal: bool = False):
        """
        Send keys to the process.

        Args:
            keys: Keys to send
            delay: Delay after sending (seconds)
            literal: If True, send keys as-is (no Enter).
                    If False (default), append Enter key.
        """
        if not self._pty_process or not self._pty_process.is_alive():
            raise RuntimeError("Process not running")

        self._pty_process.send(keys, delay=delay, press_enter=not literal)

    def get_content(self, include_history: bool = True) -> str:
        """
        Get visible terminal content from virtual screen.

        Args:
            include_history: Not used for PtySession (no scrollback history)

        Returns:
            Text content of the current screen
        """
        return self._pty_process.get_content()

    def get_screen(self) -> List[str]:
        """
        Get the current screen as a list of lines.

        Returns:
            List of lines (strings) representing the screen
        """
        return self._pty_process.get_screen()

    def cleanup(self):
        """
        Clean up the process and resources.

        MUST be called to prevent orphaned processes.
        """
        if self._is_cleaned_up:
            return

        self._is_cleaned_up = True

        # Shutdown viz server if running
        if self._viz_server:
            try:
                self._viz_server.shutdown()
            except Exception:
                pass

        # Cleanup underlying PtyProcess
        if hasattr(self, '_pty_process'):
            self._pty_process.cleanup()

    def __del__(self):
        """Destructor - ensure cleanup on garbage collection."""
        self.cleanup()
