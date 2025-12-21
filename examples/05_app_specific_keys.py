"""
Application-Specific Key Bindings - fzf, vim, tmux, lazygit, and more.

ptytest provides specialized key binding classes for popular CLI applications.
These make it easy to write readable tests that use the correct key sequences.

Run with: uv run pytest examples/05_app_specific_keys.py -v
"""

import shutil

import pytest

from ptytest import (
    PtySession,
    Keys,
    FzfKeys,
    VimKeys,
    TmuxKeys,
    LazygitKeys,
    HtopKeys,
    LessKeys,
    NcduKeys,
)


class TestFzfKeys:
    """fzf (fuzzy finder) key bindings."""

    def test_navigation_keys(self):
        """Navigation in fzf."""
        assert FzfKeys.UP == Keys.UP
        assert FzfKeys.DOWN == Keys.DOWN
        assert FzfKeys.CTRL_J == Keys.CTRL_J  # Alternative down
        assert FzfKeys.CTRL_K == Keys.CTRL_K  # Alternative up

    def test_selection_keys(self):
        """Selection and acceptance."""
        assert FzfKeys.TOGGLE == Keys.TAB
        assert FzfKeys.ACCEPT == Keys.ENTER
        assert FzfKeys.TOGGLE_ALL == '\x1ba'  # Alt+A
        assert FzfKeys.SELECT_ALL == '\x1bA'  # Alt+Shift+A

    def test_query_manipulation(self):
        """Query editing."""
        assert FzfKeys.CLEAR_QUERY == Keys.CTRL_U
        assert FzfKeys.BACKWARD_WORD == '\x1bb'

    def test_preview_keys(self):
        """Preview pane controls."""
        assert FzfKeys.TOGGLE_PREVIEW == '\x1bp'  # Alt+P
        assert FzfKeys.PREVIEW_UP == '\x1bk'
        assert FzfKeys.PREVIEW_DOWN == '\x1bj'

    def test_cancel_keys(self):
        """Cancel/quit fzf."""
        assert FzfKeys.ESC == Keys.ESCAPE
        assert FzfKeys.CTRL_C == Keys.CTRL_C

    @pytest.mark.skipif(shutil.which("fzf") is None, reason="fzf not installed")
    def test_fzf_basic_usage(self):
        """Basic fzf interaction."""
        with PtySession(["bash", "-c", "echo -e 'apple\\nbanana\\ncherry' | fzf"]) as session:
            # Wait for fzf to start
            assert session.verify_text_appears(">", timeout=2)

            # Type to filter
            session.send_keys("ban", literal=True)
            assert session.verify_text_appears("banana")

            # Select and exit
            session.send_raw(FzfKeys.ACCEPT)


class TestVimKeys:
    """Vim key bindings and commands."""

    def test_mode_switching(self):
        """Mode switching keys."""
        assert VimKeys.INSERT == 'i'
        assert VimKeys.NORMAL == Keys.ESCAPE
        assert VimKeys.VISUAL == 'v'
        assert VimKeys.VISUAL_LINE == 'V'
        assert VimKeys.COMMAND == ':'

    def test_navigation_chars(self):
        """Character navigation."""
        assert VimKeys.LEFT == 'h'
        assert VimKeys.DOWN == 'j'
        assert VimKeys.UP == 'k'
        assert VimKeys.RIGHT == 'l'

    def test_navigation_words(self):
        """Word navigation."""
        assert VimKeys.WORD_FORWARD == 'w'
        assert VimKeys.WORD_BACK == 'b'
        assert VimKeys.WORD_FORWARD_END == 'e'

    def test_navigation_lines(self):
        """Line navigation."""
        assert VimKeys.LINE_START == '0'
        assert VimKeys.LINE_FIRST_CHAR == '^'
        assert VimKeys.LINE_END == '$'
        assert VimKeys.FIRST_LINE == 'gg'
        assert VimKeys.LAST_LINE == 'G'

    def test_editing_delete(self):
        """Delete operations."""
        assert VimKeys.DELETE_CHAR == 'x'
        assert VimKeys.DELETE_LINE == 'dd'
        assert VimKeys.DELETE_WORD == 'dw'

    def test_editing_change(self):
        """Change operations."""
        assert VimKeys.CHANGE_LINE == 'cc'
        assert VimKeys.CHANGE_WORD == 'cw'

    def test_yank_put(self):
        """Yank and put (copy/paste)."""
        assert VimKeys.YANK_LINE == 'yy'
        assert VimKeys.PUT_AFTER == 'p'
        assert VimKeys.PUT_BEFORE == 'P'

    def test_undo_redo(self):
        """Undo/redo."""
        assert VimKeys.UNDO == 'u'
        assert VimKeys.REDO == Keys.CTRL_R

    def test_search(self):
        """Search commands."""
        assert VimKeys.SEARCH_FORWARD == '/'
        assert VimKeys.SEARCH_BACKWARD == '?'
        assert VimKeys.SEARCH_NEXT == 'n'
        assert VimKeys.SEARCH_PREV == 'N'

    def test_windows(self):
        """Window management."""
        assert VimKeys.WINDOW_PREFIX == Keys.CTRL_W
        assert VimKeys.WINDOW_SPLIT_HORIZONTAL == Keys.CTRL_W + 's'
        assert VimKeys.WINDOW_SPLIT_VERTICAL == Keys.CTRL_W + 'v'

    def test_helper_methods(self):
        """VimKeys helper methods."""
        assert VimKeys.command('wq') == '\x1b:wq\r'
        assert VimKeys.write() == '\x1b:w\r'
        assert VimKeys.quit() == '\x1b:q\r'
        assert VimKeys.quit_force() == '\x1b:q!\r'
        assert VimKeys.search('pattern') == '\x1b/pattern\r'
        assert VimKeys.goto_line(42) == '42G'
        assert VimKeys.repeat(5, 'j') == '5j'


