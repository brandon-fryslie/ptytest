"""
Extended key sequences and escape codes for terminal testing.

This module extends ptydriver's key classes with additional application-specific
key bindings for vim, fzf, tmux, readline, and other popular CLI tools.

Key sequence reference: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
"""

from typing import Optional
from ptydriver import Keys as PtyDriverKeys, MacKeys as PtyDriverMacKeys, ReadlineKeys as PtyDriverReadlineKeys


# Re-export base classes from ptydriver for convenience
Keys = PtyDriverKeys
MacKeys = PtyDriverMacKeys
ReadlineKeys = PtyDriverReadlineKeys


class FzfKeys:
    """
    Key bindings for fzf (command-line fuzzy finder).

    These are the default key bindings in fzf. See fzf documentation
    for the complete list of available key bindings.
    """

    # Movement
    UP = Keys.UP
    DOWN = Keys.DOWN
    LEFT = Keys.LEFT
    RIGHT = Keys.RIGHT
    HOME = Keys.HOME
    END = Keys.END
    PAGE_UP = Keys.PAGE_UP
    PAGE_DOWN = Keys.PAGE_DOWN

    # Selection
    ACCEPT = '\r'  # Enter
    ACCEPT_NON_EMPTY = Keys.CTRL_M
    ABORT = Keys.CTRL_C
    ACCEPT_OR_PRINT = Keys.CTRL_M  # Same as ACCEPT

    # Actions
    TOGGLE = Keys.TAB  # Toggle selection
    TOGGLE_ALL = Keys.CTRL_T  # Toggle all selections
    TOGGLE_IN_RANGE = Keys.CTRL_T  # With shift
    TOGGLE_ALL_AND_ACCEPT = Keys.CTRL_T  # Double press
    TOGGLE_DOWN = Keys.CTRL_J  # Toggle + down
    TOGGLE_UP = Keys.CTRL_K  # Toggle + up

    # Query manipulation
    CLEAR_QUERY = Keys.CTRL_L
    CLEAR_SELECTION = Keys.BACKSPACE
    DELETE_CHAR = Keys.DELETE
    DELETE_CHAR_EOF = Keys.CTRL_D
    DELETE_WORD = Keys.meta('\x7f')  # Alt+Backspace
    DELETE_WORD_FORWARD = Keys.meta('d')  # Alt+d
    YANK = Keys.CTRL_Y
    UNIX_LINE_DISCARD = Keys.CTRL_U
    KILL_LINE = Keys.CTRL_K

    # History navigation
    PREVIOUS_HISTORY = Keys.CTRL_P
    NEXT_HISTORY = Keys.CTRL_N

    # Search
    REVERSE_SEARCH = Keys.CTRL_R
    FORWARD_SEARCH = Keys.CTRL_S

    # View options
    TOGGLE_PREVIEW = Keys.CTRL_Q
    TOGGLE_PREVIEW_WRAP = Keys.CTRL_Z
    TOGGLE_SORT = Keys.CTRL_O

    # Scrolling
    SCROLL_LEFT = Keys.LEFT
    SCROLL_RIGHT = Keys.RIGHT

    # Special
    PRINT_QUERY = Keys.CTRL_A  # Print query to stdout
    SEND_KEYS = Keys.meta(' ')  # Alt+Space


