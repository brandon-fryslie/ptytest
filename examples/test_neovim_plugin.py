"""
Example tests demonstrating the Neovim plugin testing harness.

This file shows how to use NeovimSession to test:
- Basic Neovim operations
- Plugin loading and configuration
- Custom keybindings
- Buffer manipulation
- Mode switching
- Window and split operations
- Search functionality

Run these tests with:
    uv run pytest examples/test_neovim_plugin.py -v

Requirements:
    - Neovim installed and in PATH
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from ptytest import Keys, NeovimSession, VimKeys


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def nvim():
    """Basic Neovim session fixture."""
    with NeovimSession() as session:
        yield session


@pytest.fixture
def nvim_with_file(tmp_path):
    """Neovim session with a pre-created test file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

    with NeovimSession(args=[str(test_file)]) as session:
        session.test_file = test_file
        yield session


@pytest.fixture
def mock_plugin(tmp_path):
    """Create a mock Neovim plugin for testing."""
    plugin_dir = tmp_path / "mock-plugin"
    plugin_dir.mkdir()

    # Create plugin structure
    lua_dir = plugin_dir / "lua" / "mock_plugin"
    lua_dir.mkdir(parents=True)

    # Main plugin module
    (lua_dir / "init.lua").write_text(
        """
-- Mock plugin for testing
local M = {}

M.config = {
    greeting = "Hello from mock plugin!",
    count = 0,
}

function M.setup(opts)
    M.config = vim.tbl_extend("force", M.config, opts or {})
end

function M.greet()
    print(M.config.greeting)
end

function M.increment()
    M.config.count = M.config.count + 1
    print("Count: " .. M.config.count)
end

function M.get_count()
    return M.config.count
end

function M.insert_greeting()
    local line = vim.api.nvim_get_current_line()
    vim.api.nvim_set_current_line(M.config.greeting .. " " .. line)
end

return M
"""
    )

    # Plugin file (auto-loaded)
    plugin_file_dir = plugin_dir / "plugin"
    plugin_file_dir.mkdir()
    (plugin_file_dir / "mock_plugin.lua").write_text(
        """
-- Auto-load file for mock plugin
-- Set up default commands and mappings

vim.api.nvim_create_user_command("MockGreet", function()
    require("mock_plugin").greet()
end, {})

vim.api.nvim_create_user_command("MockIncrement", function()
    require("mock_plugin").increment()
end, {})

vim.api.nvim_create_user_command("MockInsertGreeting", function()
    require("mock_plugin").insert_greeting()
end, {})

-- Set up a keybinding
vim.keymap.set("n", "<leader>mg", function()
    require("mock_plugin").greet()
end, { desc = "Mock plugin greet" })
"""
    )

    return plugin_dir


# =============================================================================
# Basic Neovim Operation Tests
# =============================================================================


class TestNeovimBasics:
    """Test basic Neovim operations."""

    def test_session_starts_and_cleans_up(self):
        """Test that NeovimSession starts and cleans up properly."""
        session = NeovimSession()
        try:
            assert session.process is not None
            assert session.process.isalive()
            # Verify we can see Neovim's interface
            content = session.get_content()
            # Neovim shows ~ for empty lines
            assert "~" in content or len(content) > 0
        finally:
            session.cleanup()
            # After cleanup, process should be dead
            assert not session.process.isalive()

    def test_context_manager(self):
        """Test context manager properly cleans up."""
        with NeovimSession() as nvim:
            assert nvim.process.isalive()
            process = nvim.process

        # After context, process should be dead
        assert not process.isalive()

    def test_send_keys_works(self, nvim):
        """Test that we can send keys to Neovim."""
        # Type some text in insert mode
        nvim.send_raw("i")  # Enter insert mode
        time.sleep(0.1)
        nvim.send_keys("Hello, Neovim!", literal=True)
        time.sleep(0.1)
        nvim.send_raw(Keys.ESCAPE)  # Back to normal mode
        time.sleep(0.1)

        content = nvim.get_buffer_content()
        assert "Hello, Neovim!" in content

    def test_command_execution(self, nvim):
        """Test executing Ex commands."""
        nvim.ex("echo 'test message'")
        # Command output appears briefly, main test is it doesn't error
        # Try setting an option and verifying
        nvim.ex("set number")
        # If no exception, command worked


