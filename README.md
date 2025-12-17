# ptytest

**Real terminal testing framework** - Test interactive CLI applications with actual keystrokes.

ptytest lets you write automated tests for interactive terminal applications (like tmux keybindings, zsh ZLE widgets, or any interactive CLI) by sending real keystrokes and verifying actual terminal output. No mocks, no fakes - just real process control via PTY.

## Features

- **Real Keystrokes**: Send actual key sequences (Ctrl-b, Escape codes, etc.)
- **Real Output**: Verify actual terminal content, not mocked responses
- **tmux Integration**: Full control over tmux sessions, panes, and state
- **ZLE Support**: Test zsh line editor widgets with escape sequences
- **Pytest Plugin**: Auto-registered fixtures for easy test writing
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
- tmux (installed and in PATH)
- macOS or Linux

```bash
# Install tmux on macOS
brew install tmux

# Install tmux on Ubuntu/Debian
sudo apt install tmux
```

## Quick Start

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

### Basic Session Control

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

### Fixtures

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
pytest -m "not slow"    # Skip slow tests
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

## Why "Un-gameable" Tests?

Traditional unit tests can be "gamed" with mocks that don't reflect real behavior. ptytest tests are un-gameable because they:

1. **Spawn real processes** - Actual tmux/shell processes, not mocks
2. **Send real keystrokes** - Literal bytes sent to the PTY
3. **Verify real output** - Actual terminal content captured
4. **Test observable outcomes** - Pane counts, content, state changes

If a ptytest test passes, the functionality actually works. If it fails, something is genuinely broken.

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
