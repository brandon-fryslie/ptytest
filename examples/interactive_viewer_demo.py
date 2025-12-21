#!/usr/bin/env python3
"""
Interactive Textual Viewer Demo

This script demonstrates the pure-Python, in-terminal viewer for ptytest
by running an actual interactive CLI testing scenario.

Run:
    uv run python examples/interactive_viewer_demo.py

Controls:
    - q: Quit viewer
    - r: Refresh screen
    - The viewer is READ-ONLY (no input sent to PTY)
"""

import shutil
import sys
import time
import threading

from ptytest import PtySession, Keys, FzfKeys
from ptytest.viz import TerminalViewer


def run_fzf_demo(session):
    """Demo: Interactive fzf fuzzy finder testing."""
    time.sleep(1.5)  # Give viewer time to start

    # Generate a list of items and pipe to fzf
    session.send_keys(
        "echo -e 'apple\\nbanana\\ncherry\\ndate\\nelderberry\\nfig\\ngrape\\nhoneydew' | fzf"
    )
    time.sleep(1)

    # Type to filter
    session.send_keys("an", literal=True)
    time.sleep(0.8)

    # Navigate with arrow keys
    session.send_raw(Keys.DOWN)
    time.sleep(0.5)
    session.send_raw(Keys.UP)
    time.sleep(0.5)

    # Clear and try different filter
    session.send_raw(FzfKeys.CLEAR_QUERY)
    time.sleep(0.5)
    session.send_keys("err", literal=True)
    time.sleep(0.8)

    # Select with Enter
    session.send_raw(FzfKeys.ACCEPT)
    time.sleep(1)

    # Show result
    session.send_keys("echo 'Selected item shown above!'")
    time.sleep(1.5)

    # Run fzf again with multi-select
    session.send_keys(
        "echo -e 'red\\ngreen\\nblue\\nyellow\\npurple\\norange' | fzf --multi"
    )
    time.sleep(1)

    # Select multiple items with Tab
    session.send_raw(FzfKeys.TOGGLE)  # Toggle first
    time.sleep(0.3)
    session.send_raw(Keys.DOWN)
    time.sleep(0.3)
    session.send_raw(FzfKeys.TOGGLE)  # Toggle second
    time.sleep(0.3)
    session.send_raw(Keys.DOWN)
    time.sleep(0.3)
    session.send_raw(FzfKeys.TOGGLE)  # Toggle third
    time.sleep(0.5)

    # Accept selection
    session.send_raw(FzfKeys.ACCEPT)
    time.sleep(1)

    session.send_keys("echo '=== fzf demo complete ==='")
    time.sleep(2)


def run_lazygit_demo(session):
    """Demo: Interactive lazygit testing."""
    time.sleep(1.5)

    # Start lazygit
    session.send_keys("lazygit")
    time.sleep(2)

    # Navigate between panels
    from ptytest import LazygitKeys

    session.send_raw(LazygitKeys.FILES_PANEL)  # Files panel
    time.sleep(0.8)
    session.send_raw(LazygitKeys.BRANCHES_PANEL)  # Branches panel
    time.sleep(0.8)
    session.send_raw(LazygitKeys.COMMITS_PANEL)  # Commits panel
    time.sleep(0.8)
    session.send_raw(LazygitKeys.STATUS_PANEL)  # Back to status
    time.sleep(0.8)

    # Navigate within panel
    session.send_raw(LazygitKeys.DOWN)
    time.sleep(0.3)
    session.send_raw(LazygitKeys.DOWN)
    time.sleep(0.3)
    session.send_raw(LazygitKeys.UP)
    time.sleep(0.5)

    # Open help
    session.send_raw(LazygitKeys.HELP)
    time.sleep(1.5)
    session.send_raw(Keys.ESCAPE)
    time.sleep(0.5)

    # Quit lazygit
    session.send_raw(LazygitKeys.QUIT)
    time.sleep(1)

    session.send_keys("echo '=== lazygit demo complete ==='")
    time.sleep(2)


def run_python_repl_demo(session):
    """Demo: Interactive Python REPL testing."""
    time.sleep(1.5)

    # Start Python
    session.send_keys("python3")
    time.sleep(1)

    # Run some code
    session.send_keys("print('Hello from ptytest visualization!')")
    time.sleep(0.8)

    session.send_keys("2 + 2")
    time.sleep(0.6)

    session.send_keys("import math")
    time.sleep(0.5)

    session.send_keys("math.pi")
    time.sleep(0.6)

    session.send_keys("[x**2 for x in range(10)]")
    time.sleep(0.8)

    # Define a function
    session.send_keys("def greet(name):")
    time.sleep(0.3)
    session.send_keys("    return f'Hello, {name}!'")
    time.sleep(0.3)
    session.send_keys("")  # Empty line to end function
    time.sleep(0.5)

    session.send_keys("greet('ptytest')")
    time.sleep(0.8)

    # Exit
    session.send_keys("exit()")
    time.sleep(1)

    session.send_keys("echo '=== Python REPL demo complete ==='")
    time.sleep(2)


