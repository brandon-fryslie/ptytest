"""
ptytest CLI - Command-line interface for ptytest testing framework.
"""

import argparse
import shutil
import subprocess
import sys
from typing import Callable, Optional

from . import __version__


def check_environment() -> bool:
    """Check if the environment is properly configured for ptytest."""
    all_ok = True

    # Check tmux
    tmux_path = shutil.which("tmux")
    if tmux_path:
        try:
            result = subprocess.run(
                ["tmux", "-V"], capture_output=True, text=True, timeout=5
            )
            tmux_version = result.stdout.strip()
            print(f"✓ tmux found: {tmux_version} ({tmux_path})")
        except Exception as e:
            print(f"✗ tmux found but error getting version: {e}")
            all_ok = False
    else:
        print("✗ tmux not found in PATH")
        all_ok = False

    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python version: {py_version}")

    # Check pexpect
    try:
        import pexpect

        print(f"✓ pexpect installed: {pexpect.__version__}")
    except ImportError:
        print("✗ pexpect not installed")
        all_ok = False

    # Check pytest (optional)
    try:
        import pytest

        print(f"✓ pytest installed: {pytest.__version__}")
    except ImportError:
        print("○ pytest not installed (optional, needed for pytest plugin)")

    return all_ok


def cmd_check(args: argparse.Namespace) -> int:
    """Run environment check."""
    print("ptytest environment check\n")
    ok = check_environment()
    print()
    if ok:
        print("All checks passed! ptytest is ready to use.")
        return 0
    else:
        print("Some checks failed. Please install missing dependencies.")
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"ptytest {__version__}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run tests using pytest with ptytest plugin."""
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed. Install it with: pip install pytest")
        return 1

    pytest_args = args.pytest_args or []
    return pytest.main(pytest_args)  # type: ignore[no-any-return]


def main(argv: Optional[list] = None) -> int:
    """Main entry point for ptytest CLI."""
    parser = argparse.ArgumentParser(
        prog="ptytest",
        description="Real terminal testing framework - test interactive CLI apps with actual keystrokes",
    )
    parser.add_argument(
        "-V", "--version", action="store_true", help="Show version and exit"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check command
    check_parser = subparsers.add_parser(
        "check", help="Check environment for ptytest compatibility"
    )
    check_parser.set_defaults(func=cmd_check)

    # version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.set_defaults(func=cmd_version)

    # run command
    run_parser = subparsers.add_parser(
        "run", help="Run tests using pytest with ptytest plugin"
    )
    run_parser.add_argument(
        "pytest_args", nargs="*", help="Arguments to pass to pytest"
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)

    if args.version:
        return cmd_version(args)

    if args.command is None:
        parser.print_help()
        return 0

    # Type-safe way to call the function
    func: Callable[[argparse.Namespace], int] = args.func
    return func(args)


if __name__ == "__main__":
    sys.exit(main())
