# ptytest Examples

This directory contains runnable examples demonstrating all ptytest features.

## Running Examples

All examples can be run with pytest:

```bash
# Run all examples
uv run pytest examples/ -v

# Run a specific example file
uv run pytest examples/01_pty_session_basics.py -v

# Run examples with output visible
uv run pytest examples/ -v -s
```

## Example Files

### Core Session Types

| File | Description |
|------|-------------|
| `01_pty_session_basics.py` | PtySession fundamentals - spawning processes, sending keys, reading output |
| `02_tmux_session_basics.py` | TmuxSession for tmux-specific testing - panes, splits, prefix keys |
| `03_neovim_session.py` | NeovimSession for testing Neovim plugins |

### Keys and Input

| File | Description |
|------|-------------|
| `04_keys_and_escapes.py` | Using Keys class for control characters, arrows, function keys |
| `05_app_specific_keys.py` | Application-specific key bindings (fzf, vim, tmux, lazygit) |

### Testing Patterns

| File | Description |
|------|-------------|
| `06_pytest_fixtures.py` | Using ptytest's pytest fixtures and markers |
| `07_testing_patterns.py` | Common testing patterns and best practices |

### Interactive Applications

| File | Description |
|------|-------------|
| `test_fzf.py` | Testing fzf (fuzzy finder) |
| `test_ncdu.py` | Testing ncdu (disk usage analyzer) |
| `test_lazygit.py` | Testing lazygit |

### Visualization

| File | Description |
|------|-------------|
| `08_visualization.py` | Using the Textual-based terminal visualization |

## Quick Start Examples

### PtySession - Test any CLI

```python
from ptytest import PtySession

def test_echo():
    with PtySession(["bash", "--norc"]) as session:
        session.send_keys("echo 'Hello, World!'")
        assert session.verify_text_appears("Hello, World!")
```

### TmuxSession - Test tmux bindings

```python
from ptytest import TmuxSession

def test_pane_split():
    with TmuxSession() as session:
        assert session.get_pane_count() == 1
        session.send_prefix_key('"')  # Split horizontal
        assert session.get_pane_count() == 2
```

### Keys - Send special keys

```python
from ptytest import PtySession, Keys

def test_ctrl_c():
    with PtySession(["python3", "-c", "import time; time.sleep(100)"]) as session:
        session.send_raw(Keys.CTRL_C)
        assert session.verify_text_appears("KeyboardInterrupt")
```

### NeovimSession - Test Neovim plugins

```python
from ptytest import NeovimSession

def test_neovim():
    with NeovimSession() as nvim:
        nvim.type_text("Hello Neovim!")
        nvim.assert_buffer_contains("Hello Neovim!")
```

## Requirements

- Python 3.8+
- For TmuxSession: tmux installed
- For NeovimSession: neovim installed
- For visualization: `uv pip install ptytest[viz]`
