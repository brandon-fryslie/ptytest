# ptytest

**Real terminal testing framework** - Test interactive CLI applications with actual keystrokes.

ptytest lets you write automated tests for interactive terminal applications (like tmux keybindings, zsh ZLE widgets, or any interactive CLI) by sending real keystrokes and verifying actual terminal output. No mocks, no fakes - just real process control via PTY.

## Features

- **Real Keystrokes**: Send actual key sequences (Ctrl-b, Escape codes, etc.)
- **Real Output**: Verify actual terminal content, not mocked responses
- **Direct PTY Testing**: Test any CLI application directly via PtySession
- **tmux Integration**: Full control over tmux sessions, panes, and state
- **ZLE Support**: Test zsh line editor widgets with escape sequences
- **Pytest Plugin**: Auto-registered fixtures for easy test writing
- **App-Specific Keys**: Built-in helpers for fzf, vim, and more
- **Web Visualization**: Real-time browser terminal view with xterm.js (optional)
- **Un-gameable**: Tests verify real behavior - they fail when functionality breaks

## Installation

```bash
# Using pip
pip install ptytest

# Using uv
uv pip install ptytest

# From source
git clone https://github.com/brandon-fryslie/ptytest
cd ptytest
pip install -e .
```

### Requirements

- Python 3.8+
- macOS or Linux
- tmux (only for TmuxSession; PtySession works without it)

```bash
# Install tmux on macOS (optional, for TmuxSession)
brew install tmux

# Install tmux on Ubuntu/Debian (optional, for TmuxSession)
sudo apt install tmux
```

## Quick Start

### Testing Any CLI with PtySession

```python
from ptytest import PtySession, Keys

def test_fzf_filtering(pty_session_factory):
    """Test fzf fuzzy finder filtering."""
    # Spawn fzf with some items
    session = pty_session_factory(["bash", "-c", "echo -e 'apple\\nbanana\\ncherry' | fzf"])

    # Wait for fzf to start
    assert session.verify_text_appears("apple")

    # Type search query
    session.send_keys("ban", literal=True)

    # Verify filtering works
    assert session.verify_text_appears("banana")

def test_ncdu_navigation(pty_session_factory):
    """Test ncdu disk analyzer."""
    session = pty_session_factory(["ncdu", "/tmp"])

    # Navigate with arrow keys
    session.send_raw(Keys.DOWN)
    session.send_raw(Keys.ENTER)  # Enter directory
    session.send_raw(Keys.LEFT)   # Back to parent

    # Quit
    session.send_keys("q", literal=True)
```

### Testing tmux with TmuxSession

```python
import pytest
from ptytest import TmuxSession, Keys

def test_tmux_help_keybinding(tmux_session):
    """Test that Ctrl-b h shows help pane."""
    # Send Ctrl-b h
    tmux_session.send_prefix_key('h')

    # Verify help pane appeared
    assert tmux_session.get_pane_count() == 2

    # Verify content
    content = tmux_session.get_pane_content()
    assert "PANES" in content

def test_zsh_reverse_search(tmux_session):
    """Test Ctrl-R reverse history search."""
    # Send Ctrl-R
    tmux_session.send_raw(Keys.CTRL_R)

    # Verify search prompt appeared
    assert tmux_session.verify_text_appears("bck-i-search")

    # Cancel with Ctrl-G
    tmux_session.send_raw(Keys.CTRL_G)
```

Run tests with pytest:

```bash
pytest -v
```

## Usage

### PtySession - Test Any CLI

PtySession spawns processes directly via PTY, perfect for testing any interactive CLI:

```python
from ptytest import PtySession, Keys

# Using context manager (recommended)
with PtySession(["python", "-i"]) as session:
    session.send_keys("2 + 2")
    assert session.verify_text_appears("4")

# Using factory fixture
def test_my_cli(pty_session_factory):
    session = pty_session_factory(["my-cli", "--interactive"])
    session.send_keys("help")
    assert session.verify_text_appears("Commands")
```

### TmuxSession - Test tmux

```python
from ptytest import TmuxSession

# Using context manager (recommended)
with TmuxSession() as session:
    session.send_keys("echo hello")
    assert "hello" in session.get_pane_content()

# Manual cleanup
session = TmuxSession()
try:
    session.send_prefix_key('h')
    assert session.get_pane_count() == 2
finally:
    session.cleanup()
```

### Sending Keys