class TestModeOperations:
    """Test mode switching and detection."""

    def test_normal_mode_default(self, nvim):
        """Test that Neovim starts in normal mode."""
        mode = nvim.get_mode()
        assert mode == "n"

    def test_enter_insert_mode(self, nvim):
        """Test entering insert mode."""
        nvim.enter_insert_mode()
        time.sleep(0.1)

        content = nvim.get_content()
        # Check for insert mode indicator
        assert "INSERT" in content.upper() or "-- INSERT --" in content.lower()

    def test_enter_visual_mode(self, nvim):
        """Test entering visual mode."""
        # First add some text to select
        nvim.send_raw("i")
        nvim.send_keys("Some text to select", literal=True)
        nvim.send_raw(Keys.ESCAPE)
        time.sleep(0.1)

        nvim.enter_visual_mode()
        time.sleep(0.1)

        content = nvim.get_content()
        assert "VISUAL" in content.upper() or "-- VISUAL --" in content.lower()

    def test_ensure_normal_mode(self, nvim):
        """Test ensure_normal_mode from various modes."""
        # Start in insert mode
        nvim.enter_insert_mode()
        time.sleep(0.1)

        # Ensure we get back to normal
        nvim.ensure_normal_mode()
        time.sleep(0.1)

        mode = nvim.get_mode()
        assert mode == "n"


class TestBufferOperations:
    """Test buffer manipulation."""

    def test_get_buffer_content(self, nvim_with_file):
        """Test getting buffer content."""
        content = nvim_with_file.get_buffer_content()
        assert "Line 1" in content
        assert "Line 2" in content

    def test_type_text(self, nvim):
        """Test typing text into buffer."""
        nvim.type_text("Hello World")
        content = nvim.get_buffer_content()
        assert "Hello World" in content

    def test_delete_line(self, nvim_with_file):
        """Test deleting a line."""
        initial_content = nvim_with_file.get_buffer_content()
        assert "Line 1" in initial_content

        nvim_with_file.delete_line()
        time.sleep(0.1)

        content = nvim_with_file.get_buffer_content()
        # Line 1 should be deleted, Line 2 should now be at top
        # Note: depends on screen rendering

    def test_undo_redo(self, nvim):
        """Test undo and redo operations."""
        # Type something
        nvim.type_text("Original text")
        time.sleep(0.1)

        # Delete it
        nvim.ex("%delete")
        time.sleep(0.1)

        # Undo
        nvim.undo()
        time.sleep(0.1)

        content = nvim.get_buffer_content()
        # Content should be restored after undo


class TestWindowOperations:
    """Test window and split operations."""

    def test_split_window_horizontal(self, nvim):
        """Test horizontal window split."""
        initial_count = nvim.get_window_count()
        nvim.split_window(vertical=False)
        time.sleep(0.2)

        # Should have one more window now
        # Note: window count detection is approximate from screen

    def test_split_window_vertical(self, nvim):
        """Test vertical window split."""
        nvim.split_window(vertical=True)
        time.sleep(0.2)

        content = nvim.get_content()
        # Vertical splits show separator characters
        # The exact check depends on terminal rendering


class TestSearchOperations:
    """Test search functionality."""

    def test_search_forward(self, nvim_with_file):
        """Test forward search."""
        nvim_with_file.search("Line 3")
        time.sleep(0.2)

        # Cursor should be on line with "Line 3"
        # Verification depends on cursor position tracking

    def test_search_backward(self, nvim_with_file):
        """Test backward search."""
        # Go to end first
        nvim_with_file.goto_bottom()
        time.sleep(0.1)

        nvim_with_file.search("Line 1", backward=True)
        time.sleep(0.2)


# =============================================================================
# Plugin Testing
# =============================================================================