class VimKeys:
    """
    Key bindings for vim/neovim.

    Includes both Normal mode and Insert mode bindings.
    """

    # Mode switches
    NORMAL_MODE = Keys.ESCAPE
    INSERT_MODE = 'i'
    APPEND_MODE = 'a'
    INSERT_AT_LINE_START = 'I'
    APPEND_AT_LINE_END = 'A'
    INSERT_BELOW_LINE = 'o'
    INSERT_ABOVE_LINE = 'O'
    REPLACE_MODE = 'R'
    VISUAL_MODE = 'v'
    VISUAL_LINE_MODE = 'V'
    VISUAL_BLOCK_MODE = Keys.CTRL_V
    COMMAND_MODE = ':'

    # Movement (Normal mode)
    H = 'h'  # Left
    J = 'j'  # Down
    K = 'k'  # Up
    L = 'l'  # Right
    W = 'w'  # Word forward
    B = 'b'  # Word backward
    E = 'e'  # End of word
    GE = 'ge'  # Previous end of word
    GG = 'gg'  # Top of file
    G = 'G'  # Bottom of file / goto line
    ZERO = '0'  # Start of line
    CARET = '^'  # First non-whitespace
    DOLLAR = '$'  # End of line

    # Editing (Normal mode)
    X = 'x'  # Delete character
    XX = 'xx'  # Delete line
    DD = 'dd'  # Delete line
    DW = 'dw'  # Delete word
    D0 = 'd0'  # Delete to start of line
    D_DOLLAR = 'd$'  # Delete to end of line
    DG = 'dg'  # Delete to end of file
    DGG = 'dgg'  # Delete to top of file
    CW = 'cw'  # Change word
    CC = 'cc'  # Change line
    C0 = 'c0'  # Change to start of line
    C_DOLLAR = 'c$'  # Change to end of line
    CG = 'cg'  # Change to end of file
    CGG = 'cgg'  # Change to top of file
    YY = 'yy'  # Yank line
    YW = 'yw'  # Yank word
    Y0 = 'y0'  # Yank to start of line
    Y_DOLLAR = 'y$'  # Yank to end of line
    YG = 'yg'  # Yank to end of file
    YGG = 'ygg'  # Yank to top of file
    P = 'p'  # Paste after cursor
    P_CAP = 'P'  # Paste before cursor
    U = 'u'  # Undo
    REDO = Keys.CTRL_R  # Redo

    # Search and navigation
    SEARCH_FORWARD = '/'
    SEARCH_BACKWARD = '?'
    NEXT_MATCH = 'n'
    PREVIOUS_MATCH = 'N'
    STAR = '*'  # Search word under cursor
    HASH = '#'  # Search word under cursor (backward)

    # File operations
    WRITE = ':w'
    WRITE_AND_QUIT = ':wq'
    QUIT = ':q'
    QUIT_FORCE = ':q!'
    WRITE_FORCE = ':w!'
    READ_FILE = ':r'
    EDIT_FILE = ':e'

    # Window management
    SPLIT_HORIZONTAL = ':split'
    SPLIT_VERTICAL = ':vsplit'
    CLOSE_WINDOW = ':close'
    ONLY_WINDOW = ':only'
    NEXT_WINDOW = Keys.CTRL_W + 'w'  # Ctrl-w followed by w
    PREVIOUS_WINDOW = Keys.CTRL_W + 'p'
    WINDOW_UP = Keys.CTRL_W + 'k'
    WINDOW_DOWN = Keys.CTRL_W + 'j'
    WINDOW_LEFT = Keys.CTRL_W + 'h'
    WINDOW_RIGHT = Keys.CTRL_W + 'l'

    # Buffer management
    NEXT_BUFFER = ':bnext'
    PREVIOUS_BUFFER = ':bprevious'
    LIST_BUFFERS = ':ls'
    BUFFER_NUMBER = ':buffer'

    # Folding
    FOLD_OPEN = 'zo'
    FOLD_CLOSE = 'zc'
    FOLD_TOGGLE = 'za'
    FOLD_ALL = 'zM'
    UNFOLD_ALL = 'zR'

    # Marks
    SET_MARK = 'm'  # Followed by letter
    GOTO_MARK = '\''  # Followed by letter
    GOTO_MARK_LINE = '`'  # Followed by letter

    # Visual mode
    VISUAL_SWAP_START_END = 'o'  # Swap cursor and selection start
    VISUAL_BLOCK_SWAP_CORNERS = 'O'

    # Command mode shortcuts
    COMMAND_HISTORY_UP = Keys.UP
    COMMAND_HISTORY_DOWN = Keys.DOWN
    COMMAND_AUTO_COMPLETE = Keys.TAB

    # Insert mode
    INSERT_NORMAL = Keys.CTRL_O  # Execute one normal mode command
    INSERT_BACKSPACE = Keys.BACKSPACE
    INSERT_DELETE = Keys.DELETE
    INSERT_LEFT = Keys.LEFT
    INSERT_RIGHT = Keys.RIGHT
    INSERT_HOME = Keys.HOME
    INSERT_END = Keys.END
    INSERT_WORD_LEFT = Keys.CTRL_LEFT
    INSERT_WORD_RIGHT = Keys.CTRL_RIGHT
    INSERT_START_OF_LINE = Keys.CTRL_A
    INSERT_END_OF_LINE = Keys.CTRL_E
    INSERT_NEWLINE = Keys.ENTER
    INSERT_TAB = Keys.TAB

    # Insert mode completion
    INSERT_CTRL_N = Keys.CTRL_N  # Next completion match
    INSERT_CTRL_P = Keys.CTRL_P  # Previous completion match
    INSERT_CTRL_X_CTRL_N = Keys.CTRL_X + Keys.CTRL_N  # Next completion (whole lines)
    INSERT_CTRL_X_CTRL_P = Keys.CTRL_X + Keys.CTRL_P  # Previous completion (whole lines)

    # Helper methods
    @staticmethod
    def vim_command(command: str) -> str:
        """
        Create a vim command sequence.

        Args:
            command: Command without colon (e.g., 'wq', 'q!', 'e filename')

        Returns:
            Command sequence that can be sent to vim
        """
        return f':{command}\r'

    @staticmethod
    def goto_line(line_number: int) -> str:
        """
        Create a goto line command.

        Args:
            line_number: Line number to go to

        Returns:
            Command sequence to go to the specified line
        """
        return f'{line_number}G'


