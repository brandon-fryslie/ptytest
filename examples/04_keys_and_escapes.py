"""
Keys and Escape Sequences - Comprehensive guide to terminal key handling.

The Keys class provides constants and helpers for all common terminal key
sequences including control characters, escape sequences, function keys,
and modifier combinations.

Run with: uv run pytest examples/04_keys_and_escapes.py -v
"""

import pytest

from ptytest import PtySession, Keys, MacKeys, ReadlineKeys


class TestControlCharacters:
    """Control characters (Ctrl+letter)."""

    def test_ctrl_constants(self):
        """Keys class provides Ctrl+letter constants."""
        # All Ctrl+A through Ctrl+Z are available
        assert Keys.CTRL_A == '\x01'  # Beginning of line
        assert Keys.CTRL_B == '\x02'  # Back one char / tmux prefix
        assert Keys.CTRL_C == '\x03'  # Interrupt
        assert Keys.CTRL_D == '\x04'  # EOF / Delete
        assert Keys.CTRL_E == '\x05'  # End of line
        assert Keys.CTRL_K == '\x0b'  # Kill to end
        assert Keys.CTRL_L == '\x0c'  # Clear screen
        assert Keys.CTRL_R == '\x12'  # Reverse search
        assert Keys.CTRL_U == '\x15'  # Kill line
        assert Keys.CTRL_W == '\x17'  # Kill word
        assert Keys.CTRL_Z == '\x1a'  # Suspend

    def test_ctrl_helper(self):
        """Use Keys.ctrl() to generate control characters."""
        assert Keys.ctrl('c') == '\x03'
        assert Keys.ctrl('r') == '\x12'
        assert Keys.ctrl('a') == '\x01'

        # Works with uppercase too
        assert Keys.ctrl('C') == '\x03'

    def test_send_ctrl_c(self):
        """Send Ctrl-C to interrupt a process."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("sleep 100", literal=True)
            session.send_raw(Keys.ENTER)

            import time
            time.sleep(0.1)

            session.send_raw(Keys.CTRL_C)
            assert session.verify_text_appears("$", timeout=2)


class TestSpecialKeys:
    """Special keys like Enter, Escape, Tab, etc."""

    def test_special_key_constants(self):
        """Special key constants."""
        assert Keys.ESCAPE == '\x1b'
        assert Keys.ESC == Keys.ESCAPE  # Alias
        assert Keys.ENTER == '\r'
        assert Keys.RETURN == Keys.ENTER  # Alias
        assert Keys.TAB == '\t'
        assert Keys.BACKSPACE == '\x7f'
        assert Keys.DELETE == '\x1b[3~'
        assert Keys.INSERT == '\x1b[2~'

    def test_send_tab(self):
        """Send Tab for completion."""
        with PtySession(["bash", "--norc"]) as session:
            # Type partial command
            session.send_keys("ech", literal=True)
            # Send tab (may trigger completion)
            session.send_raw(Keys.TAB)


class TestArrowKeys:
    """Arrow keys and navigation."""

    def test_arrow_key_constants(self):
        """Arrow key constants (ANSI mode)."""
        assert Keys.UP == '\x1b[A'
        assert Keys.DOWN == '\x1b[B'
        assert Keys.RIGHT == '\x1b[C'
        assert Keys.LEFT == '\x1b[D'

    def test_app_mode_arrows(self):
        """Application mode arrow keys (used by some apps like vim)."""
        assert Keys.UP_APP == '\x1bOA'
        assert Keys.DOWN_APP == '\x1bOB'
        assert Keys.RIGHT_APP == '\x1bOC'
        assert Keys.LEFT_APP == '\x1bOD'

    def test_send_arrow_keys(self):
        """Send arrow keys to navigate."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("hello world", literal=True)

            # Move cursor left
            session.send_raw(Keys.LEFT)
            session.send_raw(Keys.LEFT)

            # Insert text at cursor position
            session.send_keys("XX", literal=True)


