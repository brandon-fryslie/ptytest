"""
Testing Patterns - Common patterns and best practices for ptytest.

This file demonstrates effective testing patterns when working with
interactive terminal applications.

Run with: uv run pytest examples/07_testing_patterns.py -v
"""

import time

import pytest

from ptytest import PtySession, Keys


# ============================================================================
# Pattern 1: Wait for Ready State
# ============================================================================


class TestWaitForReady:
    """Always wait for the application to be ready before interacting."""

    def test_wait_for_prompt(self):
        """Wait for shell prompt before sending commands."""
        with PtySession(["bash", "--norc"]) as session:
            # Wait for prompt indicator
            assert session.verify_text_appears("$", timeout=2)

            # Now safe to send commands
            session.send_keys("echo ready")
            assert session.verify_text_appears("ready")

    def test_wait_for_application_ready(self):
        """Wait for application-specific ready indicators."""
        with PtySession(["python3"]) as session:
            # Wait for Python's prompt
            assert session.verify_text_appears(">>>", timeout=3)

            # Now interact
            session.send_keys("2 + 2")
            assert session.verify_text_appears("4")


# ============================================================================
# Pattern 2: Verify State Before and After
# ============================================================================


class TestVerifyStateChanges:
    """Verify state before and after operations."""

    def test_verify_before_after(self):
        """Check initial state, perform action, verify new state."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            # Check initial state
            session.send_keys("echo $PWD")
            initial_pwd = session.get_content()

            # Perform action
            session.send_keys("cd /tmp")
            session.verify_text_appears("$")

            # Verify new state
            session.send_keys("echo $PWD")
            assert session.verify_text_appears("/tmp")


# ============================================================================
# Pattern 3: Use Timeouts Appropriately
# ============================================================================


class TestTimeouts:
    """Set appropriate timeouts for different operations."""

    def test_fast_operation(self):
        """Fast operations need short timeouts."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo fast")
            # Quick operation - short timeout is fine
            assert session.verify_text_appears("fast", timeout=1)

    def test_slow_operation(self):
        """Slow operations need longer timeouts."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("sleep 1 && echo slow")
            # This takes time - use appropriate timeout
            assert session.verify_text_appears("slow", timeout=3)

    def test_timeout_error_messages(self):
        """wait_for_text provides helpful error messages."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo actual")

            with pytest.raises(TimeoutError) as excinfo:
                session.wait_for_text("nonexistent", timeout=0.5)

            # Error message includes current content
            assert "nonexistent" in str(excinfo.value)
            assert "actual" in str(excinfo.value)


# ============================================================================
# Pattern 4: Send Keys with Appropriate Delays
# ============================================================================


class TestKeyDelays:
    """Use appropriate delays between keystrokes."""

    def test_default_delay(self):
        """Default delay works for most cases."""
        with PtySession(["bash", "--norc"]) as session:
            # Default delay (0.15s) is usually sufficient
            session.send_keys("echo test")
            assert session.verify_text_appears("test")

    def test_rapid_keys(self):
        """Reduce delay for rapid key sequences."""
        with PtySession(["bash", "--norc"]) as session:
            # For sequences that need to be fast
            session.send_keys("echo ", literal=True, delay=0.05)
            session.send_keys("rapid", literal=True, delay=0.05)
            session.send_raw(Keys.ENTER)
            assert session.verify_text_appears("rapid")

    def test_slow_application(self):
        """Increase delay for slow applications."""
        with PtySession(["bash", "--norc"]) as session:
            # Some apps need more time to process
            session.send_keys("echo slow", delay=0.3)
            assert session.verify_text_appears("slow")


# ============================================================================
# Pattern 5: Clean Up Resources
# ============================================================================


class TestResourceCleanup:
    """Ensure proper resource cleanup."""

    def test_context_manager(self):
        """Use context managers for automatic cleanup."""
        # Good: Resources automatically cleaned up
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo test")
            assert session.verify_text_appears("test")
        # Session is cleaned up here

    def test_explicit_cleanup(self):
        """Explicit cleanup when needed."""
        session = PtySession(["bash", "--norc"])
        try:
            session.send_keys("echo test")
            assert session.verify_text_appears("test")
        finally:
            session.cleanup()  # Always clean up


# ============================================================================
# Pattern 6: Handle Multiple Scenarios
# ============================================================================


