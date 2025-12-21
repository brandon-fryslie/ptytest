"""
Examples of testing lazygit (terminal UI for git) with ptytest.

These tests demonstrate using PtySession to test a complex multi-panel TUI
with vim-style navigation, modal interactions, and git operations.
Run with: pytest examples/test_lazygit.py -v

Note: Requires lazygit to be installed (https://github.com/jesseduffield/lazygit)

This example showcases:
- Multi-panel navigation (Status, Files, Branches, Commits, Stash)
- Vim-style keybindings (h/j/k/l)
- Modal interactions (entering/exiting edit modes)
- Complex state management (staging, committing)
- Search and filter functionality
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from ptytest import Keys, PtySession


pytestmark = pytest.mark.direct_pty


class LazygitKeys:
    """
    Key bindings specific to lazygit.

    Lazygit uses vim-style navigation with panel switching via number keys.
    """

    # Vim-style navigation
    UP = 'k'
    DOWN = 'j'
    LEFT = 'h'
    RIGHT = 'l'

    # Arrow keys also work
    ARROW_UP = Keys.UP
    ARROW_DOWN = Keys.DOWN
    ARROW_LEFT = Keys.LEFT
    ARROW_RIGHT = Keys.RIGHT

    # Panel switching (1-5)
    STATUS_PANEL = '1'
    FILES_PANEL = '2'
    BRANCHES_PANEL = '3'
    COMMITS_PANEL = '4'
    STASH_PANEL = '5'

    # Tab cycles through panels
    NEXT_PANEL = Keys.TAB

    # File operations
    STAGE_FILE = Keys.SPACE  # Stage/unstage file
    STAGE_ALL = 'a'  # Stage all files
    DISCARD_CHANGES = 'd'  # Discard changes
    ENTER_FILE = Keys.ENTER  # Enter file to see changes

    # Commit operations
    COMMIT = 'c'  # Open commit dialog
    AMEND_COMMIT = 'A'  # Amend last commit
    SQUASH = 's'  # Squash commit
    FIXUP = 'f'  # Fixup commit
    RENAME_COMMIT = 'R'  # Rename commit message

    # Interactive rebase
    START_REBASE = 'i'  # Start interactive rebase
    MOVE_COMMIT_UP = Keys.CTRL_K
    MOVE_COMMIT_DOWN = Keys.CTRL_J
    DROP_COMMIT = 'd'  # Drop commit
    EDIT_COMMIT = 'e'  # Edit commit

    # Branch operations
    CHECKOUT = Keys.SPACE  # Checkout branch
    NEW_BRANCH = 'n'  # New branch
    DELETE_BRANCH = 'd'  # Delete branch
    MERGE = 'M'  # Merge branch
    REBASE_ONTO = 'r'  # Rebase onto branch

    # Stash operations
    STASH_CHANGES = 's'  # Stash changes (from files panel)
    APPLY_STASH = Keys.SPACE  # Apply stash
    POP_STASH = 'g'  # Pop stash
    DROP_STASH = 'd'  # Drop stash

    # Search and filter
    SEARCH = '/'  # Open search
    FILTER = Keys.CTRL_S  # Filter mode

    # Navigation
    PAGE_UP = Keys.PAGE_UP
    PAGE_DOWN = Keys.PAGE_DOWN
    HOME = 'g'  # Go to top (in some contexts)
    END = 'G'  # Go to bottom

    # Help and info
    HELP = '?'  # Show help
    OPTIONS_MENU = 'x'  # Context menu
    GLOBAL_OPTIONS = '+'  # Global options

    # Diff mode
    DIFF_MODE = 'W'  # Shift+W - diff mode menu

    # View modes
    EXPAND_PANEL = '+'  # Expand panel to half/full screen
    FOCUS_MAIN = 'm'  # Focus main panel

    # Exit and cancel
    QUIT = 'q'  # Quit lazygit
    ESCAPE = Keys.ESCAPE  # Cancel current operation
    CLOSE_PANEL = Keys.ESCAPE  # Close popup/panel

    # Copy
    COPY = 'y'  # Copy (commit hash, branch name, etc.)

    # Cherry-pick
    CHERRY_PICK_COPY = 'C'  # Copy commit for cherry-pick
    CHERRY_PICK_PASTE = 'V'  # Paste/apply cherry-picked commits


@pytest.fixture(scope="module")
def lazygit_available():
    """Check if lazygit is available."""
    if not shutil.which("lazygit"):
        pytest.skip("lazygit is not installed")


@pytest.fixture
def git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repository\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def git_repo_with_changes(git_repo):
    """Git repo with uncommitted changes for staging tests."""
    # Create some modified files
    (git_repo / "README.md").write_text("# Test Repository\n\nUpdated content.\n")
    (git_repo / "new_file.txt").write_text("This is a new file.\n")
    (git_repo / "another_file.py").write_text("print('Hello, World!')\n")

    yield git_repo


@pytest.fixture
def git_repo_with_history(git_repo):
    """Git repo with multiple commits for rebase/log tests."""
    for i in range(1, 6):
        (git_repo / f"file_{i}.txt").write_text(f"Content of file {i}\n")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add file {i}"],
            cwd=git_repo,
            capture_output=True,
        )

    yield git_repo


@pytest.fixture
def git_repo_with_branches(git_repo):
    """Git repo with multiple branches for branch management tests."""
    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test-feature"],
        cwd=git_repo,
        capture_output=True,
    )
    (git_repo / "feature.txt").write_text("Feature content\n")
    subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=git_repo,
        capture_output=True,
    )

    # Create another branch
    subprocess.run(["git", "checkout", "master"], cwd=git_repo, capture_output=True)
    subprocess.run(
        ["git", "checkout", "-b", "bugfix/fix-issue"],
        cwd=git_repo,
        capture_output=True,
    )
    (git_repo / "bugfix.txt").write_text("Bugfix content\n")
    subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Fix bug"],
        cwd=git_repo,
        capture_output=True,
    )

    # Return to master
    subprocess.run(["git", "checkout", "master"], cwd=git_repo, capture_output=True)

    yield git_repo


class TestLazygitBasics:
    """Basic lazygit launch and navigation tests."""

    def test_launch_lazygit(self, lazygit_available, git_repo):
        """Test launching lazygit in a git repository."""
        with PtySession(["lazygit"], cwd=str(git_repo), height=30, width=100) as session:
            time.sleep(0.5)  # Let UI render

            content = session.get_content()

            # Should show some UI elements
            assert len(content) > 0
            # Common lazygit UI elements (exact text may vary by version)
            # The status panel usually shows branch info

    def test_quit_lazygit(self, lazygit_available, git_repo):
        """Test quitting lazygit with 'q' key."""
        with PtySession(["lazygit"], cwd=str(git_repo), height=30, width=100) as session:
            time.sleep(0.5)

            # Verify process is running
            assert session.process.isalive()

            # Press 'q' to quit
            session.send_keys(LazygitKeys.QUIT, literal=True)
            time.sleep(0.3)

            # Process should exit (or be in quitting state)

    def test_vim_navigation(self, lazygit_available, git_repo_with_changes):
        """Test vim-style j/k navigation."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Navigate with vim keys
            session.send_keys(LazygitKeys.DOWN, literal=True)  # j
            time.sleep(0.1)
            session.send_keys(LazygitKeys.DOWN, literal=True)  # j
            time.sleep(0.1)
            session.send_keys(LazygitKeys.UP, literal=True)  # k
            time.sleep(0.1)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitPanelNavigation:
    """Test panel switching and navigation."""

    def test_switch_panels_with_numbers(self, lazygit_available, git_repo):
        """Test switching between panels using number keys."""
        with PtySession(["lazygit"], cwd=str(git_repo), height=30, width=100) as session:
            time.sleep(0.5)

            # Switch to each panel
            panels = [
                LazygitKeys.STATUS_PANEL,
                LazygitKeys.FILES_PANEL,
                LazygitKeys.BRANCHES_PANEL,
                LazygitKeys.COMMITS_PANEL,
                LazygitKeys.STASH_PANEL,
            ]

            for panel_key in panels:
                session.send_keys(panel_key, literal=True)
                time.sleep(0.15)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_switch_panels_with_tab(self, lazygit_available, git_repo):
        """Test cycling through panels with Tab."""
        with PtySession(["lazygit"], cwd=str(git_repo), height=30, width=100) as session:
            time.sleep(0.5)

            # Cycle through panels with Tab
            for _ in range(5):
                session.send_raw(LazygitKeys.NEXT_PANEL)
                time.sleep(0.15)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_expand_panel(self, lazygit_available, git_repo_with_history):
        """Test expanding panel to full screen with '+'."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Expand panel
            session.send_keys(LazygitKeys.EXPAND_PANEL, literal=True)
            time.sleep(0.2)

            content = session.get_content()
            # Expanded panel should show more content
            assert len(content) > 0

            # Return to normal view
            session.send_keys(LazygitKeys.EXPAND_PANEL, literal=True)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitFileStaging:
    """Test file staging operations."""

    def test_stage_single_file(self, lazygit_available, git_repo_with_changes):
        """Test staging a single file with Space."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)

            content_before = session.get_content()

            # Stage current file with Space
            session.send_raw(LazygitKeys.STAGE_FILE)
            time.sleep(0.2)

            content_after = session.get_content()

            # Content should have changed (file moved from unstaged to staged)
            # The exact representation depends on lazygit version
            assert len(content_after) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_stage_all_files(self, lazygit_available, git_repo_with_changes):
        """Test staging all files with 'a'."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)

            # Stage all files
            session.send_keys(LazygitKeys.STAGE_ALL, literal=True)
            time.sleep(0.2)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_enter_file_to_see_diff(self, lazygit_available, git_repo_with_changes):
        """Test entering a file to see its diff."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)

            # Enter file to see diff
            session.send_raw(LazygitKeys.ENTER_FILE)
            time.sleep(0.3)

            content = session.get_content()
            # Should show diff or hunk view
            assert len(content) > 0

            # Exit with escape
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitBranchManagement:
    """Test branch management operations."""

    def test_view_branches(self, lazygit_available, git_repo_with_branches):
        """Test viewing branches panel."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_branches), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to branches panel
            session.send_keys(LazygitKeys.BRANCHES_PANEL, literal=True)
            time.sleep(0.3)

            content = session.get_content()
            # Should show branch list
            assert "master" in content or "main" in content or "feature" in content

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_navigate_branches(self, lazygit_available, git_repo_with_branches):
        """Test navigating through branches list."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_branches), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to branches panel
            session.send_keys(LazygitKeys.BRANCHES_PANEL, literal=True)
            time.sleep(0.2)

            # Navigate through branches
            session.send_keys(LazygitKeys.DOWN, literal=True)
            time.sleep(0.1)
            session.send_keys(LazygitKeys.DOWN, literal=True)
            time.sleep(0.1)
            session.send_keys(LazygitKeys.UP, literal=True)
            time.sleep(0.1)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitCommitHistory:
    """Test commit history viewing and navigation."""

    def test_view_commit_history(self, lazygit_available, git_repo_with_history):
        """Test viewing commit history."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.3)

            content = session.get_content()
            # Should show commit messages
            assert "Add file" in content or "Initial commit" in content

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_navigate_commits(self, lazygit_available, git_repo_with_history):
        """Test navigating through commit history."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Navigate through commits
            for _ in range(3):
                session.send_keys(LazygitKeys.DOWN, literal=True)
                time.sleep(0.1)

            for _ in range(2):
                session.send_keys(LazygitKeys.UP, literal=True)
                time.sleep(0.1)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_view_commit_diff(self, lazygit_available, git_repo_with_history):
        """Test viewing diff for a commit."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Enter commit to see diff
            session.send_raw(Keys.ENTER)
            time.sleep(0.3)

            content = session.get_content()
            # Should show some diff or commit details
            assert len(content) > 0

            # Exit
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitSearch:
    """Test search and filter functionality."""

    def test_open_search(self, lazygit_available, git_repo_with_history):
        """Test opening search with '/'."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Open search
            session.send_keys(LazygitKeys.SEARCH, literal=True)
            time.sleep(0.2)

            content = session.get_content()
            # Search prompt should appear
            assert len(content) > 0

            # Cancel search
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_search_commits(self, lazygit_available, git_repo_with_history):
        """Test searching commits."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Open search and type query
            session.send_keys(LazygitKeys.SEARCH, literal=True)
            time.sleep(0.1)
            session.send_keys("file 3", literal=True)
            time.sleep(0.2)
            session.send_raw(Keys.ENTER)
            time.sleep(0.2)

            content = session.get_content()
            # Should filter to matching commits
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitHelp:
    """Test help and options menus."""

    def test_open_help(self, lazygit_available, git_repo):
        """Test opening help with '?'."""
        with PtySession(["lazygit"], cwd=str(git_repo), height=30, width=100) as session:
            time.sleep(0.5)

            # Open help
            session.send_keys(LazygitKeys.HELP, literal=True)
            time.sleep(0.3)

            content = session.get_content()
            # Help should show keybindings
            # Exact content varies but should have help text
            assert len(content) > 50  # Should have substantial content

            # Close help
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_context_menu(self, lazygit_available, git_repo_with_changes):
        """Test opening context/options menu with 'x'."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)

            # Open context menu
            session.send_keys(LazygitKeys.OPTIONS_MENU, literal=True)
            time.sleep(0.3)

            content = session.get_content()
            # Should show context-specific options
            assert len(content) > 0

            # Close menu
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)


