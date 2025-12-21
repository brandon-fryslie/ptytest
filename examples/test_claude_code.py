"""
Examples of testing Claude Code CLI with ptytest.

This demonstrates using ptytest to test Claude Code, an AI-powered coding assistant.
Shows both direct mode (faster) and Docker mode (isolated).

Run with: pytest examples/test_claude_code.py -v -m claude_code

Prerequisites:
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)
- Authentication: ANTHROPIC_API_KEY env var OR `claude auth login` completed
- Docker (for Docker mode tests)

Authentication methods:
1. API key: export ANTHROPIC_API_KEY=sk-ant-...
2. OAuth: run `claude auth login` (credentials stored in ~/.claude)

Custom API endpoint (for testing other models):
    export ANTHROPIC_BASE_URL=http://localhost:8080

Cost warning: These tests invoke the Claude API and incur costs (~$0.001-0.01 per test).

Run direct mode only:
    pytest examples/test_claude_code.py -v -m "claude_code and not docker"

Run Docker mode only:
    pytest examples/test_claude_code.py -v -m docker
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import pytest

from ptytest import Keys, PtySession

pytestmark = [pytest.mark.claude_code, pytest.mark.slow]


def get_api_key() -> Optional[str]:
    """Get API key from environment if set."""
    return os.environ.get("ANTHROPIC_API_KEY")


def get_base_url() -> Optional[str]:
    """Get custom base URL from environment if set."""
    return os.environ.get("ANTHROPIC_BASE_URL")


def get_claude_config_dir() -> Path:
    """Get the Claude Code config directory (~/.claude)."""
    return Path.home() / ".claude"


def has_api_key() -> bool:
    """Check if ANTHROPIC_API_KEY is set."""
    return bool(get_api_key())


def has_oauth_auth() -> bool:
    """Check if OAuth authentication is configured (via claude auth login)."""
    config_dir = get_claude_config_dir()
    # Claude stores auth in ~/.claude/credentials.json or similar
    if not config_dir.exists():
        return False
    # Check for any auth-related files
    auth_files = ["credentials.json", "auth.json", "config.json"]
    return any((config_dir / f).exists() for f in auth_files)


def has_any_auth() -> bool:
    """Check if any authentication method is available."""
    return has_api_key() or has_oauth_auth()


def has_claude_cli() -> bool:
    """Check if Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def has_docker() -> bool:
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def build_claude_env() -> dict:
    """Build environment variables for Claude Code."""
    env = os.environ.copy()

    # API key takes precedence if set
    api_key = get_api_key()
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key

    # Custom base URL for testing other models
    base_url = get_base_url()
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    return env


def build_docker_cmd(
    image: str,
    workspace: Optional[Path] = None,
    mount_auth: bool = True
) -> list:
    """
    Build docker run command with proper volume mounts.

    Args:
        image: Docker image name
        workspace: Optional workspace directory to mount
        mount_auth: Whether to mount ~/.claude for OAuth auth persistence
    """
    cmd = ["docker", "run", "--rm", "-i"]

    # Pass API key if set
    api_key = get_api_key()
    if api_key:
        cmd.extend(["-e", f"ANTHROPIC_API_KEY={api_key}"])

    # Pass custom base URL if set
    base_url = get_base_url()
    if base_url:
        cmd.extend(["-e", f"ANTHROPIC_BASE_URL={base_url}"])

    # Mount auth credentials for OAuth persistence
    if mount_auth:
        config_dir = get_claude_config_dir()
        if config_dir.exists():
            cmd.extend(["-v", f"{config_dir}:/home/claude/.claude"])

    # Mount workspace directory
    if workspace:
        cmd.extend(["-v", f"{workspace}:/workspace", "-w", "/workspace"])

    cmd.append(image)
    cmd.append("claude")

    return cmd