def run_vim_demo(session):
    """Demo: Interactive vim testing."""
    time.sleep(1.5)

    from ptytest import VimKeys

    # Start vim with no config
    session.send_keys("vim -u NONE")
    time.sleep(1)

    # Enter insert mode and type
    session.send_raw(VimKeys.INSERT)
    time.sleep(0.3)
    session.send_keys("Hello from ptytest!", literal=True)
    time.sleep(0.5)
    session.send_raw(Keys.ENTER)
    session.send_keys("This is a vim demo.", literal=True)
    time.sleep(0.5)
    session.send_raw(Keys.ENTER)
    session.send_keys("Watch the cursor move!", literal=True)
    time.sleep(0.8)

    # Back to normal mode
    session.send_raw(VimKeys.NORMAL)
    time.sleep(0.5)

    # Navigate
    session.send_raw(VimKeys.FIRST_LINE)  # gg
    time.sleep(0.5)
    session.send_raw(VimKeys.DOWN)  # j
    time.sleep(0.3)
    session.send_raw(VimKeys.DOWN)  # j
    time.sleep(0.3)
    session.send_raw(VimKeys.LINE_START)  # 0
    time.sleep(0.3)
    session.send_raw(VimKeys.WORD_FORWARD)  # w
    time.sleep(0.3)
    session.send_raw(VimKeys.WORD_FORWARD)  # w
    time.sleep(0.5)

    # Quit without saving
    session.send_raw(VimKeys.quit_force())
    time.sleep(1)

    session.send_keys("echo '=== vim demo complete ==='")
    time.sleep(2)


def main():
    # Check what tools are available
    has_fzf = shutil.which("fzf") is not None
    has_lazygit = shutil.which("lazygit") is not None
    has_vim = shutil.which("vim") is not None

    print("=" * 70)
    print("ptytest - Interactive CLI Testing Visualization Demo")
    print("=" * 70)
    print()
    print("This demo shows ptytest testing real interactive CLI applications.")
    print("The Textual viewer displays the terminal output in real-time.")
    print()
    print("Available demos:")
    if has_fzf:
        print("  - fzf: Fuzzy finder with filtering and multi-select")
    if has_lazygit:
        print("  - lazygit: Git TUI with panel navigation")
    if has_vim:
        print("  - vim: Text editor with modal editing")
    print("  - python: Python REPL interaction")
    print()
    print("Controls:")
    print("  - Press 'q' to quit the viewer")
    print("  - Press 'r' to refresh")
    print()
    print("=" * 70)
    print()

    time.sleep(1)

    # Create PTY session with visualization
    session = PtySession(["bash", "--norc"], enable_viz=True, width=100, height=30)

    def run_demos():
        """Run available demos in sequence."""
        time.sleep(1.5)

        session.send_keys("echo '=== ptytest Interactive CLI Demo ==='")
        time.sleep(1)

        # Run fzf demo if available
        if has_fzf:
            session.send_keys("echo '\\n>>> Starting fzf demo...'")
            time.sleep(1)
            run_fzf_demo(session)

        # Run vim demo if available
        if has_vim:
            session.send_keys("echo '\\n>>> Starting vim demo...'")
            time.sleep(1)
            run_vim_demo(session)

        # Always run Python demo
        session.send_keys("echo '\\n>>> Starting Python REPL demo...'")
        time.sleep(1)
        run_python_repl_demo(session)

        # Run lazygit demo if available (and we're in a git repo)
        if has_lazygit:
            session.send_keys("echo '\\n>>> Starting lazygit demo...'")
            time.sleep(1)
            run_lazygit_demo(session)

        session.send_keys("echo ''")
        session.send_keys("echo '======================================'")
        session.send_keys("echo '  All demos complete!'")
        session.send_keys("echo '  Press q to quit the viewer'")
        session.send_keys("echo '======================================'")

    try:
        broadcaster = session._viz_server

        # Start background thread to run demos
        demo_thread = threading.Thread(target=run_demos, daemon=True)
        demo_thread.start()

        # Launch Textual viewer (this blocks until user quits)
        viewer = TerminalViewer(broadcaster, session_name="Interactive CLI Demo")
        viewer.run()

    finally:
        print("\nCleaning up session...")
        session.cleanup()
        print("Demo complete!")


if __name__ == "__main__":
    main()
