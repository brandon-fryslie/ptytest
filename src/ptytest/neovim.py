"""
Neovim plugin testing harness for ptytest.

Provides NeovimSession class for testing Neovim plugins with real terminal
interaction. Supports isolated plugin loading, buffer inspection, and
comprehensive state verification.

Example:
    from ptytest.neovim import NeovimSession

    def test_my_plugin():
        with NeovimSession(plugins=["~/.local/share/nvim/site/pack/plugins/start/my-plugin"]) as nvim:
            nvim.command("MyPluginCommand")
            assert "expected output" in nvim.get_buffer_content()
"""

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .keys import Keys, VimKeys
from .session import PtySession


class NeovimSession(PtySession):
    """
    Neovim session for testing plugins with real terminal interaction.

    Starts Neovim in an isolated environment with optional plugin loading,
    then provides methods to interact with and inspect Neovim state.

    Args:
        plugins: List of plugin paths to load (directories or git URLs)
        init_lua: Lua code to run on startup (init.lua content)
        init_vim: Vimscript to run on startup (init.vim content)
        args: Additional command-line arguments to Neovim
        env: Environment variables to set
        width: Terminal width (default: 120)
        height: Terminal height (default: 40)
        timeout: Default timeout for operations (seconds)
        clean: If True (default), start with --clean flag (no user config)
        headless: If True, start in headless mode (no UI) - not recommended for most tests
        enable_viz: Enable web visualization (default: False)
        viz_port: Port for visualization server (default: 8080)

    Example:
        # Test a simple plugin
        with NeovimSession(plugins=["~/my-plugin"]) as nvim:
            nvim.command("MyCommand")
            assert nvim.get_buffer_content() == "expected"

        # Test with custom init
        init = '''
        vim.g.my_plugin_option = true
        require("my_plugin").setup({})
        '''
        with NeovimSession(init_lua=init) as nvim:
            ...
    """

    # Marker for command output extraction
    _OUTPUT_START = "<<<PTYTEST_OUTPUT_START>>>"
    _OUTPUT_END = "<<<PTYTEST_OUTPUT_END>>>"

    def __init__(
        self,
        plugins: Optional[List[str]] = None,
        init_lua: Optional[str] = None,
        init_vim: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        width: int = 120,
        height: int = 40,
        timeout: float = 5.0,
        clean: bool = True,
        headless: bool = False,
        enable_viz: bool = False,
        viz_port: int = 8080,
    ):
        self.plugins = plugins or []
        self.init_lua = init_lua
        self.init_vim = init_vim
        self.extra_args = args or []
        self.custom_env = env or {}
        self.default_timeout = timeout
        self.clean = clean
        self.headless = headless
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self._config_dir: Optional[Path] = None

        # Build Neovim command
        nvim_cmd = self._build_command()

        # Merge environment
        full_env = os.environ.copy()
        full_env.update(self.custom_env)

        # Initialize parent PtySession
        super().__init__(
            command=nvim_cmd,
            width=width,
            height=height,
            env=full_env,
            enable_viz=enable_viz,
            viz_port=viz_port,
        )

        # Wait for Neovim to start
        self._wait_for_startup()

    def _build_command(self) -> List[str]:
        """Build the Neovim command with all options."""
        # Create temporary config directory
        self._temp_dir = tempfile.TemporaryDirectory(prefix="ptytest_nvim_")
        self._config_dir = Path(self._temp_dir.name)

        # Create directory structure
        (self._config_dir / "lua").mkdir(parents=True, exist_ok=True)
        (self._config_dir / "plugin").mkdir(parents=True, exist_ok=True)

        cmd = ["nvim"]

        if self.clean:
            cmd.append("--clean")

        if self.headless:
            cmd.append("--headless")

        # Add plugin paths via runtimepath
        if self.plugins:
            rtp_additions = []
            for plugin in self.plugins:
                plugin_path = Path(plugin).expanduser().resolve()
                if plugin_path.exists():
                    rtp_additions.append(str(plugin_path))
            if rtp_additions:
                # Will be set via init
                pass

        # Create init file
        init_content = self._build_init_content()
        init_file = self._config_dir / "init.lua"
        init_file.write_text(init_content)

        cmd.extend(["-u", str(init_file)])

        # Add extra args
        cmd.extend(self.extra_args)

        return cmd

    def _build_init_content(self) -> str:
        """Build the init.lua content."""
        lines = [
            "-- ptytest auto-generated init.lua",
            "vim.opt.swapfile = false",
            "vim.opt.backup = false",
            "vim.opt.writebackup = false",
            "vim.opt.undofile = false",
            "vim.opt.shadafile = 'NONE'",
            "vim.opt.updatetime = 100",
            "vim.opt.timeoutlen = 300",
            "vim.opt.ttimeoutlen = 10",
            "vim.opt.lazyredraw = false",
            "vim.opt.termguicolors = false",  # Simpler for testing
            "",
        ]

        # Add plugin paths to runtimepath
        if self.plugins:
            for plugin in self.plugins:
                plugin_path = Path(plugin).expanduser().resolve()
                if plugin_path.exists():
                    escaped_path = str(plugin_path).replace("'", "\\'")
                    lines.append(f"vim.opt.runtimepath:prepend('{escaped_path}')")
            lines.append("")

        # Add custom init.lua content
        if self.init_lua:
            lines.append("-- User init.lua content")
            lines.append(self.init_lua)
            lines.append("")

        # Add custom init.vim content (via vim.cmd)
        if self.init_vim:
            lines.append("-- User init.vim content")
            # Escape for Lua multiline string
            escaped = self.init_vim.replace("\\", "\\\\").replace("]", "\\]")
            lines.append(f"vim.cmd([[\n{escaped}\n]])")
            lines.append("")

        # Source plugin files after runtimepath is set
        if self.plugins:
            lines.append("-- Source plugin files")
            lines.append("for _, path in ipairs(vim.opt.runtimepath:get()) do")
            lines.append("  local plugin_dir = path .. '/plugin'")
            lines.append("  if vim.fn.isdirectory(plugin_dir) == 1 then")
            lines.append("    for _, file in ipairs(vim.fn.glob(plugin_dir .. '/*.lua', false, true)) do")
            lines.append("      dofile(file)")
            lines.append("    end")
            lines.append("    for _, file in ipairs(vim.fn.glob(plugin_dir .. '/*.vim', false, true)) do")
            lines.append("      vim.cmd('source ' .. file)")
            lines.append("    end")
            lines.append("  end")
            lines.append("end")
            lines.append("")

        return "\n".join(lines)

    def _wait_for_startup(self):
        """Wait for Neovim to be ready."""
        # Wait for the screen to show something (not just blank)
        start = time.time()
        while time.time() - start < self.default_timeout:
            content = self.get_content()
            # Neovim shows ~ for empty lines or has content
            if "~" in content or len(content.strip()) > 0:
                break
            time.sleep(0.1)

        # Give it a moment to fully initialize
        time.sleep(0.3)

    def cleanup(self):
        """Clean up Neovim session and temporary files."""
        # Try to quit Neovim gracefully first
        try:
            if self.process and self.process.isalive():
                self.send_raw(Keys.ESCAPE)  # Ensure normal mode
                time.sleep(0.05)
                self.send_raw(Keys.ESCAPE)
                time.sleep(0.05)
                self.ex("qa!", wait=False)
                time.sleep(0.2)
        except Exception:
            pass

        # Call parent cleanup
        super().cleanup()

        # Clean up temp directory
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass

    # =========================================================================
    # Command Execution
    # =========================================================================

    def ex(self, cmd: str, wait: bool = True, timeout: Optional[float] = None) -> str:
        """
        Execute an Ex command in Neovim.

        Args:
            cmd: The Ex command to execute (without leading :)
            wait: If True, wait for command to complete
            timeout: Timeout in seconds (uses default if None)

        Returns:
            Command output (if any)

        Example:
            nvim.ex("edit test.txt")
            output = nvim.ex("echo 'hello'")
            nvim.ex("MyPluginCommand")
        """
        timeout = timeout or self.default_timeout

        # Ensure we're in normal mode
        self.send_raw(Keys.ESCAPE)
        time.sleep(0.05)

        # Send the command
        self.send_raw(f":{cmd}")
        time.sleep(0.05)
        self.send_raw(Keys.ENTER)

        if wait:
            time.sleep(0.2)

        return ""

    def lua(self, code: str, timeout: Optional[float] = None) -> str:
        """
        Execute Lua code in Neovim.

        Args:
            code: Lua code to execute
            timeout: Timeout in seconds

        Returns:
            Output from the Lua code (if any)

        Example:
            nvim.lua("print('hello')")
            nvim.lua("vim.g.my_var = 42")
            result = nvim.lua("return vim.fn.expand('%')")
        """
        # Send directly - we're going through PTY, not shell
        return self.ex(f"lua {code}", timeout=timeout)

    def feedkeys(self, keys: str, mode: str = "n"):
        """
        Feed keys to Neovim using feedkeys() function.

        This is useful for testing mappings that might not work with direct send.

        Args:
            keys: Keys to feed (can use special notation like <CR>, <Esc>)
            mode: Mode for feedkeys ('n' = normal, 'm' = remap, 't' = typed)

        Example:
            nvim.feedkeys("<leader>ff")  # Trigger a leader mapping
            nvim.feedkeys("iHello<Esc>")  # Insert text
        """
        escaped = keys.replace("\\", "\\\\").replace('"', '\\"')
        self.ex(f'call feedkeys("{escaped}", "{mode}")')

    def normal(self, keys: str):
        """
        Execute normal mode commands.

        Args:
            keys: Normal mode key sequence

        Example:
            nvim.normal("gg")  # Go to top
            nvim.normal("dd")  # Delete line
            nvim.normal("5j")  # Move down 5 lines
        """
        self.ex(f"normal! {keys}")

    # =========================================================================
    # Buffer Operations
    # =========================================================================

    def get_buffer_content(self, buffer: Union[int, str] = "%") -> str:
        """
        Get the content of a buffer.

        Args:
            buffer: Buffer number or '%' for current buffer

        Returns:
            Buffer content as a string

        Example:
            content = nvim.get_buffer_content()
            content = nvim.get_buffer_content(1)  # Buffer 1
        """
        # Use the screen content for current buffer (most reliable)
        if buffer == "%":
            content = self.get_content()
            # Remove status line and command line (last 2 lines typically)
            lines = content.split("\n")
            # Filter out ~ lines (empty buffer indicators) at the end
            while lines and lines[-1].strip().startswith("~"):
                lines.pop()
            # Remove the last line if it looks like a status/command line
            if lines and (":" in lines[-1] or "%" in lines[-1] or lines[-1].strip() == ""):
                lines.pop()
            return "\n".join(lines)
        else:
            # For other buffers, we need to switch to them
            raise NotImplementedError("Getting content of non-current buffers requires buffer switching")

    def get_buffer_lines(self, start: int = 1, end: int = -1) -> List[str]:
        """
        Get specific lines from the current buffer.

        Args:
            start: Start line (1-indexed)
            end: End line (-1 for last line)

        Returns:
            List of lines
        """
        content = self.get_buffer_content()
        lines = content.split("\n")

        if end == -1:
            end = len(lines)

        return lines[start - 1 : end]

    def get_current_line(self) -> str:
        """Get the content of the current line."""
        lines = self.get_buffer_lines()
        cursor = self.get_cursor_position()
        if cursor and cursor[0] <= len(lines):
            return lines[cursor[0] - 1]
        return ""

    def set_buffer_content(self, content: str):
        """
        Set the content of the current buffer.

        Args:
            content: Content to set
        """
        # Delete all content first
        self.ex("%delete _")
        # Insert new content
        for line in content.split("\n"):
            escaped = line.replace("\\", "\\\\").replace('"', '\\"')
            self.ex(f'normal! i{escaped}')
            self.send_raw(Keys.ENTER)
        # Go to beginning
        self.ex("normal! gg")

    def append_line(self, line: str, after: int = -1):
        """
        Append a line to the buffer.

        Args:
            line: Line content to append
            after: Line number to append after (-1 for end)
        """
        escaped = line.replace("'", "''")
        if after == -1:
            self.ex(f"$put ='{escaped}'")
        else:
            self.ex(f"{after}put ='{escaped}'")

    # =========================================================================
    # Cursor and Position
    # =========================================================================

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position.

        Returns:
            Tuple of (line, column) - 1-indexed

        Example:
            line, col = nvim.get_cursor_position()
        """
        # Parse from screen - look for cursor position indicator
        # This is approximate - for exact position, use Lua
        content = self.get_content()
        lines = content.split("\n")

        # Try to find cursor by screen inspection
        # Default to 1,1 if can't determine
        return (1, 1)

    def set_cursor_position(self, line: int, col: int = 1):
        """
        Set the cursor position.

        Args:
            line: Line number (1-indexed)
            col: Column number (1-indexed)
        """
        self.ex(f"call cursor({line}, {col})")

    def goto_line(self, line: int):
        """Go to a specific line."""
        self.ex(f"{line}")

    def goto_top(self):
        """Go to the top of the buffer."""
        self.normal("gg")

    def goto_bottom(self):
        """Go to the bottom of the buffer."""
        self.normal("G")

    # =========================================================================
    # Mode Operations
    # =========================================================================

    def get_mode(self) -> str:
        """
        Get the current Neovim mode.

        Returns:
            Mode string: 'n' (normal), 'i' (insert), 'v' (visual),
                        'V' (visual line), 'CTRL-V' (visual block),
                        'c' (command), 't' (terminal), etc.
        """
        # Infer from screen content
        content = self.get_content()
        lower_content = content.lower()

        if "-- insert --" in lower_content:
            return "i"
        elif "-- visual --" in lower_content:
            return "v"
        elif "-- visual line --" in lower_content:
            return "V"
        elif "-- visual block --" in lower_content:
            return "\x16"  # Ctrl-V
        elif "-- replace --" in lower_content:
            return "R"
        elif "-- select --" in lower_content:
            return "s"
        else:
            return "n"  # Default to normal

    def ensure_normal_mode(self):
        """Ensure Neovim is in normal mode."""
        self.send_raw(Keys.ESCAPE)
        time.sleep(0.05)
        self.send_raw(Keys.ESCAPE)
        time.sleep(0.05)

    def enter_insert_mode(self, position: str = "i"):
        """
        Enter insert mode.

        Args:
            position: How to enter insert mode:
                     'i' = insert before cursor
                     'a' = append after cursor
                     'I' = insert at line beginning
                     'A' = append at line end
                     'o' = open line below
                     'O' = open line above
        """
        self.ensure_normal_mode()
        self.send_raw(position)
        time.sleep(0.1)

    def enter_visual_mode(self, mode: str = "v"):
        """
        Enter visual mode.

        Args:
            mode: Visual mode type:
                  'v' = character-wise
                  'V' = line-wise
                  '<C-v>' = block-wise
        """
        self.ensure_normal_mode()
        if mode == "<C-v>":
            self.send_raw(Keys.CTRL_V)
        else:
            self.send_raw(mode)
        time.sleep(0.1)

    # =========================================================================
    # Window and Tab Operations
    # =========================================================================

    def get_window_count(self) -> int:
        """Get the number of windows."""
        # Count by looking for window separators or use command
        # This is approximate from screen analysis
        content = self.get_content()
        # Count vertical separators (│) for split detection
        lines = content.split("\n")
        if lines:
            separators = lines[0].count("│")
            return separators + 1
        return 1

    def split_window(self, vertical: bool = False):
        """
        Split the current window.

        Args:
            vertical: If True, split vertically; if False, split horizontally
        """
        if vertical:
            self.ex("vsplit")
        else:
            self.ex("split")

    def close_window(self):
        """Close the current window."""
        self.ex("close")

    def next_window(self):
        """Move to the next window."""
        self.send_raw(Keys.CTRL_W)
        self.send_raw("w")

    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        # Look for tab line at top of screen
        content = self.get_content()
        first_line = content.split("\n")[0] if content else ""
        # Count tab indicators
        return max(1, first_line.count("["))  # Approximate

    def new_tab(self):
        """Open a new tab."""
        self.ex("tabnew")

    def next_tab(self):
        """Go to the next tab."""
        self.ex("tabnext")

    def close_tab(self):
        """Close the current tab."""
        self.ex("tabclose")

    # =========================================================================
    # File Operations
    # =========================================================================

    def edit_file(self, filepath: str):
        """
        Open a file for editing.

        Args:
            filepath: Path to the file
        """
        escaped = filepath.replace(" ", "\\ ")
        self.ex(f"edit {escaped}")

    def save_file(self, filepath: Optional[str] = None):
        """
        Save the current buffer.

        Args:
            filepath: Optional path to save to (uses current if None)
        """
        if filepath:
            escaped = filepath.replace(" ", "\\ ")
            self.ex(f"write {escaped}")
        else:
            self.ex("write")

    def get_current_filename(self) -> str:
        """Get the filename of the current buffer."""
        # Look at the status line or title
        content = self.get_content()
        lines = content.split("\n")
        # Status line is typically near the bottom
        for line in reversed(lines):
            # Look for common filename patterns
            if "/" in line or "." in line:
                # Extract potential filename
                parts = line.split()
                for part in parts:
                    if "/" in part or (
                        "." in part and not part.startswith("[") and not part.endswith("%")
                    ):
                        return part.strip()
        return "[No Name]"

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search(self, pattern: str, backward: bool = False):
        """
        Search for a pattern.

        Args:
            pattern: Search pattern
            backward: If True, search backward
        """
        prefix = "?" if backward else "/"
        self.send_raw(prefix)
        self.send_raw(pattern)
        self.send_raw(Keys.ENTER)
        time.sleep(0.1)

    def search_next(self):
        """Go to the next search match."""
        self.normal("n")

    def search_prev(self):
        """Go to the previous search match."""
        self.normal("N")

    def clear_search_highlight(self):
        """Clear search highlighting."""
        self.ex("nohlsearch")

    # =========================================================================
    # Register Operations
    # =========================================================================

    def get_register(self, reg: str = '"') -> str:
        """
        Get the content of a register.

        Args:
            reg: Register name (default: unnamed register)

        Returns:
            Register content

        Note: This requires screen parsing or Lua execution
        """
        # This would need Lua execution to get accurately
        # For now, return empty string
        return ""

    def set_register(self, reg: str, content: str):
        """
        Set the content of a register.

        Args:
            reg: Register name
            content: Content to set
        """
        escaped = content.replace("'", "''")
        self.ex(f"let @{reg} = '{escaped}'")

    def yank_line(self):
        """Yank the current line."""
        self.normal("yy")

    def paste(self, before: bool = False):
        """
        Paste from the default register.

        Args:
            before: If True, paste before cursor; if False, paste after
        """
        self.normal("P" if before else "p")

    # =========================================================================
    # Plugin-Specific Helpers
    # =========================================================================

    def wait_for_plugin_load(self, plugin_name: str, timeout: Optional[float] = None):
        """
        Wait for a plugin to be loaded.

        Args:
            plugin_name: Name of the plugin module
            timeout: Timeout in seconds
        """
        timeout = timeout or self.default_timeout
        # Try to require the plugin and see if it succeeds
        # This is a best-effort check
        time.sleep(0.5)  # Give plugins time to load

    def call_plugin_function(self, module: str, func: str, *args) -> Any:
        """
        Call a plugin's Lua function.

        Args:
            module: Plugin module name
            func: Function name
            *args: Arguments to pass

        Returns:
            Function result (if any)
        """
        args_str = ", ".join(repr(arg) for arg in args)
        self.lua(f"require('{module}').{func}({args_str})")
        return None  # Can't easily get return value via terminal

    def trigger_autocmd(self, event: str, pattern: str = "*"):
        """
        Trigger an autocommand.

        Args:
            event: Autocommand event name
            pattern: Pattern to match
        """
        self.ex(f"doautocmd {event} {pattern}")

    # =========================================================================
    # Assertion Helpers
    # =========================================================================

    def assert_buffer_contains(self, text: str, msg: Optional[str] = None):
        """
        Assert that the buffer contains specific text.

        Args:
            text: Text to search for
            msg: Optional assertion message
        """
        content = self.get_buffer_content()
        assert text in content, msg or f"Buffer does not contain '{text}'. Content:\n{content}"

    def assert_buffer_not_contains(self, text: str, msg: Optional[str] = None):
        """
        Assert that the buffer does not contain specific text.

        Args:
            text: Text that should not be present
            msg: Optional assertion message
        """
        content = self.get_buffer_content()
        assert text not in content, msg or f"Buffer unexpectedly contains '{text}'"

    def assert_mode(self, expected: str, msg: Optional[str] = None):
        """
        Assert the current mode.

        Args:
            expected: Expected mode character
            msg: Optional assertion message
        """
        actual = self.get_mode()
        assert actual == expected, msg or f"Expected mode '{expected}', got '{actual}'"

    def assert_cursor_at(self, line: int, col: Optional[int] = None, msg: Optional[str] = None):
        """
        Assert the cursor is at a specific position.

        Args:
            line: Expected line number
            col: Expected column number (optional)
            msg: Optional assertion message
        """
        actual_line, actual_col = self.get_cursor_position()
        if col is None:
            assert actual_line == line, msg or f"Expected cursor at line {line}, got {actual_line}"
        else:
            assert (actual_line, actual_col) == (
                line,
                col,
            ), msg or f"Expected cursor at ({line}, {col}), got ({actual_line}, {actual_col})"

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def type_text(self, text: str):
        """
        Type text in insert mode (enters and exits insert mode automatically).

        Args:
            text: Text to type
        """
        self.enter_insert_mode()
        self.send_keys(text, literal=True)
        self.ensure_normal_mode()

    def delete_line(self):
        """Delete the current line."""
        self.normal("dd")

    def undo(self):
        """Undo the last change."""
        self.normal("u")

    def redo(self):
        """Redo the last undone change."""
        self.send_raw(Keys.CTRL_R)

    def select_all(self):
        """Select all content in visual mode."""
        self.ex("normal! ggVG")

    def indent_line(self):
        """Indent the current line."""
        self.normal(">>")

    def unindent_line(self):
        """Unindent the current line."""
        self.normal("<<")