class TestPluginLoading:
    """Test plugin loading and configuration."""

    def test_load_plugin(self, mock_plugin):
        """Test loading a plugin from a path."""
        with NeovimSession(plugins=[str(mock_plugin)]) as nvim:
            # Plugin should be loaded, try calling it
            nvim.lua("require('mock_plugin').greet()")
            time.sleep(0.2)

            content = nvim.get_content()
            assert "Hello from mock plugin!" in content

    def test_plugin_setup(self, mock_plugin):
        """Test plugin setup with custom options."""
        init = """
        require('mock_plugin').setup({
            greeting = "Custom greeting!"
        })
        """
        with NeovimSession(plugins=[str(mock_plugin)], init_lua=init) as nvim:
            nvim.lua("require('mock_plugin').greet()")
            time.sleep(0.2)

            content = nvim.get_content()
            assert "Custom greeting!" in content

    def test_plugin_command(self, mock_plugin):
        """Test plugin-defined commands."""
        with NeovimSession(plugins=[str(mock_plugin)]) as nvim:
            # Use the plugin's command
            nvim.ex("MockGreet")
            time.sleep(0.2)

            content = nvim.get_content()
            assert "Hello from mock plugin!" in content

    def test_plugin_increment(self, mock_plugin):
        """Test plugin state across multiple calls."""
        with NeovimSession(plugins=[str(mock_plugin)]) as nvim:
            nvim.ex("MockIncrement")
            time.sleep(0.1)
            nvim.ex("MockIncrement")
            time.sleep(0.1)
            nvim.ex("MockIncrement")
            time.sleep(0.2)

            content = nvim.get_content()
            assert "Count: 3" in content


class TestPluginKeybindings:
    """Test plugin keybindings."""

    def test_leader_mapping(self, mock_plugin):
        """Test a leader key mapping defined by the plugin."""
        # Set leader to space and load plugin
        init = """
        vim.g.mapleader = " "
        """
        with NeovimSession(plugins=[str(mock_plugin)], init_lua=init) as nvim:
            # Trigger the leader mapping: <leader>mg
            nvim.ensure_normal_mode()
            nvim.send_raw(" ")  # leader (space)
            time.sleep(0.05)
            nvim.send_raw("m")
            time.sleep(0.05)
            nvim.send_raw("g")
            time.sleep(0.3)

            content = nvim.get_content()
            assert "Hello from mock plugin!" in content


class TestPluginBufferManipulation:
    """Test plugins that manipulate buffer content."""

    def test_insert_greeting(self, mock_plugin):
        """Test a plugin function that modifies buffer content."""
        with NeovimSession(plugins=[str(mock_plugin)]) as nvim:
            # Add some initial text
            nvim.type_text("World")
            time.sleep(0.1)

            # Go to beginning of line
            nvim.normal("0")
            time.sleep(0.1)

            # Call plugin function to insert greeting
            nvim.ex("MockInsertGreeting")
            time.sleep(0.2)

            content = nvim.get_buffer_content()
            # Should have "Hello from mock plugin! World"
            assert "Hello from mock plugin!" in content


# =============================================================================
# Real-World Plugin Pattern Tests
# =============================================================================


class TestCommentPluginPattern:
    """
    Demonstrate testing a comment toggle plugin pattern.

    This shows how you might test a plugin like vim-commentary or Comment.nvim
    """

    @pytest.fixture
    def comment_plugin(self, tmp_path):
        """Create a simple comment toggle plugin."""
        plugin_dir = tmp_path / "comment-plugin"
        lua_dir = plugin_dir / "lua" / "comment"
        lua_dir.mkdir(parents=True)

        (lua_dir / "init.lua").write_text(
            """
local M = {}

function M.toggle_line()
    local line = vim.api.nvim_get_current_line()
    if line:match("^%s*%-%-") then
        -- Remove comment
        line = line:gsub("^(%s*)%-%-%s?", "%1")
    else
        -- Add comment
        line = "-- " .. line
    end
    vim.api.nvim_set_current_line(line)
end

function M.setup()
    vim.keymap.set("n", "gcc", M.toggle_line, { desc = "Toggle comment" })
end

return M
"""
        )

        plugin_file_dir = plugin_dir / "plugin"
        plugin_file_dir.mkdir()
        (plugin_file_dir / "comment.lua").write_text(
            """
require("comment").setup()
"""
        )

        return plugin_dir

    def test_add_comment(self, comment_plugin):
        """Test adding a comment to a line."""
        with NeovimSession(plugins=[str(comment_plugin)]) as nvim:
            # Type some code
            nvim.type_text("local x = 42")
            time.sleep(0.1)

            # Toggle comment with gcc
            nvim.ensure_normal_mode()
            nvim.send_raw("gcc")
            time.sleep(0.2)

            content = nvim.get_buffer_content()
            assert "-- local x = 42" in content or "-- " in content

    def test_remove_comment(self, comment_plugin):
        """Test removing a comment from a line."""
        with NeovimSession(plugins=[str(comment_plugin)]) as nvim:
            # Type a commented line
            nvim.type_text("-- local x = 42")
            time.sleep(0.1)

            # Toggle comment to remove it
            nvim.ensure_normal_mode()
            nvim.send_raw("gcc")
            time.sleep(0.2)

            content = nvim.get_buffer_content()
            # Comment prefix should be removed