class TestModifiedArrowKeys:
    """Arrow keys with modifiers (Shift, Ctrl, Alt)."""

    def test_shift_arrows(self):
        """Shift + Arrow keys."""
        assert Keys.SHIFT_UP == '\x1b[1;2A'
        assert Keys.SHIFT_DOWN == '\x1b[1;2B'
        assert Keys.SHIFT_RIGHT == '\x1b[1;2C'
        assert Keys.SHIFT_LEFT == '\x1b[1;2D'

    def test_ctrl_arrows(self):
        """Ctrl + Arrow keys (often word navigation)."""
        assert Keys.CTRL_UP == '\x1b[1;5A'
        assert Keys.CTRL_DOWN == '\x1b[1;5B'
        assert Keys.CTRL_RIGHT == '\x1b[1;5C'  # Forward word
        assert Keys.CTRL_LEFT == '\x1b[1;5D'   # Backward word

    def test_alt_arrows(self):
        """Alt + Arrow keys."""
        assert Keys.ALT_UP == '\x1b[1;3A'
        assert Keys.ALT_DOWN == '\x1b[1;3B'
        assert Keys.ALT_RIGHT == '\x1b[1;3C'
        assert Keys.ALT_LEFT == '\x1b[1;3D'

    def test_combo_modifiers(self):
        """Multiple modifier combinations."""
        assert Keys.SHIFT_CTRL_UP == '\x1b[1;6A'
        assert Keys.ALT_CTRL_RIGHT == '\x1b[1;7C'
        assert Keys.SHIFT_ALT_CTRL_DOWN == '\x1b[1;8B'


class TestFunctionKeys:
    """Function keys F1-F12."""

    def test_function_key_constants(self):
        """F1-F12 constants."""
        # F1-F4 use SS3 sequences
        assert Keys.F1 == '\x1bOP'
        assert Keys.F2 == '\x1bOQ'
        assert Keys.F3 == '\x1bOR'
        assert Keys.F4 == '\x1bOS'

        # F5-F12 use CSI sequences
        assert Keys.F5 == '\x1b[15~'
        assert Keys.F10 == '\x1b[21~'
        assert Keys.F12 == '\x1b[24~'

    def test_function_key_helper(self):
        """Use Keys.function_key() to generate F-key sequences."""
        assert Keys.function_key(1) == Keys.F1
        assert Keys.function_key(5) == Keys.F5
        assert Keys.function_key(12) == Keys.F12

    def test_modified_function_keys(self):
        """Function keys with modifiers."""
        assert Keys.SHIFT_F1 == '\x1b[1;2P'
        assert Keys.CTRL_F5 == '\x1b[15;5~'
        assert Keys.ALT_F12 == '\x1b[24;3~'

        # Use helper with modifier
        assert Keys.function_key(5, modifier=2) == '\x1b[15;2~'  # Shift+F5
        assert Keys.function_key(5, modifier=5) == '\x1b[15;5~'  # Ctrl+F5


class TestNavigationKeys:
    """Navigation keys: Home, End, Page Up/Down."""

    def test_navigation_constants(self):
        """Navigation key constants."""
        assert Keys.HOME == '\x1b[H'
        assert Keys.END == '\x1b[F'
        assert Keys.PAGE_UP == '\x1b[5~'
        assert Keys.PAGE_DOWN == '\x1b[6~'

    def test_modified_navigation(self):
        """Navigation keys with modifiers."""
        assert Keys.SHIFT_HOME == '\x1b[1;2H'
        assert Keys.CTRL_END == '\x1b[1;5F'
        assert Keys.SHIFT_PAGE_UP == '\x1b[5;2~'


class TestMetaAndAlt:
    """Meta/Alt key combinations."""

    def test_meta_helper(self):
        """Use Keys.meta() for Alt combinations."""
        # Alt+letter is ESC + letter
        assert Keys.meta('d') == '\x1bd'  # Alt+D
        assert Keys.meta('f') == '\x1bf'  # Alt+F (forward word)
        assert Keys.meta('b') == '\x1bb'  # Alt+B (backward word)

    def test_alt_alias(self):
        """Keys.alt() is an alias for meta()."""
        assert Keys.alt('x') == Keys.meta('x')

    def test_ctrl_alt_combination(self):
        """Ctrl+Alt combinations."""
        assert Keys.ctrl_alt('d') == '\x1b\x04'  # Ctrl+Alt+D


class TestMacKeys:
    """macOS-specific Option key combinations."""

    def test_option_keys(self):
        """Option+letter keys."""
        assert MacKeys.OPT_B == '\x1bb'  # Back word
        assert MacKeys.OPT_F == '\x1bf'  # Forward word
        assert MacKeys.OPT_D == '\x1bd'  # Delete word forward

    def test_option_shift(self):
        """Option+Shift combinations."""
        assert MacKeys.OPT_SHIFT_A == '\x1bA'

    def test_option_special(self):
        """Option with special keys."""
        assert MacKeys.OPT_BACKSPACE == '\x1b\x7f'  # Delete word backward
        assert MacKeys.OPT_PERIOD == '\x1b.'  # Insert last argument


