"""
Common key sequences and escape codes for terminal testing.

This module provides constants for commonly used key sequences when testing
interactive terminal applications.
"""


class Keys:
    """Common key sequences for terminal interaction."""

    # Control characters
    CTRL_A = '\x01'
    CTRL_B = '\x02'  # tmux default prefix
    CTRL_C = '\x03'  # Interrupt
    CTRL_D = '\x04'  # EOF
    CTRL_E = '\x05'
    CTRL_F = '\x06'
    CTRL_G = '\x07'  # Bell / abort in some apps
    CTRL_H = '\x08'  # Backspace
    CTRL_I = '\x09'  # Tab
    CTRL_J = '\x0a'  # Newline
    CTRL_K = '\x0b'
    CTRL_L = '\x0c'  # Clear screen
    CTRL_M = '\x0d'  # Enter/Return
    CTRL_N = '\x0e'
    CTRL_O = '\x0f'
    CTRL_P = '\x10'
    CTRL_Q = '\x11'
    CTRL_R = '\x12'  # Reverse search
    CTRL_S = '\x13'
    CTRL_T = '\x14'
    CTRL_U = '\x15'  # Kill line
    CTRL_V = '\x16'
    CTRL_W = '\x17'  # Kill word
    CTRL_X = '\x18'
    CTRL_Y = '\x19'  # Yank
    CTRL_Z = '\x1a'  # Suspend

    # Special keys
    ESCAPE = '\x1b'
    ESC = ESCAPE
    ENTER = '\r'
    RETURN = ENTER
    TAB = '\t'
    BACKSPACE = '\x7f'
    DELETE = '\x1b[3~'

    # Arrow keys (ANSI)
    UP = '\x1b[A'
    DOWN = '\x1b[B'
    RIGHT = '\x1b[C'
    LEFT = '\x1b[D'

    # Arrow keys (Application mode)
    UP_APP = '\x1bOA'
    DOWN_APP = '\x1bOB'
    RIGHT_APP = '\x1bOC'
    LEFT_APP = '\x1bOD'

    # Function keys
    F1 = '\x1bOP'
    F2 = '\x1bOQ'
    F3 = '\x1bOR'
    F4 = '\x1bOS'
    F5 = '\x1b[15~'
    F6 = '\x1b[17~'
    F7 = '\x1b[18~'
    F8 = '\x1b[19~'
    F9 = '\x1b[20~'
    F10 = '\x1b[21~'
    F11 = '\x1b[23~'
    F12 = '\x1b[24~'

    # Navigation
    HOME = '\x1b[H'
    END = '\x1b[F'
    PAGE_UP = '\x1b[5~'
    PAGE_DOWN = '\x1b[6~'
    INSERT = '\x1b[2~'

    # Meta/Alt key combinations (ESC + key)
    @staticmethod
    def meta(key: str) -> str:
        """
        Create a Meta/Alt key combination.

        Args:
            key: The key to combine with Meta/Alt

        Returns:
            The escape sequence for Meta + key

        Example:
            Keys.meta('d')  # Alt+D / Option+D -> '\\x1bd'
            Keys.meta('D')  # Alt+Shift+D / Option+Shift+D -> '\\x1bD'
        """
        return f'\x1b{key}'

    @staticmethod
    def ctrl(key: str) -> str:
        """
        Create a Ctrl key combination.

        Args:
            key: The letter to combine with Ctrl (a-z)

        Returns:
            The control character

        Example:
            Keys.ctrl('c')  # Ctrl+C -> '\\x03'
            Keys.ctrl('r')  # Ctrl+R -> '\\x12'
        """
        if len(key) != 1 or not key.isalpha():
            raise ValueError("Key must be a single letter a-z")
        return chr(ord(key.lower()) - ord('a') + 1)


# Common macOS Option key combinations (same as Meta)
class MacKeys(Keys):
    """macOS-specific key combinations using Option key."""

    # Option + letter (same as Meta/ESC + letter)
    OPT_A = Keys.meta('a')
    OPT_B = Keys.meta('b')
    OPT_C = Keys.meta('c')
    OPT_D = Keys.meta('d')
    OPT_F = Keys.meta('f')

    # Option + Shift + letter
    OPT_SHIFT_A = Keys.meta('A')
    OPT_SHIFT_B = Keys.meta('B')
    OPT_SHIFT_C = Keys.meta('C')
    OPT_SHIFT_D = Keys.meta('D')  # Common zaw binding
    OPT_SHIFT_F = Keys.meta('F')
