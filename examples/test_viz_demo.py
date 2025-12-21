"""
Demo: Pure-Python terminal visualization with ptytest.

This example demonstrates the Textual-based visualization feature for PtySession.
Unlike the previous browser-based approach, this runs entirely in your terminal!

Prerequisites:
    uv pip install -e ".[viz]"

Run:
    # Terminal 1: Run the test
    uv run pytest examples/test_viz_demo.py::test_basic_visualization -v -s

    # Terminal 2: Attach a viewer (future feature - manual demo for now)
    # python -m ptytest.viz

Note: The current implementation uses ScreenBroadcaster. Full viewer integration
      with a standalone CLI command is coming soon.
"""

import pytest
import time

# Skip if viz dependencies not installed
pytest.importorskip("textual")

from ptytest import PtySession
from ptytest.viz.viewer import TerminalViewer


@pytest.mark.viz
def test_basic_visualization_broadcaster():
    """
    Basic visualization demo - shows broadcaster receiving updates.

    This demonstrates that the broadcaster correctly receives terminal updates.
    """
    print("\n" + "=" * 70)
    print("Terminal Visualization Broadcaster Demo")
    print("=" * 70)
    print("\nStarting broadcaster...")
    print("=" * 70 + "\n")

    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        # Track updates
        updates = []

        def on_update(lines, cursor_x, cursor_y):
            content = "\n".join(lines)
            updates.append(content)
            print(f"[Update {len(updates)}] Screen updated (cursor: {cursor_x}, {cursor_y})")

        broadcaster.subscribe(on_update)

        # Give broadcaster time to start
        time.sleep(0.5)

        # Run some commands to demonstrate visualization
        print("Running: echo 'Hello from ptytest!'")
        session.send_keys('echo "Hello from ptytest!"')
        time.sleep(1)

        print("Running: ls -la")
        session.send_keys("ls -la")
        time.sleep(1)

        print("Running: date")
        session.send_keys("date")
        time.sleep(1)

        print(f"\nTotal updates received: {len(updates)}")
        print("Broadcaster demo complete.")


@pytest.mark.viz
@pytest.mark.skip(reason="Interactive Textual app - run manually")
def test_interactive_viewer():
    """
    Interactive viewer demo - launches Textual TUI.

    To run this manually:
        uv run python examples/test_viz_demo.py
    """
    print("\n" + "=" * 70)
    print("Interactive Terminal Viewer Demo")
    print("=" * 70)
    print("\nLaunching Textual viewer...")
    print("Press 'q' to quit the viewer")
    print("=" * 70 + "\n")

    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        # Send some initial commands
        session.send_keys('echo "Welcome to ptytest viewer!"')
        time.sleep(0.5)
        session.send_keys("ls")
        time.sleep(0.5)

        # Launch viewer (this will take over the terminal)
        viewer = TerminalViewer(broadcaster, session_name="bash")
        viewer.run()


@pytest.mark.viz
def test_multiple_viewers_simulation():
    """
    Simulate multiple viewers watching same session.

    This demonstrates that multiple subscribers can watch the same session
    without interfering with each other.
    """
    print("\n" + "=" * 70)
    print("Multiple Viewers Demo")
    print("=" * 70)
    print("\nSimulating 3 viewers watching the same session...")
    print("=" * 70 + "\n")

    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        # Simulate 3 different viewers
        viewer1_updates = []
        viewer2_updates = []
        viewer3_updates = []

        def viewer1_callback(lines, cx, cy):
            viewer1_updates.append(f"Viewer1: {len(lines)} lines")

        def viewer2_callback(lines, cx, cy):
            viewer2_updates.append(f"Viewer2: cursor at ({cx}, {cy})")

        def viewer3_callback(lines, cx, cy):
            content = "\n".join(lines)
            if "test" in content.lower():
                viewer3_updates.append("Viewer3: detected 'test'")

        broadcaster.subscribe(viewer1_callback)
        broadcaster.subscribe(viewer2_callback)
        broadcaster.subscribe(viewer3_callback)

        time.sleep(0.3)

        # Send commands
        print("Running commands...")
        session.send_keys('echo "Testing multiple viewers"')
        time.sleep(0.5)

        session.send_keys("pwd")
        time.sleep(0.5)

        # Check all viewers received updates
        print(f"\nViewer 1 received {len(viewer1_updates)} updates")
        print(f"Viewer 2 received {len(viewer2_updates)} updates")
        print(f"Viewer 3 received {len(viewer3_updates)} updates")

        assert len(viewer1_updates) > 0
        assert len(viewer2_updates) > 0
        # Viewer 3 might not get updates if 'test' isn't visible

        print("\nAll viewers successfully received updates!")