class TestReadlineKeys:
    """Readline (bash/zsh) key bindings."""

    def test_movement_keys(self):
        """Movement keys."""
        assert ReadlineKeys.BEGINNING_OF_LINE == Keys.CTRL_A
        assert ReadlineKeys.END_OF_LINE == Keys.CTRL_E
        assert ReadlineKeys.FORWARD_CHAR == Keys.CTRL_F
        assert ReadlineKeys.BACKWARD_CHAR == Keys.CTRL_B
        assert ReadlineKeys.FORWARD_WORD == '\x1bf'
        assert ReadlineKeys.BACKWARD_WORD == '\x1bb'

    def test_editing_keys(self):
        """Editing keys."""
        assert ReadlineKeys.KILL_LINE == Keys.CTRL_K
        assert ReadlineKeys.UNIX_LINE_DISCARD == Keys.CTRL_U
        assert ReadlineKeys.KILL_WORD == '\x1bd'
        assert ReadlineKeys.BACKWARD_KILL_WORD == Keys.CTRL_W
        assert ReadlineKeys.TRANSPOSE_CHARS == Keys.CTRL_T

    def test_history_keys(self):
        """History navigation keys."""
        assert ReadlineKeys.PREVIOUS_HISTORY == Keys.CTRL_P
        assert ReadlineKeys.NEXT_HISTORY == Keys.CTRL_N
        assert ReadlineKeys.REVERSE_SEARCH == Keys.CTRL_R

    def test_completion_keys(self):
        """Completion keys."""
        assert ReadlineKeys.COMPLETE == Keys.TAB


class TestKeyHelpers:
    """Key helper methods."""

    def test_repeat(self):
        """Repeat a key sequence."""
        assert Keys.repeat('j', 5) == 'jjjjj'
        assert Keys.repeat(Keys.DOWN, 3) == '\x1b[B\x1b[B\x1b[B'

    def test_sequence(self):
        """Combine multiple key sequences."""
        seq = Keys.sequence(Keys.ESCAPE, ':', 'w', Keys.ENTER)
        assert seq == '\x1b:w\r'  # Vim save command

    def test_vim_command(self):
        """Generate vim command sequence."""
        assert Keys.vim_command('wq') == '\x1b:wq\r'
        assert Keys.vim_command('set number') == '\x1b:set number\r'

    def test_vim_search(self):
        """Generate vim search sequence."""
        assert Keys.vim_search('pattern') == '\x1b/pattern\r'
        assert Keys.vim_search('pattern', backward=True) == '\x1b?pattern\r'


class TestCommonCharacters:
    """Common characters for readability."""

    def test_character_constants(self):
        """Character constants."""
        assert Keys.SPACE == ' '
        assert Keys.SLASH == '/'
        assert Keys.PIPE == '|'
        assert Keys.COLON == ':'

    def test_brackets(self):
        """Bracket constants."""
        assert Keys.OPEN_PAREN == '('
        assert Keys.CLOSE_PAREN == ')'
        assert Keys.OPEN_BRACKET == '['
        assert Keys.CLOSE_BRACKET == ']'
        assert Keys.OPEN_BRACE == '{'
        assert Keys.CLOSE_BRACE == '}'


class TestNumericKeypad:
    """Numeric keypad keys."""

    def test_keypad_constants(self):
        """Keypad keys (application mode)."""
        assert Keys.KP_ENTER == '\x1bOM'
        assert Keys.KP_0 == '\x1bOp'
        assert Keys.KP_5 == '\x1bOu'


class TestPracticalExamples:
    """Practical examples combining keys."""

    def test_readline_word_navigation(self):
        """Navigate by words in shell."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("one two three four", literal=True)

            # Go back one word (Alt+B)
            session.send_raw(ReadlineKeys.BACKWARD_WORD)

            # Go forward one word (Alt+F)
            session.send_raw(ReadlineKeys.FORWARD_WORD)

            # Delete word backward (Ctrl+W)
            session.send_raw(ReadlineKeys.BACKWARD_KILL_WORD)

    def test_kill_and_yank(self):
        """Kill and yank (cut and paste)."""
        with PtySession(["bash", "--norc"]) as session:
            session.send_keys("hello world", literal=True)

            # Kill to end of line (Ctrl+K)
            session.send_raw(ReadlineKeys.BEGINNING_OF_LINE)
            session.send_raw(ReadlineKeys.KILL_LINE)

            # Yank (paste) it back (Ctrl+Y)
            session.send_raw(ReadlineKeys.YANK)