class TmuxKeys:
    """
    Key bindings for tmux.

    These are the default tmux key bindings when using the default prefix (Ctrl-b).
    """

    # Default prefix
    PREFIX = Keys.CTRL_B  # Can be reconfigured

    # Sessions
    PREFIX_LIST_SESSIONS = 's'  # List sessions
    PREFIX_NEW_SESSION = 'C'  # New session
    PREFIX_ATTACH_SESSION = '$'  # Prompt for session to attach
    PREFIX_DETACH_CLIENT = 'd'  # Detach client
    PREFIX_KILL_SESSION = '&'  # Kill session
    PREFIX_RENAME_SESSION = '$'  # Rename session

    # Windows (tabs)
    PREFIX_LIST_WINDOWS = 'w'  # List windows
    PREVIOS_WINDOW = 'p'  # Previous window
    NEXT_WINDOW = 'n'  # Next window
    PREFIX_LAST_WINDOW = 'l'  # Last window
    PREFIX_NEW_WINDOW = 'c'  # Create new window
    PREFIX_KILL_WINDOW = '&'  # Kill window
    PREFIX_RENAME_WINDOW = ','  # Rename window
    PREFIX_FIND_WINDOW = 'f'  # Find window
    PREFIX_SELECT_WINDOW = '0'  # Select window by number
    PREFIX_SELECT_WINDOW_1 = '1'
    PREFIX_SELECT_WINDOW_2 = '2'
    PREFIX_SELECT_WINDOW_3 = '3'
    PREFIX_SELECT_WINDOW_4 = '4'
    PREFIX_SELECT_WINDOW_5 = '5'
    PREFIX_SELECT_WINDOW_6 = '6'
    PREFIX_SELECT_WINDOW_7 = '7'
    PREFIX_SELECT_WINDOW_8 = '8'
    PREFIX_SELECT_WINDOW_9 = '9'

    # Panes
    PREFIX_SPLIT_HORIZONTAL = '"'  # Split window horizontally
    PREFIX_SPLIT_VERTICAL = '%'  # Split window vertically
    PREFIX_KILL_PANE = 'x'  # Kill pane
    PREFIX_SWAP_PANE_PREVIOUS = '{'  # Swap pane with previous
    PREFIX_SWAP_PANE_NEXT = '}'  # Swap pane with next
    PREFIX_PANE_LEFT = Keys.LEFT  # Resize pane left
    PREFIX_PANE_RIGHT = Keys.RIGHT  # Resize pane right
    PREFIX_PANE_UP = Keys.UP  # Resize pane up
    PREFIX_PANE_DOWN = Keys.DOWN  # Resize pane down
    PREFIX_LAYOUT_EVEN_HORIZONTAL = 'M-H'  # Even horizontal layout
    PREFIX_LAYOUT_EVEN_VERTICAL = 'M-v'  # Even vertical layout
    PREFIX_LAYOUT_MAIN_HORIZONTAL = 'M-1'  # Main horizontal layout
    PREFIX_LAYOUT_MAIN_VERTICAL = 'M-2'  # Main vertical layout
    PREFIX_LAYOUT_TILED = 'M-Space'  # Tiled layout

    # Pane navigation
    PREFIX_SELECT_PANE_UP = Keys.UP  # Select pane above
    PREFIX_SELECT_PANE_DOWN = Keys.DOWN  # Select pane below
    PREFIX_SELECT_PANE_LEFT = Keys.LEFT  # Select pane left
    PREFIX_SELECT_PANE_RIGHT = Keys.RIGHT  # Select pane right
    PREFIX_SELECT_PANE_LAST = ';'  # Select last pane
    PREFIX_SELECT_PANE_LAST_ALT = 'l'  # Select last pane (alternative)

    # Copy mode
    PREFIX_COPY_MODE = '['  # Enter copy mode
    PREFIX_PASTE_BUFFER = ']'  # Paste buffer
    PREFIX_LIST_BUFFERS = '#'  # List buffers
    PREFIX_CHOOSE_BUFFER = '"'  # Choose buffer
    PREFIX_DELETE_BUFFER = '-'  # Delete buffer
    PREFIX_SAVE_BUFFER = '='  # Save buffer
    PREFIX_APPEND_BUFFER = '+'  # Append buffer

    # Clock
    PREFIX_CLOCK_MODE = 't'  # Clock mode

    # Help
    PREFIX_LIST_KEYS = '?'  # List key bindings

    # Command prompt
    PREFIX_COMMAND_PROMPT = ':'  # Command prompt

    # Misc
    PREFIX_REFRESH_CLIENT = 'r'  # Refresh client
    PREFIX_SOURCE_FILE = ':'  # Source file (with command prompt)

    # Prefix variations
    ALT_PREFIX = Keys.CTRL_A  # Common alternative prefix

    @staticmethod
    def send_prefix_and_key(prefix_key: str, key: str) -> str:
        """
        Create a tmux prefix + key sequence.

        Args:
            prefix_key: Prefix key sequence (usually TmuxKeys.PREFIX)
            key: Key to send after prefix

        Returns:
            Complete key sequence
        """
        return prefix_key + key