@pytest.mark.viz
def test_colored_output():
    """
    Demonstrate colored terminal output with broadcaster.

    Shows that ANSI escape sequences are properly handled by pyte.
    """
    print("\n" + "=" * 70)
    print("Colored Output Demo")
    print("=" * 70)
    print("\nTesting ANSI color handling...")
    print("=" * 70 + "\n")

    with PtySession(["bash", "--norc"], enable_viz=True) as session:
        broadcaster = session._viz_server

        # Track colored output
        def check_colors(lines, cx, cy):
            content = "\n".join(lines)
            # pyte processes ANSI codes, so we check for the text
            if "Red" in content or "Green" in content:
                print(f"✓ Detected colored text in screen")

        broadcaster.subscribe(check_colors)
        time.sleep(0.3)

        # Output colored text
        print("Sending colored output commands...")
        session.send_keys('echo -e "\\033[31mRed text\\033[0m"')
        time.sleep(0.5)

        session.send_keys('echo -e "\\033[32mGreen text\\033[0m"')
        time.sleep(0.5)

        session.send_keys('echo -e "\\033[33mYellow text\\033[0m"')
        time.sleep(0.5)

        print("\nColored output demo complete.")


@pytest.mark.viz
@pytest.mark.slow
@pytest.mark.skip(reason="Requires fzf - run manually if fzf is installed")
def test_fzf_visualization():
    """
    Demonstrate fzf visualization.

    This shows how interactive TUI applications work with the broadcaster.
    Requires fzf to be installed.
    """
    print("\n" + "=" * 70)
    print("fzf Visualization Demo")
    print("=" * 70)
    print("\nStarting fzf with broadcaster...")
    print("=" * 70 + "\n")

    # Create fzf with some test data
    cmd = ["bash", "-c", 'echo -e "apple\\nbanana\\ncherry\\ndate\\nfig\\ngrape" | fzf']

    with PtySession(cmd, enable_viz=True) as session:
        broadcaster = session._viz_server

        updates = []

        def track_fzf(lines, cx, cy):
            content = "\n".join(lines)
            if "6/6" in content or "apple" in content:
                updates.append("fzf screen detected")

        broadcaster.subscribe(track_fzf)

        # Wait for fzf to start
        assert session.verify_text_appears("6/6", timeout=3)

        # Type a query to filter
        session.send_keys("ap", literal=True)
        time.sleep(1)

        # Verify filtering works
        assert session.verify_text_appears("apple")

        print(f"\nfzf demo: {len(updates)} screen updates detected")

        # Exit fzf
        session.send_raw("\x1b")  # Escape key

    print("\nfzf visualization demo complete.")


if __name__ == "__main__":
    # Run demos directly with: uv run python examples/test_viz_demo.py
    print("\nRunning basic broadcaster demo...")
    test_basic_visualization_broadcaster()

    print("\nRunning multiple viewers demo...")
    test_multiple_viewers_simulation()

    print("\nRunning colored output demo...")
    test_colored_output()

    print("\n" + "=" * 70)
    print("All demos complete!")
    print("=" * 70)