class TestMultipleScenarios:
    """Handle different scenarios in tests."""

    @pytest.mark.parametrize("input_text,expected", [
        ("hello", "hello"),
        ("world", "world"),
        ("test 123", "test 123"),
    ])
    def test_multiple_inputs(self, input_text, expected):
        """Test multiple input variations."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")
            session.send_keys(f"echo '{input_text}'")
            assert session.verify_text_appears(expected)


# ============================================================================
# Pattern 7: Test Interactive Sequences
# ============================================================================


class TestInteractiveSequences:
    """Test multi-step interactive workflows."""

    def test_multi_step_interaction(self):
        """Test a sequence of interactions."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            # Step 1: Create variable
            session.send_keys("MY_VAR='step1'")
            session.verify_text_appears("$")

            # Step 2: Modify it
            session.send_keys("MY_VAR=\"${MY_VAR}_step2\"")
            session.verify_text_appears("$")

            # Step 3: Verify result
            session.send_keys("echo $MY_VAR")
            assert session.verify_text_appears("step1_step2")

    def test_state_accumulation(self):
        """Test that state accumulates correctly."""
        with PtySession(["python3"]) as session:
            session.verify_text_appears(">>>")

            # Build up state
            session.send_keys("x = 1")
            session.verify_text_appears(">>>")

            session.send_keys("y = 2")
            session.verify_text_appears(">>>")

            session.send_keys("x + y")
            assert session.verify_text_appears("3")


# ============================================================================
# Pattern 8: Error Recovery
# ============================================================================


class TestErrorRecovery:
    """Handle errors and recover gracefully."""

    def test_recover_from_bad_state(self):
        """Recover from a bad state."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            # Enter a bad state (partial command)
            session.send_keys("echo 'incomplete", literal=True)

            # Recover with Ctrl-C
            session.send_raw(Keys.CTRL_C)
            session.verify_text_appears("$")

            # Now in good state again
            session.send_keys("echo 'recovered'")
            assert session.verify_text_appears("recovered")

    def test_clear_line(self):
        """Clear the current line if something goes wrong."""
        with PtySession(["bash", "--norc"]) as session:
            session.verify_text_appears("$")

            # Type something we don't want
            session.send_keys("wrong command", literal=True)

            # Clear it with Ctrl-U
            session.send_raw(Keys.CTRL_U)

            # Type the right thing
            session.send_keys("echo 'correct'")
            assert session.verify_text_appears("correct")


# ============================================================================
# Pattern 9: Test Screen Content
# ============================================================================


class TestScreenContent:
    """Work with screen content effectively."""

    def test_get_full_content(self):
        """Get and analyze full screen content."""
        with PtySession(["bash", "--norc"]) as session:
            for i in range(3):
                session.send_keys(f"echo 'Line {i}'")

            session.verify_text_appears("Line 2")

            content = session.get_content()
            assert "Line 0" in content
            assert "Line 1" in content
            assert "Line 2" in content

    def test_get_screen_lines(self):
        """Get screen as list of lines."""
        with PtySession(["bash", "--norc"], width=80, height=24) as session:
            session.send_keys("echo 'test line'")
            session.verify_text_appears("test line")

            lines = session.get_screen()
            assert isinstance(lines, list)
            assert len(lines) == 24  # Screen height


# ============================================================================
# Pattern 10: Assertions with Context
# ============================================================================


class TestAssertionsWithContext:
    """Provide helpful context when assertions fail."""

    def test_with_context(self):
        """Include context in assertion messages."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo 'actual output'")
            session.verify_text_appears("actual output")

            content = session.get_content()
            assert "actual output" in content, (
                f"Expected 'actual output' in screen content.\n"
                f"Actual content:\n{content}"
            )

    def test_detailed_failure(self):
        """Detailed failure information."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo 'result'")

            try:
                session.wait_for_text("wrong", timeout=0.5)
            except TimeoutError as e:
                # The error includes the actual content
                assert "result" in str(e)


# ============================================================================
# Pattern 11: Avoid Flaky Tests
# ============================================================================


class TestAvoidFlaky:
    """Patterns to avoid flaky tests."""

    def test_wait_dont_sleep(self):
        """Use verify_text_appears instead of time.sleep."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("echo done")

            # BAD: Fixed sleep might be too short or too long
            # time.sleep(1)

            # GOOD: Wait for actual output
            assert session.verify_text_appears("done")

    def test_use_appropriate_timeout(self):
        """Use timeouts that account for variance."""
        with PtySession(["bash", "--norc"]) as session:
            # If something usually takes 0.1s, use 1s timeout
            # to account for system load variance
            session.send_keys("echo fast")
            assert session.verify_text_appears("fast", timeout=1)

    def test_verify_ready_state(self):
        """Always verify ready state before acting."""
        with PtySession(["bash", "--norc"]) as session:
            # Wait for shell to be ready
            session.verify_text_appears("$")

            # Now it's safe to send commands
            session.send_keys("echo test")
            assert session.verify_text_appears("test")
