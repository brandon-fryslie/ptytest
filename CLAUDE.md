# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ptytest is a real terminal testing framework for testing interactive CLI applications with actual keystrokes. It spawns real processes via PTY (or tmux for multi-pane testing), sends actual key bytes, and verifies real terminal output - no mocks.

**Goal**: Comprehensive toolkit for testing interactive CLI applications.

## Build & Development Commands

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest -v

# Run single test
uv run pytest tests/test_session.py::TestTmuxSessionBasics::test_context_manager -v

# Run tests by marker
uv run pytest -m keybinding    # keybinding tests only
uv run pytest -m direct_pty    # PtySession tests only
uv run pytest -m "not slow"    # skip slow tests

# Run examples
uv run pytest examples/ -v

# Lint
uv run ruff check src/ tests/ examples/
uv run ruff format src/ tests/ examples/

# Type check
uv run mypy src/

# Environment check
uv run ptytest check
```

## Architecture

```
src/ptytest/
├── __init__.py      # Public API: BaseSession, TmuxSession, PtySession, Keys, FzfKeys, VimKeys
├── session.py       # BaseSession ABC + TmuxSession + PtySession implementations
├── keys.py          # Keys/MacKeys/FzfKeys/VimKeys - escape sequences and control characters
├── pytest_plugin.py # Auto-registered pytest fixtures and markers
└── cli.py           # CLI entrypoint (ptytest check/run/version)
```

### Core Components

**BaseSession** (`session.py`): Abstract base class defining the session interface.
- Abstract: `send_keys()`, `send_raw()`, `get_content()`, `cleanup()`
- Concrete: `verify_text_appears()`, `wait_for_text()`, context manager support

**PtySession** (`session.py`): Direct PTY-based testing for any CLI application.
- Spawns any command via pexpect with virtual terminal (pyte)
- No tmux required - test fzf, vim, ncdu, or any interactive CLI
- Uses background thread to keep virtual screen synchronized
- `get_content()` returns current screen state

**TmuxSession** (`session.py`): tmux-specific testing with multi-pane support.
- Creates detached tmux session, attaches via pexpect
- `send_prefix_key(key)` - Sends tmux prefix (Ctrl-b) + key
- `get_pane_count()`, `split_window()`, `get_pane_ids()` - tmux pane management

**Keys** (`keys.py`): Control characters, escape sequences, arrow keys, function keys.
- `Keys.meta(key)` - Alt combinations
- `Keys.ctrl(key)` - Ctrl combinations
- Shift/Ctrl/Alt arrow modifiers: `SHIFT_UP`, `CTRL_LEFT`, `ALT_DOWN`

**FzfKeys** (`keys.py`): fzf-specific bindings.
- `ACCEPT`, `TOGGLE`, `TOGGLE_ALL`, `CLEAR_QUERY`, etc.

**VimKeys** (`keys.py`): vim-specific bindings and helpers.
- `vim_command('wq')` - Send :wq + Enter
- `NORMAL_MODE`, `INSERT_MODE`, navigation keys

**Pytest Plugin** (`pytest_plugin.py`): Auto-registered via `pyproject.toml` entry point.
- `pty_session` - PtySession with bash shell
- `pty_session_factory` - Factory for custom PtySession instances
- `tmux_session` - Standard fixture with user's ~/.tmux.conf
- `tmux_session_minimal` - Clean tmux fixture (no config)
- `tmux_session_factory` - Factory for multiple tmux sessions

### Test Markers

Defined in `pyproject.toml`: `keybinding`, `zle`, `zaw`, `e2e`, `slow`, `interactive`, `direct_pty`

## Key Design Principle

Tests are **un-gameable** - they verify real behavior through actual process control:
1. **PtySession**: Spawns real process via pexpect, maintains virtual screen with pyte
2. **TmuxSession**: Spawns real tmux, attaches via pexpect for raw keystrokes
3. Cannot be faked with mocks - if tests pass, functionality works

## When to Use Which Session

| Session Type | Use Case | Requirements |
|--------------|----------|--------------|
| **PtySession** | Any interactive CLI (fzf, vim, ncdu, REPLs) | None (just pexpect + pyte) |
| **TmuxSession** | tmux keybindings, multi-pane workflows, ZLE widgets | tmux in PATH |

## Requirements

- Python 3.8+
- macOS or Linux
- tmux (only for TmuxSession; PtySession works without it)