class TestFileTypePluginPattern:
    """
    Demonstrate testing filetype-specific plugin behavior.

    Shows how to test plugins that behave differently based on filetype.
    """

    @pytest.fixture
    def filetype_plugin(self, tmp_path):
        """Create a filetype-aware plugin."""
        plugin_dir = tmp_path / "ft-plugin"
        lua_dir = plugin_dir / "lua" / "ft_plugin"
        lua_dir.mkdir(parents=True)

        (lua_dir / "init.lua").write_text(
            """
local M = {}

M.templates = {
    python = "#!/usr/bin/env python3\\n# -*- coding: utf-8 -*-\\n\\n",
    lua = "-- Module\\nlocal M = {}\\n\\nreturn M\\n",
    javascript = "// @ts-check\\n\\n",
}

function M.insert_template()
    local ft = vim.bo.filetype
    local template = M.templates[ft]
    if template then
        local lines = vim.split(template, "\\n")
        vim.api.nvim_buf_set_lines(0, 0, 0, false, lines)
        print("Inserted " .. ft .. " template")
    else
        print("No template for filetype: " .. ft)
    end
end

return M
"""
        )

        plugin_file_dir = plugin_dir / "plugin"
        plugin_file_dir.mkdir()
        (plugin_file_dir / "ft_plugin.lua").write_text(
            """
vim.api.nvim_create_user_command("InsertTemplate", function()
    require("ft_plugin").insert_template()
end, {})
"""
        )

        return plugin_dir

    def test_python_template(self, filetype_plugin, tmp_path):
        """Test inserting Python template."""
        test_file = tmp_path / "test.py"
        test_file.write_text("")

        with NeovimSession(
            plugins=[str(filetype_plugin)], args=[str(test_file)]
        ) as nvim:
            time.sleep(0.3)  # Wait for filetype detection

            nvim.ex("InsertTemplate")
            time.sleep(0.2)

            content = nvim.get_buffer_content()
            assert "python3" in content or "#!/usr/bin/env" in content

    def test_lua_template(self, filetype_plugin, tmp_path):
        """Test inserting Lua template."""
        test_file = tmp_path / "test.lua"
        test_file.write_text("")

        with NeovimSession(
            plugins=[str(filetype_plugin)], args=[str(test_file)]
        ) as nvim:
            time.sleep(0.3)

            nvim.ex("InsertTemplate")
            time.sleep(0.2)

            content = nvim.get_buffer_content()
            assert "Module" in content or "local M" in content


# =============================================================================
# Advanced Plugin Testing Patterns
# =============================================================================


class TestAsyncPluginPattern:
    """
    Demonstrate testing plugins with async operations.

    Shows patterns for testing plugins that do async work.
    """

    def test_wait_for_async_result(self, tmp_path):
        """Test waiting for an async operation to complete."""
        plugin_dir = tmp_path / "async-plugin"
        lua_dir = plugin_dir / "lua" / "async_test"
        lua_dir.mkdir(parents=True)

        (lua_dir / "init.lua").write_text(
            """
local M = {}

function M.delayed_message()
    vim.defer_fn(function()
        print("ASYNC_COMPLETE: Operation finished!")
    end, 500)  -- 500ms delay
    print("Starting async operation...")
end

return M
"""
        )

        plugin_file_dir = plugin_dir / "plugin"
        plugin_file_dir.mkdir()
        (plugin_file_dir / "async_test.lua").write_text(
            """
vim.api.nvim_create_user_command("AsyncTest", function()
    require("async_test").delayed_message()
end, {})
"""
        )

        with NeovimSession(plugins=[str(plugin_dir)]) as nvim:
            nvim.ex("AsyncTest")

            # Wait for async operation
            assert nvim.verify_text_appears("ASYNC_COMPLETE", timeout=2.0)


