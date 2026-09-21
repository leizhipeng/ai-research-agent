#!/bin/sh

set -eu

if [ "$(uname -s)" != "Darwin" ]; then
    echo "This setup script is intended for macOS." >&2
    exit 1
fi

if ! command -v xcode-select >/dev/null 2>&1 || ! xcode-select -p >/dev/null 2>&1; then
    echo "Apple Command Line Tools are required. Run: xcode-select --install" >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Install it with one of:" >&2
    echo "  brew install uv" >&2
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

echo "Installing the Python version selected in .python-version..."
uv python install

echo "Creating/updating .venv and installing locked dependencies..."
uv sync --all-groups --locked

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example. Add OPENAI_API_KEY before live runs."
else
    echo "Kept the existing .env file unchanged."
fi

echo "Running tests..."
uv run pytest

echo "macOS setup complete. Try:"
echo "  uv run research-agent --offline \"What methods accelerate vision transformers?\""