class LazygitKeys:
    """
    Key bindings for lazygit (terminal Git UI).

    These are the default key bindings in lazygit.
    """

    # Navigation
    UP = Keys.UP
    DOWN = Keys.DOWN
    LEFT = Keys.LEFT
    RIGHT = Keys.RIGHT
    PAGE_UP = Keys.PAGE_UP
    PAGE_DOWN = Keys.PAGE_DOWN
    HOME = Keys.HOME
    END = Keys.END

    # Global
    QUIT = 'q'
    QUIT_ALL = Keys.CTRL_C
    CONFIRM = Keys.ENTER
    CANCEL = Keys.ESCAPE

    # Panels (sections)
    STATUS = '1'  # Status panel
    FILES = '2'  # Files panel
    BRANCHES = '3'  # Branches panel
    COMMITS = '4'  # Commits panel
    STASH = '5'  # Stash panel

    # Navigation between panels
    NEXT_PANEL = Keys.TAB
    PREVIOUS_PANEL = Keys.SHIFT_TAB
    PARENT_PANEL = Keys.ESCAPE

    # Files panel
    STAGE_FILE = Keys.SPACE
    STAGE_ALL_FILES = 'a'
    UNSTAGE_FILE = Keys.BACKSPACE
    UNSTAGE_ALL_FILES = 'A'
    COMMIT_FILES = 'c'
    COMMIT_FILES_WITH_EDITOR = 'C'
    AMEND_LAST_COMMIT = 'A'
    REVERT_COMMIT = 'g'  # With confirmation
    CREATE_FIXUP_COMMIT = 'f'
    SQUASH_DOWN = 's'
    RENAME_COMMIT = 'r'
    DROP_COMMIT = 'd'
    EDIT_COMMIT = 'e'
    PULL = 'p'
    PUSH = 'P'
    PUSH_FORCE = 'F'
    FETCH = 'f'
    CREATE_BRANCH = 'n'
    CHECKOUT_BRANCH = 'c'
    CHECKOUT_DETACHED = 'd'
    MERGE_BRANCH = 'm'
    REBASE_BRANCH = 'r'
    FAST_FORWARD_BRANCH = 'f'
    DELETE_BRANCH = 'D'
    VIEW_LOG_OPTIONS = 'l'

    # Commits panel
    VIEW_COMMIT = Keys.ENTER
    VIEW_COMMIT_FILES = 'f'
    SQUASH_COMMIT = 's'
    RENAME_COMMIT = 'r'
    DELETE_COMMIT = 'd'
    REVERT_COMMIT = 'g'
    EDIT_COMMIT = 'e'
    AMEND_COMMIT = 'A'
    PICK_COMMIT = 'p'
    REWORD_COMMIT = 'r'
    EDIT_COMMIT = 'e'
    SQUASH_COMMIT = 's'
    FIXUP_COMMIT = 'f'
    DROP_COMMIT = 'd'

    # Branches panel
    CHECKOUT_BRANCH = Keys.ENTER
    CREATE_BRANCH = 'n'
    DELETE_BRANCH = 'D'
    MERGE_BRANCH = 'm'
    REBASE_BRANCH = 'r'
    RENAME_BRANCH = 'r'

    # Stash panel
    APPLY_STASH = Keys.ENTER
    POP_STASH = 'g'
    DROP_STASH = 'd'
    VIEW_STASH_FILES = 'f'

    # Search
    START_SEARCH = '/'
    CONTINUE_SEARCH = 'n'
    REVERSE_SEARCH = 'N'

    # Filter
    FILTER_FILES = 'f'
    REMOVE_FILE_FILTER = Keys.CTRL_F

    # Other
    SHOW_OPTIONS = 'x'  # Show/hide options
    OPEN_CONFIG = ','  # Open config file
    SHOW_RECENT_REPOS = 's'
    TOGGLE_FILE_VIEW = 'v'  # Toggle between tree and list view
    CREATE_PULL_REQUEST = 'o'  # Open pull request in browser

    # Bulk actions (requires selecting multiple files first)
    STAGE_SELECTED = 's'
    UNSTAGE_SELECTED = 'u'
    COMMIT_SELECTED = 'c'
    DELETE_SELECTED = 'd'

    @staticmethod
    def ctrl_char(char: str) -> str:
        """
        Create a Ctrl key combination for lazygit.

        Args:
            char: Character to combine with Ctrl

        Returns:
            Ctrl + char sequence
        """
        return Keys.ctrl(char)


