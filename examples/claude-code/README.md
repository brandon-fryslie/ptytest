# Claude Code Docker Environment

This directory contains Docker configuration for safely testing Claude Code with ptytest.

## Why Docker?

Running Claude Code in Docker provides:
- **Isolation**: File operations and commands don't affect your real filesystem
- **Safety**: Tool use is sandboxed
- **Reproducibility**: Clean environment for each test run
- **Auth persistence**: Mount ~/.claude to reuse OAuth credentials

## Authentication Methods

### 1. API Key (Environment Variable)

```bash
# Pass API key at runtime
docker run -e ANTHROPIC_API_KEY=sk-ant-... ptytest-claude-code
```

### 2. OAuth (Persistent Auth)

First, authenticate on your host machine:
```bash
claude auth login
```

Then mount your credentials into Docker:
```bash
docker run -v ~/.claude:/home/claude/.claude ptytest-claude-code
```

### Combined (Both Methods)

You can use both - API key takes precedence if set:
```bash
docker run \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v ~/.claude:/home/claude/.claude \
  ptytest-claude-code
```

## Custom API Endpoint

For testing with local LLM servers, alternative providers, or mock servers:

```bash
# Local Ollama, vLLM, etc.
docker run -e ANTHROPIC_BASE_URL=http://host.docker.internal:8080 ptytest-claude-code

# Note: Use host.docker.internal to reach host services from within Docker
```

## Building the Image

```bash
cd examples/claude-code
docker build -t ptytest-claude-code .
```

## Running Claude Code

### Basic (with API key)
```bash
docker run -it --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ptytest-claude-code
```

### With OAuth auth persistence
```bash
docker run -it --rm \
  -v ~/.claude:/home/claude/.claude \
  ptytest-claude-code
```

### With workspace directory (for tool use)
```bash
docker run -it --rm \
  -v ~/.claude:/home/claude/.claude \
  -v $(pwd):/workspace \
  -w /workspace \
  ptytest-claude-code
```

### With custom API endpoint
```bash
docker run -it --rm \
  -e ANTHROPIC_BASE_URL=http://host.docker.internal:8080 \
  -v ~/.claude:/home/claude/.claude \
  ptytest-claude-code
```

## Running Tests

```bash
# All Claude Code tests
pytest examples/test_claude_code.py -v -m claude_code

# Direct mode only (no Docker)
pytest examples/test_claude_code.py -v -m "claude_code and not docker"

# Docker mode only
pytest examples/test_claude_code.py -v -m docker

# With custom endpoint
ANTHROPIC_BASE_URL=http://localhost:8080 pytest examples/test_claude_code.py -v
```

## Files

- `Dockerfile` - Defines the Claude Code test environment
- `.dockerignore` - Files to exclude from Docker context
- `README.md` - This file

## Dockerfile Details

The Dockerfile:
- Uses Node.js 20 slim base image
- Installs Claude Code CLI globally via npm
- Creates a non-root user for security
- Sets up ~/.claude directory for auth persistence
- Supports API key, OAuth, and custom base URL

## Cost Considerations

- Each test invokes the Claude API
- Estimated cost: ~$0.001-0.01 per test
- Use `pytest -m "claude_code and not docker"` for faster, cheaper direct tests
- Docker mode is recommended only for tool use tests (file/command operations)

## Customization

To pin a specific Claude Code version, modify the Dockerfile:

```dockerfile
RUN npm install -g @anthropic-ai/claude-code@1.2.3
```

To add additional tools for testing:

```dockerfile
RUN apt-get update && apt-get install -y \
    your-tool-here \
    && rm -rf /var/lib/apt/lists/*
```