```python
from ptytest import TmuxSession, Keys

with TmuxSession() as session:
    # Send tmux prefix + key (Ctrl-b h)
    session.send_prefix_key('h')

    # Send raw escape sequences (for ZLE widgets, etc.)
    session.send_raw('\x1bD')  # ESC D (Option+Shift+D on macOS)
    session.send_raw(Keys.CTRL_R)  # Ctrl-R

    # Send shell commands
    session.send_keys("ls -la")  # Types and presses Enter
    session.send_keys("hello", literal=True)  # Types without Enter
```

### Key Constants

```python
from ptytest import Keys

# Control characters
Keys.CTRL_C    # '\x03' - Interrupt
Keys.CTRL_R    # '\x12' - Reverse search
Keys.CTRL_Z    # '\x1a' - Suspend

# Special keys
Keys.ESCAPE    # '\x1b'
Keys.ENTER     # '\r'
Keys.TAB       # '\t'

# Arrow keys
Keys.UP, Keys.DOWN, Keys.LEFT, Keys.RIGHT

# Function keys
Keys.F1, Keys.F2, ..., Keys.F12

# Create Meta/Alt combinations
Keys.meta('d')  # Alt+D -> '\x1bd'
Keys.meta('D')  # Alt+Shift+D -> '\x1bD'

# Create Ctrl combinations
Keys.ctrl('c')  # Ctrl+C -> '\x03'
```

### Verifying Output

```python
with TmuxSession() as session:
    # Get pane content
    content = session.get_pane_content()

    # Get specific pane
    pane_ids = session.get_pane_ids()
    help_content = session.get_pane_content(pane_ids[1])

    # Wait for text to appear
    if session.verify_text_appears("Ready", timeout=5.0):
        print("App is ready!")

    # Assert text appears (raises on timeout)
    session.wait_for_text("Success", timeout=2.0)

    # Check pane count
    assert session.get_pane_count() == 2

    # Check pane dimensions
    height = session.get_pane_height()
    width = session.get_pane_width()
```

### Pane Management

```python
with TmuxSession() as session:
    # Split panes
    session.split_window("-h")  # Horizontal split (left/right)
    session.split_window("-v")  # Vertical split (top/bottom)

    # Get pane info
    pane_count = session.get_pane_count()
    pane_ids = session.get_pane_ids()

    # Get tmux options
    help_pane_id = session.get_global_option("@help_pane_id")
```

## Pytest Integration

ptytest automatically registers as a pytest plugin, providing fixtures:

### PtySession Fixtures (for any CLI)

```python
# Test any CLI with pty_session (spawns bash by default)
def test_something(pty_session):
    pty_session.send_keys("ls")
    assert pty_session.verify_text_appears("README")

# Factory for custom commands
def test_fzf(pty_session_factory):
    session = pty_session_factory(["fzf", "--version"])
    assert session.verify_text_appears("fzf")

# Factory with custom dimensions
def test_vim(pty_session_factory):
    session = pty_session_factory(["vim"], width=80, height=24)
    session.send_raw(Keys.ESCAPE)
    session.send_keys(":q!", literal=True)
```

### TmuxSession Fixtures

```python
# Standard fixture with user's tmux config
def test_something(tmux_session):
    tmux_session.send_prefix_key('h')

# Minimal config (no ~/.tmux.conf)
def test_basic(tmux_session_minimal):
    tmux_session_minimal.send_keys("echo test")

# Factory for multiple sessions
def test_multi(tmux_session_factory):
    session1 = tmux_session_factory()
    session2 = tmux_session_factory(width=80, height=24)
```

### Markers

```python
import pytest

@pytest.mark.keybinding
def test_ctrl_b_h(tmux_session):
    """Test a tmux keybinding."""
    pass

@pytest.mark.zle
def test_zsh_widget(tmux_session):
    """Test a ZLE widget."""
    pass

@pytest.mark.slow
def test_long_workflow(tmux_session):
    """Mark slow tests."""
    pass
```

Run specific test categories:

```bash
pytest -m keybinding    # Only keybinding tests
pytest -m zle           # Only ZLE tests
pytest -m direct_pty    # Only PtySession tests
pytest -m "not slow"    # Skip slow tests
```

### Extended Key Classes