# Skip all tests if no authentication is available
pytestmark.append(
    pytest.mark.skipif(
        not has_any_auth(),
        reason="No authentication available (need ANTHROPIC_API_KEY or 'claude auth login')"
    )
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def claude_env():
    """Environment variables for Claude Code."""
    return build_claude_env()


class TestClaudeCodeDirect:
    """
    Direct mode tests - launch Claude Code directly via PtySession.

    These tests are:
    - Faster (no Docker overhead)
    - Simpler to debug
    - Good for basic interaction tests

    BUT they affect your real filesystem, so avoid tool use tests here.

    Authentication: Uses ANTHROPIC_API_KEY or OAuth from ~/.claude
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_claude(self):
        """Skip these tests if Claude Code CLI is not installed."""
        if not has_claude_cli():
            pytest.skip("Claude Code CLI not installed")

    def test_launch_and_verify_ready(self, claude_env):
        """Test that Claude Code launches and shows ready prompt."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            # Wait for the ready prompt (Claude shows '>' when ready)
            assert session.verify_text_appears(">", timeout=30), \
                "Claude Code did not show ready prompt"
            assert session.process.isalive()

    def test_simple_prompt_and_response(self, claude_env):
        """Test sending a simple prompt and verifying response streams."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            # Send a simple, cheap prompt
            session.send_keys("What is 2+2? Answer with just the number.", literal=False)

            time.sleep(5)
            content = session.get_content()

            # Check that we got SOME response
            assert len(content) > 100, "No response received from Claude"
            assert "error" not in content.lower() or "4" in content
            assert session.process.isalive()

    def test_exit_cleanly(self, claude_env):
        """Test that /exit command exits Claude Code cleanly."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys("/exit", literal=False)
            time.sleep(1)

            for _ in range(10):
                if not session.process.isalive():
                    break
                time.sleep(0.5)

            assert not session.process.isalive(), "Claude Code did not exit after /exit"

    def test_help_command(self, claude_env):
        """Test that /help command works."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys("/help", literal=False)
            time.sleep(2)

            content = session.get_content()
            help_indicators = ["/exit", "command", "help"]
            assert any(indicator in content.lower() for indicator in help_indicators), \
                f"Help text not found in: {content}"

    def test_interrupt_response(self, claude_env):
        """Test interrupting a streaming response with Ctrl+C."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys(
                "Write a long story about a robot. Make it at least 500 words.",
                literal=False
            )

            time.sleep(2)
            session.send_raw(Keys.CTRL_C)
            time.sleep(1)

            assert session.process.isalive(), "Claude Code crashed after Ctrl+C"

            session.send_keys("/help", literal=False)
            time.sleep(1)
            content = session.get_content()
            assert "help" in content.lower() or "/exit" in content.lower()

    def test_multi_turn_conversation(self, claude_env):
        """Test that Claude maintains context across multiple turns."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys("My favorite color is blue. Just acknowledge this.", literal=False)
            time.sleep(5)

            session.send_keys("What is my favorite color?", literal=False)
            time.sleep(5)

            content = session.get_content()
            assert "blue" in content.lower(), \
                "Claude did not maintain conversation context"


class TestClaudeCodeWithBaseURL:
    """
    Tests for custom API endpoint (ANTHROPIC_BASE_URL).

    Use this for testing with:
    - Local LLM servers (Ollama, vLLM, etc.)
    - Alternative API providers
    - Mock servers for testing
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_base_url(self):
        """Skip these tests if no custom base URL is set."""
        if not get_base_url():
            pytest.skip("ANTHROPIC_BASE_URL not set")
        if not has_claude_cli():
            pytest.skip("Claude Code CLI not installed")

    def test_custom_endpoint_connection(self, claude_env):
        """Test connecting to a custom API endpoint."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            # Just verify we can launch - actual behavior depends on the endpoint
            time.sleep(5)
            assert session.process.isalive(), "Claude Code failed to start with custom endpoint"

            content = session.get_content()
            # Check for common error patterns
            assert "connection refused" not in content.lower(), \
                f"Failed to connect to custom endpoint: {content}"


@pytest.mark.docker
class TestClaudeCodeDocker:
    """
    Docker mode tests - launch Claude Code in a container.

    These tests are:
    - Isolated (safe for tool use)
    - Reproducible (clean environment)
    - Slower (Docker overhead)

    Use this mode for testing tool use (file operations, commands).

    Authentication options:
    - API key: passed via ANTHROPIC_API_KEY env var
    - OAuth: mount ~/.claude volume with existing auth credentials
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_docker(self):
        """Skip these tests if Docker is not available."""
        if not has_docker():
            pytest.skip("Docker not available")

    @pytest.fixture
    def docker_image(self):
        """Build the Claude Code Docker image."""
        dockerfile_dir = Path(__file__).parent / "claude-code"
        dockerfile_path = dockerfile_dir / "Dockerfile"

        if not dockerfile_path.exists():
            pytest.skip(f"Dockerfile not found at {dockerfile_path}")

        image_name = "ptytest-claude-code:latest"
        result = subprocess.run(
            ["docker", "build", "-t", image_name, str(dockerfile_dir)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Failed to build Docker image: {result.stderr}")

        yield image_name

    def test_launch_in_docker(self, docker_image):
        """Test launching Claude Code in Docker container."""
        cmd = build_docker_cmd(docker_image, mount_auth=True)

        with PtySession(cmd, width=120, height=40, timeout=30) as session:
            assert session.verify_text_appears(">", timeout=30), \
                "Claude Code in Docker did not show ready prompt"
            assert session.process.isalive()

    def test_read_file_in_docker(self, docker_image, temp_workspace):
        """Test asking Claude to read a file in Docker (isolated)."""
        test_file = temp_workspace / "test.txt"
        test_content = "This is a test file for Claude Code testing."
        test_file.write_text(test_content)

        cmd = build_docker_cmd(docker_image, workspace=temp_workspace, mount_auth=True)

        with PtySession(cmd, width=120, height=40, timeout=30) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys(
                "Please read the file test.txt and tell me what it says. Use the Read tool.",
                literal=False
            )

            time.sleep(5)
            content = session.get_content()

            # Handle tool approval if needed
            if "approve" in content.lower() or "allow" in content.lower():
                session.send_keys("y", literal=False)
                time.sleep(5)
                content = session.get_content()

            assert "test file" in content.lower() or "testing" in content.lower(), \
                f"Claude did not read the file correctly: {content}"

    def test_run_command_in_docker(self, docker_image):
        """Test asking Claude to run a shell command in Docker (isolated)."""
        cmd = build_docker_cmd(docker_image, mount_auth=True)

        with PtySession(cmd, width=120, height=40, timeout=30) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys(
                "Run the command 'echo Hello from Docker' using the Bash tool.",
                literal=False
            )

            time.sleep(5)
            content = session.get_content()

            if "approve" in content.lower() or "allow" in content.lower():
                session.send_keys("y", literal=False)
                time.sleep(5)
                content = session.get_content()

            assert "hello" in content.lower() and "docker" in content.lower(), \
                f"Command output not found: {content}"

    def test_create_file_in_docker(self, docker_image, temp_workspace):
        """Test asking Claude to create a file in Docker (isolated)."""
        cmd = build_docker_cmd(docker_image, workspace=temp_workspace, mount_auth=True)

        with PtySession(cmd, width=120, height=40, timeout=30) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys(
                "Create a file named 'output.txt' with the content 'Created by Claude' "
                "using the Write tool.",
                literal=False
            )

            time.sleep(5)
            content = session.get_content()

            if "approve" in content.lower() or "allow" in content.lower():
                session.send_keys("y", literal=False)
                time.sleep(5)

            time.sleep(2)

            output_file = temp_workspace / "output.txt"
            assert output_file.exists(), "Claude did not create the file"

            file_content = output_file.read_text()
            assert "created by claude" in file_content.lower(), \
                f"File content incorrect: {file_content}"


class TestClaudeCodeEdgeCases:
    """Edge case and stress tests for Claude Code."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_claude(self):
        """Skip these tests if Claude Code CLI is not installed."""
        if not has_claude_cli():
            pytest.skip("Claude Code CLI not installed")

    def test_handles_empty_input(self, claude_env):
        """Test that Claude handles empty input gracefully."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            session.send_keys("", literal=False)
            time.sleep(1)

            assert session.process.isalive()

            session.send_keys("/help", literal=False)
            time.sleep(1)
            content = session.get_content()
            assert "help" in content.lower() or "/exit" in content.lower()

    def test_rapid_interrupts(self, claude_env):
        """Test rapid Ctrl+C interrupts."""
        with PtySession(["claude"], width=120, height=40, timeout=30, env=claude_env) as session:
            assert session.verify_text_appears(">", timeout=30)

            for _ in range(3):
                session.send_raw(Keys.CTRL_C)
                time.sleep(0.2)

            assert session.process.isalive()

            session.send_keys("/help", literal=False)
            time.sleep(1)
            assert session.process.isalive()