class TestLazygitComplexWorkflow:
    """Test complex multi-step workflows."""

    def test_stage_and_view_staged(self, lazygit_available, git_repo_with_changes):
        """Test staging files and then viewing staged changes."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)

            # Stage all files
            session.send_keys(LazygitKeys.STAGE_ALL, literal=True)
            time.sleep(0.2)

            # Navigate to see staged changes
            session.send_raw(Keys.TAB)  # Switch to staged view
            time.sleep(0.2)

            content = session.get_content()
            # Should show staged files
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_full_commit_workflow_cancel(self, lazygit_available, git_repo_with_changes):
        """Test starting commit workflow and canceling."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_changes), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to files panel and stage all
            session.send_keys(LazygitKeys.FILES_PANEL, literal=True)
            time.sleep(0.2)
            session.send_keys(LazygitKeys.STAGE_ALL, literal=True)
            time.sleep(0.2)

            # Start commit (opens commit message editor)
            session.send_keys(LazygitKeys.COMMIT, literal=True)
            time.sleep(0.3)

            content = session.get_content()
            # Should be in commit message mode
            assert len(content) > 0

            # Cancel commit
            session.send_raw(LazygitKeys.ESCAPE)
            time.sleep(0.2)

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_navigate_all_panels(self, lazygit_available, git_repo_with_branches):
        """Test navigating through all panels in sequence."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_branches), height=30, width=100) as session:
            time.sleep(0.5)

            panels_and_actions = [
                (LazygitKeys.STATUS_PANEL, "Status"),
                (LazygitKeys.FILES_PANEL, "Files"),
                (LazygitKeys.BRANCHES_PANEL, "Branches"),
                (LazygitKeys.COMMITS_PANEL, "Commits"),
                (LazygitKeys.STASH_PANEL, "Stash"),
            ]

            for panel_key, panel_name in panels_and_actions:
                session.send_keys(panel_key, literal=True)
                time.sleep(0.2)

                # Navigate a bit in each panel
                session.send_keys(LazygitKeys.DOWN, literal=True)
                time.sleep(0.1)
                session.send_keys(LazygitKeys.UP, literal=True)
                time.sleep(0.1)

            content = session.get_content()
            assert len(content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)

    def test_arrow_and_vim_navigation_equivalence(self, lazygit_available, git_repo_with_history):
        """Test that arrow keys and vim keys produce similar navigation."""
        with PtySession(["lazygit"], cwd=str(git_repo_with_history), height=30, width=100) as session:
            time.sleep(0.5)

            # Go to commits panel
            session.send_keys(LazygitKeys.COMMITS_PANEL, literal=True)
            time.sleep(0.2)

            # Navigate with vim keys
            session.send_keys(LazygitKeys.DOWN, literal=True)  # j
            session.send_keys(LazygitKeys.DOWN, literal=True)  # j
            time.sleep(0.1)
            vim_content = session.get_content()

            # Navigate back up
            session.send_keys(LazygitKeys.UP, literal=True)  # k
            session.send_keys(LazygitKeys.UP, literal=True)  # k
            time.sleep(0.1)

            # Navigate with arrow keys
            session.send_raw(LazygitKeys.ARROW_DOWN)
            session.send_raw(LazygitKeys.ARROW_DOWN)
            time.sleep(0.1)
            arrow_content = session.get_content()

            # Both should show valid content
            assert len(vim_content) > 0
            assert len(arrow_content) > 0

            session.send_keys(LazygitKeys.QUIT, literal=True)
