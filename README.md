# Agentic Scientific Research Assistant

An evidence-grounded research workflow built while studying AI-agent engineering. The project begins with a framework-free tool-calling loop, then progresses to live literature retrieval, typed evidence extraction, MCP tools, evaluation, and a LangGraph workflow.

## Day 1 capability

The current implementation contains a bounded, inspectable agent loop. A language model can request the read-only `search_papers` tool. The application validates tool arguments, executes the local mock search, sends the observation back to the model, and ends only when the model provides an answer or the configured step limit is reached.

The bundled paper catalog is intentionally mocked for the first lesson. It will be replaced with provider-neutral adapters for real sources in the next stage.

## Run on Windows with WSL

Use a WSL 2 Linux distribution and keep the repository in its Linux filesystem (for example, `~/projects/ai_agent_demo`) instead of under `/mnt/c`. This generally gives development tools and Git better file-system performance.

Install Python 3.11 or later and [uv](https://docs.astral.sh/uv/) inside WSL. Then, from the repository root, synchronize the dependencies and run the deterministic demonstration:

```bash
uv sync --all-groups
uv run python experiments/manual_agent/main.py --offline \
  "What methods are being used to accelerate vision transformers on edge GPUs?"
```

To run against an OpenAI-compatible API, copy the example environment file, add your credentials, load it into the current shell, and omit `--offline`:

```bash
cp .env.example .env
# Edit .env and replace the placeholder values.
set -a
source .env
set +a

uv run research-agent \
  "What methods are being used to accelerate vision transformers on edge GPUs?"
```

The application reads configuration from environment variables; it does not load `.env` automatically. The `.env` file is ignored by Git and should never contain credentials you intend to commit.

## Validate

```bash
uv run pytest
```

## Important reading

The durable study reference for the project is [LLM Agent Engineering Foundations](docs/llm-agent-engineering-foundations.md). It explains the framework-independent concepts that underpin the implementation: messages, system instructions, tool calling, schemas, observations, loops, termination, structured outputs, context, and state.