class HtopKeys:
    """
    Key bindings for htop (interactive process viewer).

    These are the default key bindings in htop.
    """

    # Navigation
    UP = Keys.UP
    DOWN = Keys.DOWN
    LEFT = Keys.LEFT
    RIGHT = Keys.RIGHT
    PAGE_UP = Keys.PAGE_UP
    PAGE_DOWN = Keys.PAGE_DOWN
    HOME = Keys.HOME
    END = Keys.END

    # Global
    QUIT = 'q'
    HELP = Keys.F1
    INC_PAGE = 'h'
    DEC_PAGE = 'l'

    # Setup
    SETUP = Keys.F2  # Setup
    SETUP_LEFT = Keys.LEFT
    SETUP_RIGHT = Keys.RIGHT
    SETUP_UP = Keys.UP
    SETUP_DOWN = Keys.DOWN
    SETUP_OK = Keys.ENTER
    SETUP_CANCEL = Keys.ESCAPE

    # Search
    SEARCH = Keys.F3  # Incremental search
    SEARCH_AGAIN = Keys.F3
    INVERT_SORT = 'I'

    # Sort options
    SORT_BY_CPU = 'P'
    SORT_BY_MEMORY = 'M'
    SORT_BY_TIME = 'T'
    SORT_BY_USER = 'U'
    SORT_BY_PID = 'K'

    # Process actions
    KILL = Keys.F9  # Kill process
    KILL_SIGNAL_1 = '1'  # SIGHUP
    KILL_SIGNAL_2 = '2'  # SIGINT
    KILL_SIGNAL_3 = '3'  # SIGQUIT
    KILL_SIGNAL_4 = '4'  # SIGILL
    KILL_SIGNAL_5 = '5'  # SIGTRAP
    KILL_SIGNAL_6 = '6'  # SIGABRT
    KILL_SIGNAL_7 = '7'  # SIGBUS
    KILL_SIGNAL_8 = '8'  # SIGFPE
    KILL_SIGNAL_9 = '9'  # SIGKILL
    KILL_SIGNAL_10 = '0'  # SIGUSR1
    KILL_SIGNAL_11 = 'a'  # SIGUSR2
    KILL_SIGNAL_12 = 'b'  # SIGPIPE
    KILL_SIGNAL_13 = 'c'  # SIGALRM
    KILL_SIGNAL_14 = 'd'  # SIGTERM
    KILL_SIGNAL_15 = 'e'  # SIGSTKFLT
    KILL_SIGNAL_16 = 'f'  # SIGCHLD
    KILL_SIGNAL_17 = 'g'  # SIGCONT
    KILL_SIGNAL_18 = 'h'  # SIGSTOP
    KILL_SIGNAL_19 = 'i'  # SIGTSTP
    KILL_SIGNAL_20 = 'j'  # SIGTTIN
    KILL_SIGNAL_21 = 'k'  # SIGTTOU
    KILL_SIGNAL_22 = 'l'  # SIGURG
    KILL_SIGNAL_23 = 'm'  # SIGXCPU
    KILL_SIGNAL_24 = 'n'  # SIGXFSZ
    KILL_SIGNAL_25 = 'o'  # SIGVTALRM
    KILL_SIGNAL_26 = 'p'  # SIGPROF
    KILL_SIGNAL_27 = 'q'  # SIGWINCH
    KILL_SIGNAL_28 = 'r'  # SIGIO
    KILL_SIGNAL_29 = 's'  # SIGPWR
    KILL_SIGNAL_30 = 't'  # SIGSYS
    KILL_SIGNAL_31 = 'u'  # SIGUNUSED

    # Other process actions
    RENICE = 'r'  # Renice process
    FOLLOW = 'F'  # Follow process
    TAG = 't'  # Tag process
    UNTAG = 'u'  # Untag process
    SHOW_TAGS = Keys.TAB  # Show tags

    # Tree view
    TREE_VIEW = 't'  # Toggle tree view
    COLLAPSE_PROCESS = Keys.LEFT  # Collapse process tree
    EXPAND_PROCESS = Keys.RIGHT  # Expand process tree

    # Display options
    TOGGLE_PATHS = 'P'
    HIDE_KERNEL_THREADS = 'K'
    HIDE_USERLAND_THREADS = 'H'
    DISPLAY_THREADS = 'T'
    SHOW_FULL_COMMAND = 'c'
    TOGGLE_ACTIVE_PROCESSES = 'a'

    # Color modes
    COLOR_MONOCHROME = '1'
    COLOR_LOW = '2'
    COLOR_MEDIUM = '3'
    COLOR_HIGH = '4'
    COLOR_LARGE = '5'
    COLOR_DEFAULT = '0'

    # User filtering
    FILTER_BY_USER = 'U'

    # Other
    REFRESH = Keys.F5
    UPDATE_PROCESSES = 'd'
    STRIP_EXE_FROM_CMDLINE = 'C'

    @staticmethod
    def kill_signal(signal_num: int) -> str:
        """
        Create kill signal sequence.

        Args:
            signal_num: Signal number (1-31)

        Returns:
            Key sequence for the specified signal
        """
        if signal_num == 9:
            return '9'
        elif signal_num == 15:
            return 'e'
        elif 1 <= signal_num <= 31:
            # Map to correct character based on htop's mapping
            signal_chars = [
                '', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u'
            ]
            return signal_chars[signal_num]
        else:
            raise ValueError(f"Signal number must be between 1 and 31, got {signal_num}")


