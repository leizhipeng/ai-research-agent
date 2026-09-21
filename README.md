# Agentic Scientific Research Assistant

An evidence-grounded research workflow built while studying AI-agent engineering. The project begins with a framework-free tool-calling loop, then progresses to live literature retrieval, typed evidence extraction, MCP tools, evaluation, and a LangGraph workflow.

## Day 1 capability

The current implementation contains a bounded, inspectable agent loop. A language model can request the read-only `search_papers` tool. The application validates tool arguments, executes the local mock search, sends the observation back to the model, and ends only when the model provides an answer or the configured step limit is reached.

The bundled paper catalog is intentionally mocked for the first lesson. It will be replaced with provider-neutral adapters for real sources in the next stage.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) to install Python and manage dependencies.

From the repository root, run the bootstrap script. It installs Python 3.13, creates the local `.venv`, installs the locked development dependencies, creates `.env` if needed, and runs the tests:

```bash
./scripts/setup-macos.sh
```

### Run offline

Run the deterministic offline demonstration:

```bash
uv run python experiments/manual_agent/main.py --offline \
  "What methods are being used to accelerate vision transformers on edge GPUs?"
```

### Run with an API

Edit `.env` and replace the API-key placeholder. For the normal OpenAI API, leave `OPENAI_BASE_URL` commented out. Set it only when using a compatible proxy or another provider. Load the values into the current zsh session, then omit `--offline`:

```bash
set -a
source .env
set +a

uv run research-agent \
  "What methods are being used to accelerate vision transformers on edge GPUs?"
```

The application reads configuration from environment variables; it does not load `.env` automatically. When you open a new Terminal window, run the three environment-loading commands again before a live API run. Offline runs do not require `.env`.

## Manual setup and other POSIX systems

The project remains compatible with Ubuntu and WSL 2. Without the macOS bootstrap script, the equivalent setup is:

```bash
uv python install
uv sync --all-groups --locked
cp .env.example .env
uv run pytest
```

## Validate

```bash
uv run pytest
```

## Important reading

The durable study reference for the project is [LLM Agent Engineering Foundations](docs/llm-agent-engineering-foundations.md). It explains the framework-independent concepts that underpin the implementation: messages, system instructions, tool calling, schemas, observations, loops, termination, structured outputs, context, and state.
