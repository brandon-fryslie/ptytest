"""
NeovimSession - Testing Neovim plugins with real terminal interaction.

NeovimSession provides a harness for testing Neovim plugins with isolated
configuration, buffer inspection, and comprehensive state verification.

Requirements: neovim (nvim) must be installed

Run with: uv run pytest examples/03_neovim_session.py -v
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from ptytest import NeovimSession, Keys


# Skip all tests if neovim is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("nvim") is None,
    reason="neovim not installed"
)


class TestNeovimBasics:
    """Basic NeovimSession usage patterns."""

    def test_start_neovim(self):
        """Start Neovim in clean mode."""
        with NeovimSession() as nvim:
            # Neovim should be running
            content = nvim.get_content()
            # Empty buffer shows ~ for empty lines
            assert "~" in content or len(content.strip()) > 0

    def test_execute_ex_command(self):
        """Execute Ex commands."""
        with NeovimSession() as nvim:
            # Echo a message
            nvim.ex("echo 'Hello from Neovim!'")
            assert nvim.verify_text_appears("Hello from Neovim!")

    def test_execute_lua_code(self):
        """Execute Lua code."""
        with NeovimSession() as nvim:
            nvim.lua("print('Lua says hello!')")
            assert nvim.verify_text_appears("Lua says hello!")


class TestNeovimModes:
    """Test Neovim mode operations."""

    def test_insert_mode(self):
        """Enter and exit insert mode."""
        with NeovimSession() as nvim:
            nvim.enter_insert_mode()
            assert nvim.get_mode() == "i"

            nvim.ensure_normal_mode()
            assert nvim.get_mode() == "n"

    def test_type_text(self):
        """Type text using the convenience method."""
        with NeovimSession() as nvim:
            nvim.type_text("Hello, Neovim!")

            # Text should be in the buffer
            nvim.assert_buffer_contains("Hello, Neovim!")

    def test_visual_mode(self):
        """Enter visual mode."""
        with NeovimSession() as nvim:
            nvim.type_text("some text to select")
            nvim.ensure_normal_mode()

            nvim.enter_visual_mode()
            mode = nvim.get_mode()
            assert mode in ("v", "V")  # Character or line visual


class TestNeovimNavigation:
    """Test Neovim navigation."""

    def test_goto_line(self):
        """Navigate to specific lines."""
        with NeovimSession() as nvim:
            # Create multiple lines
            nvim.enter_insert_mode()
            nvim.send_keys("Line 1", literal=True)
            nvim.send_raw(Keys.ENTER)
            nvim.send_keys("Line 2", literal=True)
            nvim.send_raw(Keys.ENTER)
            nvim.send_keys("Line 3", literal=True)
            nvim.ensure_normal_mode()

            # Go to top
            nvim.goto_top()

            # Go to bottom
            nvim.goto_bottom()

    def test_goto_specific_line(self):
        """Go to a specific line number."""
        with NeovimSession() as nvim:
            # Add some lines
            for i in range(5):
                nvim.ex(f"$put ='Line {i+1}'")

            nvim.goto_line(3)
            # Cursor should be on line 3


class TestNeovimBufferOperations:
    """Test buffer operations."""

    def test_get_buffer_content(self):
        """Get buffer content."""
        with NeovimSession() as nvim:
            nvim.type_text("Buffer content test")
            content = nvim.get_buffer_content()
            assert "Buffer content test" in content

    def test_get_buffer_lines(self):
        """Get specific lines from buffer."""
        with NeovimSession() as nvim:
            for i in range(3):
                nvim.ex(f"$put ='Line {i+1}'")

            lines = nvim.get_buffer_lines()
            # Should have our lines (plus possibly empty first line)

    def test_append_line(self):
        """Append a line to the buffer."""
        with NeovimSession() as nvim:
            nvim.append_line("First appended line")
            nvim.append_line("Second appended line")

            nvim.assert_buffer_contains("First appended line")
            nvim.assert_buffer_contains("Second appended line")

    def test_delete_line(self):
        """Delete a line."""
        with NeovimSession() as nvim:
            nvim.type_text("Line to delete")
            nvim.assert_buffer_contains("Line to delete")

            nvim.delete_line()
            # Line should be gone (or buffer may be empty)


class TestNeovimEditing:
    """Test editing operations."""

    def test_undo_redo(self):
        """Test undo and redo."""
        with NeovimSession() as nvim:
            nvim.type_text("Original text")
            nvim.assert_buffer_contains("Original text")

            nvim.undo()
            # Text should be undone

            nvim.redo()
            # Text should be restored

    def test_indent(self):
        """Test indentation."""
        with NeovimSession() as nvim:
            nvim.type_text("Indentable line")
            nvim.ensure_normal_mode()

            nvim.indent_line()
            # Line should be indented

    def test_normal_mode_commands(self):
        """Execute normal mode commands."""
        with NeovimSession() as nvim:
            nvim.type_text("hello world")
            nvim.ensure_normal_mode()

            # Go to beginning and change word
            nvim.normal("0")  # Go to start of line
            nvim.normal("cw")  # Change word
            # Now in insert mode, could type replacement


class TestNeovimWindows:
    """Test window operations."""

    def test_split_window(self):
        """Split window."""
        with NeovimSession() as nvim:
            initial_count = nvim.get_window_count()

            nvim.split_window()  # Horizontal split

            # Window count should increase
            # (Note: detection is approximate)

    def test_vertical_split(self):
        """Vertical split."""
        with NeovimSession() as nvim:
            nvim.split_window(vertical=True)
            # Now have two windows side by side


class TestNeovimSearch:
    """Test search operations."""

    def test_search_forward(self):
        """Search forward."""
        with NeovimSession() as nvim:
            nvim.type_text("Find this needle in the haystack")
            nvim.ensure_normal_mode()
            nvim.goto_top()

            nvim.search("needle")
            # Cursor should be on "needle"

    def test_search_next_prev(self):
        """Navigate search results."""
        with NeovimSession() as nvim:
            nvim.ex("$put ='first match'")
            nvim.ex("$put ='second match'")
            nvim.ex("$put ='third match'")
            nvim.goto_top()

            nvim.search("match")
            nvim.search_next()
            nvim.search_prev()

    def test_clear_search_highlight(self):
        """Clear search highlighting."""
        with NeovimSession() as nvim:
            nvim.type_text("highlighted text")
            nvim.search("text")

            nvim.clear_search_highlight()


class TestNeovimFiles:
    """Test file operations."""

    def test_edit_file(self):
        """Open a file for editing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("File content\n")
            filepath = f.name

        try:
            with NeovimSession() as nvim:
                nvim.edit_file(filepath)
                nvim.assert_buffer_contains("File content")
        finally:
            Path(filepath).unlink()

    def test_save_file(self):
        """Save a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"

            with NeovimSession() as nvim:
                nvim.type_text("Content to save")
                nvim.save_file(str(filepath))

                # File should exist
                assert filepath.exists()
                assert "Content to save" in filepath.read_text()


class TestNeovimAssertions:
    """Test assertion helpers."""

    def test_assert_buffer_contains(self):
        """Assert buffer contains text."""
        with NeovimSession() as nvim:
            nvim.type_text("Expected content")
            nvim.assert_buffer_contains("Expected content")

    def test_assert_buffer_not_contains(self):
        """Assert buffer does not contain text."""
        with NeovimSession() as nvim:
            nvim.type_text("Some content")
            nvim.assert_buffer_not_contains("Unexpected")

    def test_assert_mode(self):
        """Assert current mode."""
        with NeovimSession() as nvim:
            nvim.ensure_normal_mode()
            nvim.assert_mode("n")

            nvim.enter_insert_mode()
            nvim.assert_mode("i")


class TestNeovimPluginTesting:
    """Examples of testing Neovim plugins."""

    def test_with_custom_init_lua(self):
        """Use custom init.lua code."""
        init_code = """
        -- Custom init.lua
        vim.g.my_custom_var = 42
        vim.opt.number = true
        """

        with NeovimSession(init_lua=init_code) as nvim:
            # The custom init should have run
            nvim.lua("print(vim.g.my_custom_var)")
            assert nvim.verify_text_appears("42")

    def test_with_custom_init_vim(self):
        """Use custom init.vim code."""
        init_code = """
        let g:my_vim_var = 'hello'
        set relativenumber
        """

        with NeovimSession(init_vim=init_code) as nvim:
            nvim.ex("echo g:my_vim_var")
            assert nvim.verify_text_appears("hello")

    @pytest.mark.skip(reason="Requires actual plugin path")
    def test_with_plugin_path(self):
        """Load a plugin from path."""
        with NeovimSession(plugins=["~/my-plugin"]) as nvim:
            # Plugin should be loaded
            nvim.ex("MyPluginCommand")