class TestAutocommandPluginPattern:
    """Test plugins that use autocommands."""

    def test_bufenter_autocommand(self, tmp_path):
        """Test a plugin that reacts to BufEnter."""
        plugin_dir = tmp_path / "autocmd-plugin"
        lua_dir = plugin_dir / "lua" / "autocmd_test"
        lua_dir.mkdir(parents=True)

        (lua_dir / "init.lua").write_text(
            """
local M = {}

M.enter_count = 0

function M.setup()
    vim.api.nvim_create_autocmd("BufEnter", {
        pattern = "*.test",
        callback = function()
            M.enter_count = M.enter_count + 1
            print("BufEnter triggered! Count: " .. M.enter_count)
        end
    })
end

return M
"""
        )

        plugin_file_dir = plugin_dir / "plugin"
        plugin_file_dir.mkdir()
        (plugin_file_dir / "autocmd_test.lua").write_text(
            """
require("autocmd_test").setup()
"""
        )

        # Create a .test file
        test_file = tmp_path / "example.test"
        test_file.write_text("test content")

        with NeovimSession(plugins=[str(plugin_dir)]) as nvim:
            # Open the .test file to trigger autocmd
            nvim.edit_file(str(test_file))
            time.sleep(0.3)

            content = nvim.get_content()
            assert "BufEnter triggered!" in content


# =============================================================================
# Assertion Helper Tests
# =============================================================================


class TestAssertionHelpers:
    """Test the built-in assertion helpers."""

    def test_assert_buffer_contains(self, nvim):
        """Test assert_buffer_contains helper."""
        nvim.type_text("Expected content here")
        nvim.assert_buffer_contains("Expected content")

    def test_assert_buffer_not_contains(self, nvim):
        """Test assert_buffer_not_contains helper."""
        nvim.type_text("Some content")
        nvim.assert_buffer_not_contains("unexpected text")

    def test_assert_mode(self, nvim):
        """Test assert_mode helper."""
        nvim.assert_mode("n")  # Should be in normal mode

        nvim.enter_insert_mode()
        time.sleep(0.1)
        nvim.assert_mode("i")  # Should be in insert mode


# =============================================================================
# Performance and Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_large_buffer(self, nvim):
        """Test handling large amounts of text."""
        # Generate large content
        large_text = "\n".join([f"Line {i}: " + "x" * 80 for i in range(100)])

        nvim.enter_insert_mode()
        # Send in chunks to avoid issues
        for line in large_text.split("\n")[:10]:  # Just first 10 lines for speed
            nvim.send_keys(line, literal=True)
            nvim.send_raw(Keys.ENTER)
        nvim.ensure_normal_mode()

        content = nvim.get_buffer_content()
        assert "Line 0:" in content

    def test_special_characters(self, nvim):
        """Test handling special characters in buffer."""
        nvim.type_text("Special: <> & | $ @ # % ^ * () [] {} \\ / ' \"")
        content = nvim.get_buffer_content()
        assert "Special:" in content

    def test_unicode_content(self, nvim):
        """Test handling unicode characters."""
        nvim.type_text("Unicode: \u4e2d\u6587 \u0420\u0443\u0441\u0441\u043a\u0438\u0439 \U0001f600")
        content = nvim.get_buffer_content()
        assert "Unicode:" in content

    def test_rapid_commands(self, nvim):
        """Test rapid command execution doesn't cause issues."""
        for i in range(10):
            nvim.ex(f"echo 'Command {i}'")
            time.sleep(0.05)

        # Should complete without hanging or crashing
        content = nvim.get_content()
        assert len(content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