```python
from ptytest import Keys, FzfKeys, VimKeys

# Standard keys
Keys.CTRL_C, Keys.ESCAPE, Keys.ENTER, Keys.TAB
Keys.UP, Keys.DOWN, Keys.LEFT, Keys.RIGHT
Keys.F1, Keys.F2, ..., Keys.F12

# Arrow key modifiers
Keys.SHIFT_UP, Keys.SHIFT_DOWN      # Select in many apps
Keys.CTRL_LEFT, Keys.CTRL_RIGHT     # Word navigation
Keys.ALT_UP, Keys.ALT_DOWN          # Alt+arrow

# Helpers
Keys.meta('d')   # Alt+D -> '\x1bd'
Keys.ctrl('c')   # Ctrl+C -> '\x03'

# fzf-specific
FzfKeys.ACCEPT              # Enter to select
FzfKeys.TOGGLE              # Tab to toggle selection
FzfKeys.TOGGLE_ALL          # Ctrl+A
FzfKeys.CLEAR_QUERY         # Ctrl+U

# vim-specific
VimKeys.NORMAL_MODE         # Escape
VimKeys.QUIT                # :q
VimKeys.SAVE_QUIT           # :wq
VimKeys.vim_command('wq')   # :wq + Enter
```

## Examples

### Testing tmux Keybindings

```python
@pytest.mark.keybinding
def test_ctrl_b_h_toggle(tmux_session):
    """Test help pane toggle."""
    # Toggle on
    tmux_session.send_prefix_key('h')
    assert tmux_session.get_pane_count() == 2

    # Toggle off
    tmux_session.send_prefix_key('h')
    assert tmux_session.get_pane_count() == 1
```

### Testing ZLE Widgets

```python
@pytest.mark.zle
def test_zaw_widget(tmux_session):
    """Test zaw plugin activation."""
    import time
    time.sleep(0.5)  # Wait for shell init

    # Send Option+Shift+D (zaw-rad-dev)
    tmux_session.send_raw('\x1bD')
    time.sleep(0.5)

    # Verify widget activated
    content = tmux_session.get_pane_content()
    assert "bad set of key/value pairs" not in content  # No error

    # Dismiss with Escape
    tmux_session.send_raw(Keys.ESCAPE)
```

### End-to-End Workflow

```python
@pytest.mark.e2e
@pytest.mark.slow
def test_complete_workflow(tmux_session):
    """Test a complete user workflow."""
    # Setup
    tmux_session.split_window("-h")
    assert tmux_session.get_pane_count() == 2

    # Run command in first pane
    tmux_session.send_keys("echo 'Hello from pane 1'")

    # Switch to second pane
    tmux_session.send_prefix_key('o')

    # Run command in second pane
    tmux_session.send_keys("echo 'Hello from pane 2'")

    # Verify both commands executed
    content = tmux_session.get_pane_content()
    assert "Hello from pane 2" in content
```

### Testing AI CLI Tools

ptytest excels at testing AI-powered CLI tools with non-deterministic outputs. See `examples/test_claude_code.py` for a complete example.

```python
@pytest.mark.claude_code
def test_ai_cli_interaction(pty_session_factory):
    """Test Claude Code CLI - demonstrates AI tool testing patterns."""
    # Launch AI CLI
    session = pty_session_factory(["claude"], timeout=30)

    # Wait for ready (AI tools may take time to initialize)
    assert session.verify_text_appears(">", timeout=30)

    # Send a prompt
    session.send_keys("What is 2+2? Answer with just the number.")
    time.sleep(5)  # Wait for streaming response

    # Non-deterministic assertions - check for concepts, not exact text
    content = session.get_content()
    assert len(content) > 100, "No response received"
    assert "error" not in content.lower() or "4" in content

    # Test context retention across turns
    session.send_keys("What did I just ask you?")
    time.sleep(5)
    content = session.get_content()
    assert "2" in content or "math" in content.lower()
```

#### Docker Mode for Tool Use Testing

For AI tools that modify files or run commands, use Docker for safety:

```python
@pytest.mark.docker
def test_ai_tool_use_safely(docker_image, temp_workspace):
    """Test AI tool use in isolated Docker container."""
    cmd = [
        "docker", "run", "--rm", "-i",
        "-e", f"ANTHROPIC_API_KEY={os.environ['ANTHROPIC_API_KEY']}",
        "-v", f"{temp_workspace}:/workspace",
        "-w", "/workspace",
        docker_image, "claude"
    ]

    with PtySession(cmd, timeout=30) as session:
        assert session.verify_text_appears(">", timeout=30)

        # Ask AI to create a file
        session.send_keys("Create a file named test.txt with 'Hello'")
        time.sleep(5)

        # Handle tool approval if needed
        content = session.get_content()
        if "approve" in content.lower():
            session.send_keys("y")
            time.sleep(3)

        # Verify file was created
        assert (temp_workspace / "test.txt").exists()
```

**Key patterns for AI CLI testing:**