class LessKeys:
    """
    Key bindings for less/more pagers.

    These are the default key bindings in less (many work in more too).
    """

    # Navigation
    FORWARD_LINE = Keys.ENTER  # or 'e', 'j'
    FORWARD_HALF_SCREEN = Keys.SPACE  # or 'f', 'z'
    FORWARD_FULL_SCREEN = 'f'
    FORWARD_PAGE = Keys.SPACE  # or 'f'
    BACKWARD_LINE = 'y'  # or 'k'
    BACKWARD_HALF_SCREEN = 'u'
    BACKWARD_FULL_SCREEN = 'b'
    BACKWARD_PAGE = 'b'
    BACKWARD_HALF_WINDOW = 'u'
    BACKWARD_WINDOW = 'w'
    FORWARD_HALF_WINDOW = 'd'

    # Jump to specific positions
    JUMP_PERCENT = 'p'  # Jump to N% into file
    JUMP_LINE = 'g'  # Jump to line number
    JUMP_START = 'g'  # or '<', 'GG'
    JUMP_END = 'G'  # or '>'
    JUMP_N_SCREENS_FORWARD = 'z'  # Forward N screens
    JUMP_N_SCREENS_BACKWARD = 'w'  # Backward N screens

    # Scrolling
    SCROLL_LEFT = Keys.LEFT  # or 'h'
    SCROLL_RIGHT = Keys.RIGHT  # or 'l'
    SCROLL_LEFT_HALF = Keys.LEFT  # With H modifier
    SCROLL_RIGHT_HALF = Keys.RIGHT  # With L modifier

    # Search
    SEARCH_FORWARD = '/'  # Forward search
    SEARCH_BACKWARD = '?'  # Backward search
    REPEAT_SEARCH = 'n'  # Repeat forward search
    REPEAT_SEARCH_BACKWARD = 'N'  # Repeat backward search
    REPEAT_SEARCH_ALL = '&n'  # Repeat search through all open files
    REPEAT_SEARCH_BACKWARD_ALL = '&N'  # Repeat backward search through all files

    # File operations
    NEXT_FILE = ':n'  # Next file
    PREVIOUS_FILE = ':p'  # Previous file
    FIRST_FILE = ':f'  # First file
    LAST_FILE = ':l'  # Last file
    LIST_FILES = '='  # Show file info
    LIST_FILES_OPEN = '*:f'  # List all open files
    EDIT_FILE = 'v'  # Edit current file with $EDITOR
    EXAMINE_FILE = ':e'  # Examine new file

    # Marks
    SET_MARK = 'm'  # Set mark (followed by letter)
    GOTO_MARK = '\''  # Go to mark (followed by letter)
    GOTO_MARK_SAME_LINE = '\''  # Go to mark at same line

    # Display options
    TOGGLE_LINE_NUMBERS = '-N'  # or '-N'
    TOGGLE_QUIET = 'Q'  # Quiet mode
    TOGGLE_VERBOSE = '=v'  # Verbose mode
    TOGGLE_CASE_SENSITIVE = '-i'  # Case insensitive search
    TOGGLE_WRAP_MODE = '-S'  # Don't wrap long lines
    TOGGLE_TILDE_DISPLAY = '~'  # Show tildes after end of file

    # Filter
    FILTER = '&'  # Filter lines
    FILTER_RESET = '|'

    # History
    COMMAND_HISTORY = Keys.TAB  # Show command history
    COMMAND_HISTORY_PREV = Keys.UP
    COMMAND_HISTORY_NEXT = Keys.DOWN

    # Misc
    HELP = 'h'  # Help
    VERSION = '_V'  # Version
    COMMAND_PROMPT = ':'  # Command prompt
    SHELL = 's'  # Shell escape
    QUIT = 'q'
    QUIT_FORCE = 'Q'

    # Mouse support (if enabled)
    # Note: Mouse sequences are typically handled by the terminal, not sent as escape sequences
    MOUSE_CLICK = '\x1b[M '  # Mouse button 1 click (simplified)
    MOUSE_WHEEL_UP = '\x1b[M`'  # Mouse wheel up (simplified)
    MOUSE_WHEEL_DOWN = '\x1b[Ma'  # Mouse wheel down (simplified)

    @staticmethod
    def goto_percentage(percent: int) -> str:
        """
        Create a goto percentage command.

        Args:
            percent: Percentage to jump to (0-100)

        Returns:
            Command sequence
        """
        return f'{percent}p'

    @staticmethod
    def goto_line(line_number: int) -> str:
        """
        Create a goto line command.

        Args:
            line_number: Line number to jump to

        Returns:
            Command sequence
        """
        return f'{line_number}g'


