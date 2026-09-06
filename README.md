# Agentic Scientific Research Assistant

An evidence-grounded research workflow built while studying AI-agent engineering. The project begins with a framework-free tool-calling loop, then progresses to live literature retrieval, typed evidence extraction, MCP tools, evaluation, and a LangGraph workflow.

## Day 1 capability

The current implementation contains a bounded, inspectable agent loop. A language model can request the read-only `search_papers` tool. The application validates tool arguments, executes the local mock search, sends the observation back to the model, and ends only when the model provides an answer or the configured step limit is reached.

The bundled paper catalog is intentionally mocked for the first lesson. It will be replaced with provider-neutral adapters for real sources in the next stage.

## Run on Windows with uv

Install [uv](https://docs.astral.sh/uv/) and Python 3.11 or later. In PowerShell, synchronize dependencies and run the deterministic demonstration:

```powershell
uv sync --all-groups
uv run python experiments/manual_agent/main.py --offline "What methods are being used to accelerate vision transformers on edge GPUs?"
```

To run against an OpenAI-compatible API, set the environment variables shown in `.env.example`, then omit `--offline`:

```powershell
$env:OPENAI_API_KEY = "..."
$env:OPENAI_API_BASE = "https://your-api-base/v1"
uv run research-agent "What methods are being used to accelerate vision transformers on edge GPUs?"
```

## Validate

```powershell
uv run pytest
```

## Important reading

The durable study reference for the project is [LLM Agent Engineering Foundations](docs/llm-agent-engineering-foundations.md). It explains the framework-independent concepts that underpin the implementation: messages, system instructions, tool calling, schemas, observations, loops, termination, structured outputs, context, and state.
