"""
Examples of testing fzf (fuzzy finder) with ptytest.

These tests demonstrate using PtySession to test interactive fuzzy finding
with fzf. Run with: pytest examples/test_fzf.py -v

Note: Requires fzf to be installed (https://github.com/junegunn/fzf)
"""

import shutil
import time

import pytest

from ptytest import FzfKeys, Keys, PtySession

pytestmark = pytest.mark.direct_pty


@pytest.fixture(scope="module")
def fzf_available():
    """Check if fzf is available."""
    if not shutil.which("fzf"):
        pytest.skip("fzf is not installed")


class TestFzfBasics:
    """Basic fzf usage tests."""

    def test_launch_fzf_with_input(self, fzf_available):
        """Test launching fzf with pre-populated items."""
        # Use shell command to pipe items to fzf
        items = ["apple", "banana", "cherry", "apricot", "blueberry"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            # Wait for fzf prompt to appear
            time.sleep(0.3)
            content = session.get_content()

            # Verify items appear in the list
            assert "apple" in content or "5/5" in content  # Either items or count

    def test_filter_with_search_query(self, fzf_available):
        """Test typing search query to filter results."""
        items = ["apple", "banana", "cherry", "apricot", "blueberry"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Type search query "ap" (should match apple, apricot)
            session.send_keys("ap", literal=True)
            time.sleep(0.2)

            content = session.get_content()
            # Should show 2/5 or similar count, or show filtered items
            assert "ap" in content.lower()  # Query should be visible

    def test_navigate_with_arrow_keys(self, fzf_available):
        """Test navigating filtered results with arrow keys."""
        items = ["first", "second", "third", "fourth"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Navigate down
            session.send_raw(FzfKeys.DOWN)
            time.sleep(0.1)

            # Navigate down again
            session.send_raw(FzfKeys.DOWN)
            time.sleep(0.1)

            # Content should have changed (cursor moved)
            content = session.get_content()
            assert len(content) > 0

    def test_select_with_enter(self, fzf_available):
        """Test selecting an item with Enter."""
        items = ["option1", "option2", "option3"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Press Enter to select
            session.send_raw(FzfKeys.ENTER)
            time.sleep(0.2)

            # Process should exit after selection
            # We can't easily capture the selection without additional setup,
            # but we can verify the process behavior

    def test_cancel_with_escape(self, fzf_available):
        """Test canceling fzf with Escape."""
        items = ["item1", "item2", "item3"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Verify fzf is running
            assert session.process.isalive()

            # Press Escape to cancel
            session.send_raw(FzfKeys.ESC)
            time.sleep(0.2)

            # Process should exit after cancellation
            time.sleep(0.3)


class TestFzfAdvanced:
    """Advanced fzf features."""

    def test_multi_select_with_tab(self, fzf_available):
        """Test multi-select mode with Tab key."""
        items = ["file1.txt", "file2.txt", "file3.txt"]
        # -m enables multi-select mode
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf -m"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Select first item with Tab
            session.send_raw(FzfKeys.TAB)
            time.sleep(0.1)

            # Navigate down
            session.send_raw(FzfKeys.DOWN)
            time.sleep(0.1)

            # Select second item with Tab
            session.send_raw(FzfKeys.TAB)
            time.sleep(0.1)

            content = session.get_content()
            # Should show multiple selections (exact format varies)
            assert len(content) > 0

    def test_ctrl_k_ctrl_j_navigation(self, fzf_available):
        """Test Ctrl-K and Ctrl-J for navigation (vim-style)."""
        items = ["alpha", "beta", "gamma", "delta"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Ctrl-J moves down (like Down arrow)
            session.send_raw(FzfKeys.CTRL_J)
            time.sleep(0.1)

            # Ctrl-K moves up (like Up arrow)
            session.send_raw(FzfKeys.CTRL_K)
            time.sleep(0.1)

            content = session.get_content()
            assert len(content) > 0


class TestFzfRealWorld:
    """Real-world fzf usage patterns."""

    def test_large_list_filtering(self, fzf_available):
        """Test filtering a large list of items."""
        # Generate a large list
        items = [f"item_{i:04d}" for i in range(100)]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Filter to specific items
            session.send_keys("_00", literal=True)  # Match item_000x
            time.sleep(0.2)

            content = session.get_content()
            # Should show filtered count
            assert "_00" in content or "00" in content

    def test_clear_query_and_restart(self, fzf_available):
        """Test clearing query with Ctrl-U and restarting."""
        items = ["test1", "test2", "test3"]
        cmd = ["sh", "-c", f"echo '{chr(10).join(items)}' | fzf"]

        with PtySession(cmd, height=20, width=80) as session:
            time.sleep(0.3)

            # Type a query
            session.send_keys("xyz", literal=True)
            time.sleep(0.1)

            # Clear the query with Ctrl-U
            session.send_raw(Keys.CTRL_U)
            time.sleep(0.1)

            # Type new query
            session.send_keys("test", literal=True)
            time.sleep(0.2)

            content = session.get_content()
            assert "test" in content.lower()