class NcduKeys:
    """
    Key bindings for ncdu (NCurses Disk Usage).

    These are the default key bindings in ncdu.
    """

    # Navigation
    UP = Keys.UP  # or 'k'
    DOWN = Keys.DOWN  # or 'j'
    LEFT = Keys.LEFT  # or 'h'
    RIGHT = Keys.RIGHT  # or 'l', Keys.ENTER
    PARENT = Keys.LEFT  # Go to parent directory
    ENTER_SUBDIR = Keys.RIGHT  # or Keys.ENTER
    PAGE_UP = Keys.PAGE_UP
    PAGE_DOWN = Keys.PAGE_DOWN
    HOME = Keys.HOME  # or 'g'
    END = Keys.END  # or 'G'

    # Selection and marking
    MARK_FILE = Keys.SPACE  # Mark/unmark file
    MARK_PARENT = '<'  # Mark files in parent dir
    MARK_ALL = '>'  # Mark all files in current dir
    MARK_INVERT = 'b'  # Invert marks
    MARK_RECURSIVE = 's'  # Mark files recursively
    MARK_PATTERN = 'm'  # Mark files matching pattern

    # Deletion
    DELETE_FILE = 'd'  # Delete file or directory
    DELETE_SELECTED = 'D'  # Delete selected files

    # File operations
    FILE_INFO = 'i'  # Show file info
    FILE_INFO_EXTENDED = 'I'  # Show extended file info
    OPEN_FILE = Keys.ENTER  # Open file with $PAGER
    OPEN_SHELL = '!'  # Open shell in current directory
    EDIT_FILE = 'e'  # Open file with $EDITOR

    # Sorting
    SORT_BY_NAME = 'n'
    SORT_BY_SIZE = 's'
    SORT_BY_ITEMS = 'a'  # Apparent size
    SORT_BY_MTIME = 'm'  # Modification time
    SORT_BY_CTIME = 'c'  # Creation time
    REVERSE_SORT = 'r'
    SORT_LETTERS_FIRST = 't'
    SORT_DIRS_FIRST = '.'

    # Display options
    TOGGLE_DISPLAY = 'g'  # Toggle between graph and numbers
    TOGGLE_PERCENTAGE = '%'  # Show/hide percentage
    TOGGLE_GRAPH = 'g'
    TOGGLE_APPARENT_SIZE = 'a'
    TOGGLE_BARS = 'u'
    TOGGLE_FILE_COUNT = 'c'
    TOGGLE_HIDDEN = 'h'  # Show/hide hidden files
    TOGGLE_IGNORE = 'i'  # Show/hide ignored files

    # Recalculation
    RECALCULATE = 'r'  # Recalculate current directory
    RECALCULATE_ALL = 'R'  # Recalculate all directories

    # Save and load
    SAVE_SCAN = '^S'  # Save scan to file
    LOAD_SCAN = '^L'  # Load scan from file
    DELETE_SCAN = '^D'  # Delete saved scan

    # Config
    CONFIG = ','  # Open config

    # Help and quit
    HELP = '?'  # Help
    QUIT = 'q'
    QUIT_FORCE = 'Q'

    # Other
    REFRESH = Keys.CTRL_L  # Refresh screen
    COLLAPSE_ALL = Keys.CTRL_K  # Collapse all dirs
    EXPAND_ALL = Keys.CTRL_E  # Expand all dirs

    @staticmethod
    def ctrl_key(key: str) -> str:
        """
        Create a Ctrl key combination for ncdu.

        Args:
            key: Key to combine with Ctrl

        Returns:
            Ctrl + key sequence
        """
        return Keys.ctrl(key)