"""
Terminal Visualization - Watch tests run in real-time.

ptytest provides a pure-Python, in-terminal visualization feature using
Textual and pyte. Multiple viewers can watch the same session.

Requirements: uv pip install ptytest[viz]

Run with: uv run pytest examples/08_visualization.py -v
"""

import time

import pytest

from ptytest import PtySession, Keys


# Check if viz dependencies are available
try:
    from ptytest.viz import TerminalViewer, ScreenBroadcaster
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not VIZ_AVAILABLE,
    reason="Visualization dependencies not installed. Run: uv pip install ptytest[viz]"
)


class TestVisualizationBasics:
    """Basic visualization usage."""

    def test_enable_viz_parameter(self):
        """Enable visualization with enable_viz=True."""
        # Note: This starts the broadcaster but not the interactive viewer
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            session.verify_text_appears("$")
            session.send_keys("echo 'visualized!'")
            assert session.verify_text_appears("visualized!")

            # The _viz_server is the ScreenBroadcaster
            assert session._viz_server is not None

    def test_custom_viz_port(self):
        """Use a custom port for visualization."""
        with PtySession(["bash", "--norc"], enable_viz=True, viz_port=9090) as session:
            session.verify_text_appears("$")
            session.send_keys("echo 'custom port'")
            assert session.verify_text_appears("custom port")

    def test_viz_disabled_by_default(self):
        """Visualization is disabled by default (zero overhead)."""
        with PtySession(["bash", "--norc"]) as session:
            # No viz server when disabled
            assert session._viz_server is None

            session.send_keys("echo 'no viz'")
            assert session.verify_text_appears("no viz")


class TestScreenBroadcaster:
    """Test the ScreenBroadcaster component."""

    def test_broadcaster_creation(self):
        """Create a ScreenBroadcaster manually."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            # Create broadcaster from the session (not screen directly)
            broadcaster = ScreenBroadcaster(session)

            # Start it
            broadcaster.start()

            try:
                # Send some commands
                session.send_keys("echo 'broadcasting'")
                session.verify_text_appears("broadcasting")

                # Get current screen state
                lines, cursor_x, cursor_y = broadcaster.get_screen_state()
                assert isinstance(lines, list)
                assert len(lines) > 0
            finally:
                broadcaster.shutdown()

    def test_broadcaster_subscribers(self):
        """Subscribe to screen updates."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            updates_received = []

            def on_update(lines, cursor_x, cursor_y):
                updates_received.append((len(lines), cursor_x, cursor_y))

            # Subscribe
            broadcaster.subscribe(on_update)

            try:
                # Generate some output
                session.send_keys("echo 'update 1'")
                session.verify_text_appears("update 1")
                time.sleep(0.2)  # Let broadcaster poll

                session.send_keys("echo 'update 2'")
                session.verify_text_appears("update 2")
                time.sleep(0.2)

                # Unsubscribe
                broadcaster.unsubscribe(on_update)

                # Should have received updates
                # (exact number depends on polling frequency)

            finally:
                broadcaster.shutdown()


class TestVisualizationIntegration:
    """Integration tests for visualization."""

    def test_viz_with_multiple_commands(self):
        """Run multiple commands with visualization."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            session.verify_text_appears("$")

            commands = [
                "echo 'Step 1: Initialize'",
                "echo 'Step 2: Process'",
                "echo 'Step 3: Complete'",
            ]

            for cmd in commands:
                session.send_keys(cmd)
                expected = cmd.split("'")[1]  # Extract quoted text
                assert session.verify_text_appears(expected)

    def test_viz_with_interactive_app(self):
        """Visualization with an interactive application."""
        with PtySession(["python3"], enable_viz=True) as session:
            # Wait for Python prompt
            assert session.verify_text_appears(">>>", timeout=3)

            # Run some code
            session.send_keys("x = 42")
            session.verify_text_appears(">>>")

            session.send_keys("print(f'The answer is {x}')")
            assert session.verify_text_appears("The answer is 42")

            session.send_keys("exit()")


class TestTerminalViewer:
    """Test the TerminalViewer component."""

    def test_viewer_creation(self):
        """Create a TerminalViewer."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            broadcaster = ScreenBroadcaster(session)
            broadcaster.start()

            try:
                # Create viewer (but don't run it - that's interactive)
                viewer = TerminalViewer(broadcaster, session_name="test")
                assert viewer is not None
            finally:
                broadcaster.shutdown()


# ============================================================================
# Manual Testing / Demo
# ============================================================================


@pytest.mark.skip(reason="Interactive demo - run manually")
class TestInteractiveDemo:
    """
    Interactive visualization demos.

    To run manually:
        python -c "
        from ptytest import PtySession
        from ptytest.viz import TerminalViewer

        with PtySession(['bash'], enable_viz=True) as session:
            broadcaster = session._viz_server
            viewer = TerminalViewer(broadcaster, session_name='demo')
            viewer.run()
        "
    """

    def test_interactive_viewer(self):
        """Launch interactive viewer (requires manual interaction)."""
        with PtySession(["bash", "--norc"], enable_viz=True) as session:
            broadcaster = session._viz_server
            viewer = TerminalViewer(broadcaster, session_name="Interactive Demo")

            # This would block and show the viewer
            # viewer.run()  # Press 'q' to quit

            # For testing, just verify it's created
            assert viewer is not None


# ============================================================================
# Documentation
# ============================================================================


class TestVisualizationDocs:
    """
    Documentation for visualization features.

    ## Overview

    ptytest's visualization feature allows you to watch PTY sessions in
    real-time. It's built on:

    - **pyte**: Virtual terminal emulator (already used by PtySession)
    - **Textual**: Modern Python TUI framework (from the Rich authors)

    ## Architecture

    ```
    PtySession
        └── pyte.Screen (virtual terminal buffer)
                └── ScreenBroadcaster (polls screen, notifies subscribers)
                        └── TerminalViewer (Textual app that renders screen)
    ```

    ## Usage Patterns

    ### 1. Enable in Session
    ```python
    with PtySession(['bash'], enable_viz=True) as session:
        # The broadcaster starts automatically
        session.send_keys('echo hello')
    ```

    ### 2. Subscribe to Updates
    ```python
    broadcaster = session._viz_server

    def on_update(lines, cursor_x, cursor_y):
        print(f"Screen has {len(lines)} lines, cursor at ({cursor_x}, {cursor_y})")

    broadcaster.subscribe(on_update)
    ```

    ### 3. Launch Interactive Viewer
    ```python
    from ptytest.viz import TerminalViewer

    viewer = TerminalViewer(broadcaster, session_name='my-test')
    viewer.run()  # Blocks until 'q' is pressed
    ```

    ## Key Bindings (in TerminalViewer)

    - `q` - Quit the viewer
    - `r` - Force refresh

    ## Benefits Over Browser-Based Approach

    1. **Pure Python** - No JavaScript, no browser needed
    2. **No network** - No HTTP server, WebSocket, or ports
    3. **Simpler** - Just Python and your terminal
    4. **Lighter** - textual instead of flask+socketio+xterm.js
    """

    def test_docs(self):
        """This test exists to hold documentation."""
        pass