class TestTmuxKeys:
    """tmux key bindings."""

    def test_prefix(self):
        """Default prefix key."""
        assert TmuxKeys.PREFIX == Keys.CTRL_B

    def test_window_keys(self):
        """Window management."""
        assert TmuxKeys.NEW_WINDOW == 'c'
        assert TmuxKeys.NEXT_WINDOW == 'n'
        assert TmuxKeys.PREV_WINDOW == 'p'
        assert TmuxKeys.LAST_WINDOW == 'l'
        assert TmuxKeys.RENAME_WINDOW == ','

    def test_pane_keys(self):
        """Pane management."""
        assert TmuxKeys.SPLIT_HORIZONTAL == '"'
        assert TmuxKeys.SPLIT_VERTICAL == '%'
        assert TmuxKeys.CLOSE_PANE == 'x'
        assert TmuxKeys.NEXT_PANE == 'o'
        assert TmuxKeys.TOGGLE_ZOOM == 'z'

    def test_session_keys(self):
        """Session management."""
        assert TmuxKeys.DETACH == 'd'
        assert TmuxKeys.LIST_SESSIONS == 's'

    def test_copy_mode(self):
        """Copy mode."""
        assert TmuxKeys.COPY_MODE == '['
        assert TmuxKeys.PASTE == ']'

    def test_helper_methods(self):
        """TmuxKeys helper methods."""
        assert TmuxKeys.prefix_key('"') == Keys.CTRL_B + '"'
        assert TmuxKeys.send_prefix() == Keys.CTRL_B


class TestLazygitKeys:
    """lazygit key bindings."""

    def test_vim_navigation(self):
        """Vim-style navigation."""
        assert LazygitKeys.UP == 'k'
        assert LazygitKeys.DOWN == 'j'
        assert LazygitKeys.LEFT == 'h'
        assert LazygitKeys.RIGHT == 'l'

    def test_panel_switching(self):
        """Panel switching with numbers."""
        assert LazygitKeys.STATUS_PANEL == '1'
        assert LazygitKeys.FILES_PANEL == '2'
        assert LazygitKeys.BRANCHES_PANEL == '3'
        assert LazygitKeys.COMMITS_PANEL == '4'
        assert LazygitKeys.STASH_PANEL == '5'

    def test_file_operations(self):
        """File operations."""
        assert LazygitKeys.STAGE_FILE == Keys.SPACE
        assert LazygitKeys.STAGE_ALL == 'a'
        assert LazygitKeys.DISCARD_CHANGES == 'd'
        assert LazygitKeys.EDIT_FILE == 'e'

    def test_commit_operations(self):
        """Commit operations."""
        assert LazygitKeys.COMMIT == 'c'
        assert LazygitKeys.AMEND_COMMIT == 'A'
        assert LazygitKeys.SQUASH == 's'
        assert LazygitKeys.FIXUP == 'f'

    def test_branch_operations(self):
        """Branch operations."""
        assert LazygitKeys.NEW_BRANCH == 'n'
        assert LazygitKeys.DELETE_BRANCH == 'd'
        assert LazygitKeys.CHECKOUT == Keys.SPACE
        assert LazygitKeys.MERGE == 'M'

    def test_remote_operations(self):
        """Remote operations."""
        assert LazygitKeys.FETCH == 'f'
        assert LazygitKeys.PULL == 'p'
        assert LazygitKeys.PUSH == 'P'
        assert LazygitKeys.FORCE_PUSH == 'F'

    def test_navigation(self):
        """Extended navigation."""
        assert LazygitKeys.HOME == 'g'  # First item
        assert LazygitKeys.END == 'G'   # Last item
        assert LazygitKeys.SCROLL_UP == Keys.CTRL_U
        assert LazygitKeys.SCROLL_DOWN == Keys.CTRL_D

    def test_misc(self):
        """Miscellaneous."""
        assert LazygitKeys.QUIT == 'q'
        assert LazygitKeys.HELP == '?'
        assert LazygitKeys.UNDO == 'z'


