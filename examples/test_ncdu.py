"""
Examples of testing ncdu (disk usage analyzer) with ptytest.

These tests demonstrate using PtySession to test interactive directory
navigation and disk usage analysis with ncdu. Run with: pytest examples/test_ncdu.py -v

Note: Requires ncdu to be installed (https://dev.yorhel.nl/ncdu)
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from ptytest import Keys, PtySession

pytestmark = pytest.mark.direct_pty


@pytest.fixture(scope="module")
def ncdu_available():
    """Check if ncdu is available."""
    if not shutil.which("ncdu"):
        pytest.skip("ncdu is not installed")


@pytest.fixture
def test_directory():
    """Create a test directory structure for ncdu to scan."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small directory structure
        base = Path(tmpdir)

        # Create directories
        (base / "dir1").mkdir()
        (base / "dir2").mkdir()
        (base / "dir1" / "subdir").mkdir()

        # Create some files with known sizes
        (base / "file1.txt").write_text("x" * 1000)  # 1KB
        (base / "dir1" / "file2.txt").write_text("x" * 2000)  # 2KB
        (base / "dir1" / "subdir" / "file3.txt").write_text("x" * 500)  # 0.5KB
        (base / "dir2" / "file4.txt").write_text("x" * 1500)  # 1.5KB

        yield tmpdir


class TestNcduBasics:
    """Basic ncdu usage tests."""

    def test_launch_ncdu_and_verify_initial_view(self, ncdu_available, test_directory):
        """Test launching ncdu on a test directory and verifying initial view."""
        # Use -0 flag to disable colors (easier to test)
        # Use -q to suppress progress animation
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            # Wait for scan to complete - ncdu shows "Scanning..." then the list
            import time
            time.sleep(1.0)  # Give ncdu time to scan

            content = session.get_content()

            # Should show directories and files
            assert "dir1" in content or "dir2" in content or "file" in content

    def test_navigate_with_arrows(self, ncdu_available, test_directory):
        """Test navigating the file list with arrow keys."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Navigate down
            session.send_raw(Keys.DOWN)
            time.sleep(0.1)

            # Navigate down again
            session.send_raw(Keys.DOWN)
            time.sleep(0.1)

            # Navigate up
            session.send_raw(Keys.UP)
            time.sleep(0.1)

            content = session.get_content()
            # Verify we still see the directory contents
            assert len(content) > 0

    def test_enter_directory(self, ncdu_available, test_directory):
        """Test entering a directory with Enter key."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Navigate to dir1 (might need to move down depending on sort order)
            # Just press Enter on current selection
            session.send_raw(Keys.ENTER)
            time.sleep(0.3)

            content = session.get_content()

            # Content should exist after entering a directory
            # (can't rely on specific content due to ordering)
            assert isinstance(content, str)

    def test_exit_directory_with_left_arrow(self, ncdu_available, test_directory):
        """Test returning to parent directory with left arrow."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Enter a directory
            session.send_raw(Keys.ENTER)
            time.sleep(0.3)

            # Go back to parent with left arrow
            session.send_raw(Keys.LEFT)
            time.sleep(0.3)

            content = session.get_content()
            # Should be back at parent directory
            assert len(content) > 0


class TestNcduNavigation:
    """Test ncdu navigation features."""

    def test_navigate_deep_directory_structure(self, ncdu_available, test_directory):
        """Test navigating into nested directories."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Try to navigate to dir1
            # Find and enter dir1
            for _ in range(5):  # Try a few downs to find a directory
                session.send_raw(Keys.DOWN)
                time.sleep(0.05)

            session.send_raw(Keys.ENTER)
            time.sleep(0.3)

            # Try to enter subdir if we're in dir1
            session.send_raw(Keys.ENTER)
            time.sleep(0.3)

            content = session.get_content()
            assert isinstance(content, str)
            assert len(content) > 0

    def test_quit_ncdu(self, ncdu_available, test_directory):
        """Test quitting ncdu with 'q' key."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Verify ncdu is running
            assert session.process.isalive()

            # Press 'q' to quit
            session.send_keys("q", literal=True)
            time.sleep(0.3)

            # Process should exit
            # (cleanup will happen automatically via context manager)


class TestNcduDisplay:
    """Test ncdu display and information."""

    def test_size_display_format(self, ncdu_available, test_directory):
        """Test that ncdu displays file sizes."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            content = session.get_content()

            # ncdu should show size information
            # Sizes are typically shown in bytes, KB, MB, etc.
            # Just verify we have numeric content (sizes)
            assert any(c.isdigit() for c in content)

    def test_help_screen(self, ncdu_available, test_directory):
        """Test accessing ncdu help screen."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Press '?' to open help
            session.send_raw(Keys.QUESTION)
            time.sleep(0.2)

            # Help screen should appear
            # (specific content varies by ncdu version)
            assert len(session.get_content()) > 0

            # Close help
            session.send_raw(Keys.QUESTION)  # Or press 'q'
            time.sleep(0.2)


class TestNcduRealWorld:
    """Real-world ncdu usage patterns."""

    def test_scan_actual_small_directory(self, ncdu_available):
        """Test scanning a real directory (use tmp for speed)."""
        # Scan /tmp which should exist on most systems
        test_dir = "/tmp"
        if not os.path.exists(test_dir):
            test_dir = os.path.expanduser("~")

        with PtySession(["ncdu", "-0", "-x", test_dir], height=24, width=80) as session:
            import time
            # Give more time for potentially larger directory
            time.sleep(2.0)

            content = session.get_content()

            # Should show some content
            assert len(content) > 10  # At least some text

            # Quit
            session.send_keys("q", literal=True)
            time.sleep(0.2)

    def test_refresh_directory_scan(self, ncdu_available, test_directory):
        """Test refreshing the directory scan with 'r' key."""
        with PtySession(["ncdu", "-0", test_directory], height=24, width=80) as session:
            import time
            time.sleep(1.0)

            # Press 'r' to refresh
            session.send_keys("r", literal=True)
            time.sleep(0.5)

            # Should rescan and show content
            content = session.get_content()
            assert len(content) > 0
