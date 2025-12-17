"""Pytest configuration for ptytest tests."""

# Import fixtures from the package
# They're auto-registered via the pytest11 entry point,
# but we import here for IDE support
from ptytest.pytest_plugin import (
    tmux_session,
    tmux_session_minimal,
    tmux_session_factory,
)