class TestHtopKeys:
    """htop key bindings."""

    def test_function_keys(self):
        """Function key mappings."""
        assert HtopKeys.HELP == Keys.F1
        assert HtopKeys.SETUP == Keys.F2
        assert HtopKeys.SEARCH == Keys.F3
        assert HtopKeys.FILTER == Keys.F4
        assert HtopKeys.TREE_VIEW == Keys.F5
        assert HtopKeys.SORT == Keys.F6
        assert HtopKeys.KILL == Keys.F9
        assert HtopKeys.QUIT == Keys.F10

    def test_navigation(self):
        """Navigation."""
        assert HtopKeys.UP == Keys.UP
        assert HtopKeys.DOWN == Keys.DOWN
        assert HtopKeys.VI_UP == 'k'
        assert HtopKeys.VI_DOWN == 'j'

    def test_process_management(self):
        """Process management."""
        assert HtopKeys.TAG_PROCESS == Keys.SPACE
        assert HtopKeys.KILL_PROCESS == 'k'

    def test_display(self):
        """Display toggles."""
        assert HtopKeys.TOGGLE_TREE == 't'
        assert HtopKeys.SORT_BY_CPU == 'P'
        assert HtopKeys.SORT_BY_MEMORY == 'M'


class TestLessKeys:
    """less pager key bindings."""

    def test_navigation(self):
        """Navigation."""
        assert LessKeys.DOWN_LINE == 'j'
        assert LessKeys.UP_LINE == 'k'
        assert LessKeys.DOWN_PAGE == Keys.SPACE
        assert LessKeys.UP_PAGE == 'b'
        assert LessKeys.BEGINNING == 'g'
        assert LessKeys.END == 'G'

    def test_search(self):
        """Search."""
        assert LessKeys.SEARCH_FORWARD == '/'
        assert LessKeys.SEARCH_BACKWARD == '?'
        assert LessKeys.NEXT_MATCH == 'n'
        assert LessKeys.PREV_MATCH == 'N'

    def test_misc(self):
        """Miscellaneous."""
        assert LessKeys.HELP == 'h'
        assert LessKeys.QUIT == 'q'


class TestNcduKeys:
    """ncdu (disk usage analyzer) key bindings."""

    def test_navigation(self):
        """Navigation."""
        assert NcduKeys.UP == Keys.UP
        assert NcduKeys.DOWN == Keys.DOWN
        assert NcduKeys.ENTER_DIR == Keys.ENTER
        assert NcduKeys.PARENT_DIR == Keys.LEFT
        assert NcduKeys.VI_UP == 'k'
        assert NcduKeys.VI_DOWN == 'j'

    def test_display(self):
        """Display options."""
        assert NcduKeys.TOGGLE_GRAPH == 'g'
        assert NcduKeys.CYCLE_SORT == 's'
        assert NcduKeys.TOGGLE_HIDDEN == 'e'
        assert NcduKeys.INFO == 'i'

    def test_actions(self):
        """Actions."""
        assert NcduKeys.DELETE == 'd'
        assert NcduKeys.SPAWN_SHELL == 'b'
        assert NcduKeys.REFRESH == 'r'

    def test_misc(self):
        """Miscellaneous."""
        assert NcduKeys.HELP == '?'
        assert NcduKeys.QUIT == 'q'


class TestCombinedExamples:
    """Examples using multiple key classes together."""

    @pytest.mark.skipif(shutil.which("vim") is None, reason="vim not installed")
    def test_vim_editing_session(self):
        """Complete vim editing session."""
        with PtySession(["vim", "-u", "NONE"]) as session:
            # Wait for vim to start
            import time
            time.sleep(0.5)

            # Enter insert mode
            session.send_raw(VimKeys.INSERT)
            session.send_keys("Hello, Vim!", literal=True)

            # Back to normal mode
            session.send_raw(VimKeys.NORMAL)

            # Navigate
            session.send_raw(VimKeys.LINE_START)
            session.send_raw(VimKeys.WORD_FORWARD)

            # Quit without saving
            session.send_raw(VimKeys.quit_force())
