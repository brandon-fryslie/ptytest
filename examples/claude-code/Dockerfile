# Dockerfile for Claude Code CLI testing
# This creates an isolated environment for safely testing Claude Code tool use
#
# Supports two authentication methods:
# 1. API key: -e ANTHROPIC_API_KEY=sk-...
# 2. OAuth: mount ~/.claude volume with existing auth (-v ~/.claude:/home/claude/.claude)
#
# Custom API endpoint:
# -e ANTHROPIC_BASE_URL=http://localhost:8080

FROM node:20-slim

# Install basic utilities
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
# Note: This installs the latest version. Pin version for reproducibility in production.
RUN npm install -g @anthropic-ai/claude-code

# Set up a non-root user for safety
RUN useradd -m -s /bin/bash claude

# Create .claude directory for config/auth persistence
RUN mkdir -p /home/claude/.claude && chown -R claude:claude /home/claude/.claude

USER claude
WORKDIR /home/claude

# Environment variables (can be overridden at runtime):
# - ANTHROPIC_API_KEY: API key authentication
# - ANTHROPIC_BASE_URL: Custom API endpoint (for testing other models)
#
# Volume mounts:
# - /home/claude/.claude: Persist auth credentials from 'claude auth login'
# - /workspace: Working directory for file operations

# Default command (can be overridden)
CMD ["claude"]