1. **Use generous timeouts** - AI responses take time to generate
2. **Non-deterministic assertions** - Check for presence of concepts/keywords, not exact text
3. **Verify side effects** - For tool use, check files created or commands run
4. **Docker for safety** - Isolate filesystem and command execution
5. **Skip gracefully** - Tests should skip if API keys or prerequisites are missing

See `examples/test_claude_code.py` for complete examples with both direct and Docker modes.

## Why "Un-gameable" Tests?

Traditional unit tests can be "gamed" with mocks that don't reflect real behavior. ptytest tests are un-gameable because they:

1. **Spawn real processes** - Actual tmux/shell processes, not mocks
2. **Send real keystrokes** - Literal bytes sent to the PTY
3. **Verify real output** - Actual terminal content captured
4. **Test observable outcomes** - Pane counts, content, state changes

If a ptytest test passes, the functionality actually works. If it fails, something is genuinely broken.


## Web Visualization

Visualize your terminal sessions in real-time through your web browser using xterm.js. Perfect for demos, documentation, and debugging.

### Installation

Install the visualization dependencies:

```bash
# Development installation
uv pip install -e ".[viz]"

# Production installation
pip install ptytest[viz]
```

### Basic Usage

Enable visualization by adding `enable_viz=True` to your PtySession:

```python
from ptytest import PtySession

# Enable web visualization
with PtySession(['bash'], enable_viz=True, viz_port=8080) as session:
    session.send_keys('ls -la')
    session.send_keys('echo "Hello from ptytest!"')
    # Open http://localhost:8080 in browser to view
```

The visualization server will start automatically and display terminal output in your browser with full ANSI color support.

### Features

- **Real-time streaming**: See terminal output as it happens
- **ANSI color support**: Full color rendering via xterm.js
- **Multi-viewer**: Multiple browsers can watch the same session
- **Auto-reconnect**: Browser reconnects automatically if connection drops
- **Read-only**: Visualization is for viewing only (no keyboard input from browser)
- **Zero overhead**: Disabled by default, only runs when `enable_viz=True`

### Example: Visualizing fzf

```python
from ptytest import PtySession

# Visualize fzf fuzzy finder
cmd = ['bash', '-c', 'echo -e "apple\\nbanana\\ncherry" | fzf']

with PtySession(cmd, enable_viz=True, viz_port=8080) as session:
    # Wait for fzf to start
    session.verify_text_appears('3/3')
    
    # Type search query
    session.send_keys('ban', literal=True)
    
    # Watch the filtering happen in your browser!
    # Open http://localhost:8080
```

### Configuration

```python
# Custom port
with PtySession(['bash'], enable_viz=True, viz_port=9090) as session:
    pass  # Server runs on http://localhost:9090

# Default port is 8080
with PtySession(['bash'], enable_viz=True) as session:
    pass  # Server runs on http://localhost:8080
```

### Use Cases

**Demos and Documentation**:
```python
# Record a demo session
with PtySession(['bash'], enable_viz=True) as session:
    session.send_keys('# This is a demo')
    session.send_keys('ls -la')
    time.sleep(10)  # Keep alive for viewing
```

**Debugging Tests**:
```python
# Enable visualization for failing tests
def test_my_cli(pty_session_factory):
    session = pty_session_factory(['my-cli'], enable_viz=True, viz_port=8080)
    # Debug by watching http://localhost:8080
```

**Multiple Sessions**:
```python
# Different ports for different sessions
session1 = PtySession(['bash'], enable_viz=True, viz_port=8080)
session2 = PtySession(['bash'], enable_viz=True, viz_port=8081)
# View both at http://localhost:8080 and http://localhost:8081
```

### Troubleshooting

**Port already in use**:
```python
# Use a different port
with PtySession(['bash'], enable_viz=True, viz_port=9090) as session:
    pass
```

**Missing dependencies**:
```bash
# Error: Visualization dependencies not installed
# Solution: Install viz extras
uv pip install ptytest[viz]
```

**Browser not connecting**:
- Check firewall settings
- Verify server is running: `http://localhost:PORT/health`
- Check server startup message in console

## Troubleshooting

### Tests fail with "tmux: command not found"

Install tmux:
```bash
brew install tmux  # macOS
sudo apt install tmux  # Ubuntu/Debian
```

### Tests hang or timeout

- Check for orphaned sessions: `tmux ls`
- Kill old test sessions: `tmux kill-session -t ptytest-*`
- Increase timeout in pytest.ini or per-test

### Shell not initializing properly

Increase the shell ready timeout:
```python
session = TmuxSession(timeout=10)
```

Or add explicit waits:
```python
import time
time.sleep(1.0)  # Wait for shell initialization
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
