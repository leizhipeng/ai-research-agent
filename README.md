# Evidence-grounded AI research agent

A personal research demo and Python learning project. One **LangGraph** workflow
plans a question, searches **arXiv and OpenAlex**, ranks/deduplicates sources,
extracts and checks evidence, reviews coverage, and saves a Markdown report.
**Pydantic** defines contracts; **SQLite** retains artifacts, events, cache,
and restart checkpoints. The same functions are exposed through a CLI and MCP.

The model proposes plans, analyses, support decisions, and follow-up searches.
Python executes retrieval, enforces limits, validates exact evidence spans, and
renders reports from accepted records. Incomplete outcomes remain inspectable.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). From this directory:

```bash
uv python install
uv sync --locked
cp .env.example .env  # only if .env does not already exist
uv run research-agent --help
```

On macOS, `./scripts/setup-macos.sh` installs and checks imports, preserving an
existing `.env`. The commands above also apply to Ubuntu/WSL. There is no mandatory
test execution. Existing test files are historical; no new tests or automated
evaluation suite were added.

## Run without credentials

```bash
uv run research-agent run --offline \
  "How do quantization and pruning affect vision transformer inference on edge GPUs?"
uv run research-agent inspect
```

Copy the printed run ID into subsequent commands:

```bash
uv run research-agent inspect RUN_ID
uv run research-agent export RUN_ID --output data/my-report
```

Offline mode uses three **synthetic classroom abstracts** and deterministic
model substitutes. It exercises two search rounds, evidence checking, a
different-setup comparison, persistence, and report generation. It deliberately
returns `partial`: the synthetic corpus cannot answer a real research question.
Its fixed corpus remains the same for any question. Read the saved
[offline report](examples/offline/report.md) and [evidence trail](examples/offline/artifacts.json).

## Live research

Set `OPENAI_API_KEY` and a model available to your account in `.env`. The default
template uses `gpt-5-mini`; the verification record identifies the model actually
used. An optional `OPENALEX_API_KEY` increases OpenAlex's allowance. Current
OpenAlex guidance permits small keyless requests; access/quotas can change.
See [provider verification and official references](docs/verification.md).

The application does **not** automatically load `.env`. In a POSIX shell:

```bash
set -a
source .env
set +a

uv run research-agent run \
  "What methods are described for post-training quantization of vision transformers?" \
  --scope "Describe author-reported methods and limitations from abstracts only." \
  --max-papers 3 --max-queries 1 --results-per-query 2 \
  --max-model-calls 20 --max-tokens 180000 --max-seconds 150
```

`OPENAI_BASE_URL` (or `OPENAI_API_BASE`) selects an explicitly configured compatible
endpoint. Native JSON Schema output is the default. For an endpoint with JSON mode
but no native schema support, explicitly set `RESEARCH_AGENT_JSON_MODE=true`;
Pydantic and semantic validation still apply. `RESEARCH_AGENT_TIMEOUT_SECONDS`
bounds requests; `RESEARCH_AGENT_MAX_OUTPUT_TOKENS` bounds each model response.

Direct discovery needs no model credentials:

```bash
uv run research-agent search "vision transformer quantization" --provider arxiv --max-results 2
uv run research-agent search "vision transformer quantization" --provider openalex --max-results 2
```

For a known paper, steer initial discovery with `--query`; repeat it for several
queries. For example, `run "What is the PTF component proposed by FQ-ViT?"
--query FQ-ViT --max-papers 1 --max-rounds 1 --max-tokens 90000`. The planner still
creates the objective/subquestions, and the saved plan records the supplied query.
See the [focused live report](examples/live-fq-vit/report.md) and
[its evidence trail](examples/live-fq-vit/artifacts.json).

Use `--full-text` to attempt freely accessible arXiv HTML. Reading falls back to
the abstract when HTML is unavailable; it does not bypass paywalls or parse PDFs.
The [saved live report](examples/live-quantization/report.md) and
[structured export](examples/live-quantization/artifacts.json) retain actual retrieval and model output.

## Control and resume

```bash
uv run research-agent run --offline --pause-after-plan \
  "How do quantization and pruning affect vision transformer inference on edge GPUs?"
uv run research-agent inspect RUN_ID
uv run research-agent resume RUN_ID --approve
```

`resume` without approval leaves a plan approval gate paused. For an active run,
use `pause RUN_ID` or `cancel RUN_ID` from another terminal with the same database.
Control takes effect at workflow/request/reading boundaries. Ctrl-C also saves a
paused outcome. Paused or failed runs can resume; completed, partial, and halted
runs are immutable outcomes. Cancelled/budget-halted work needs a fresh run.
Saved successful stages, calls, and searches are reused during recovery.

`--db PATH` selects a database; default `data/research.sqlite`, overrideable via
`RESEARCH_AGENT_DB`. `run --help` lists all bounds: rounds, papers, queries,
results, model calls, reserved tokens, active seconds, HTTP calls, downloaded
bytes, and concurrency. Token reservations use conservative byte-based capacity
accounting; measured provider tokens are separate. An in-flight read can exceed
byte/deadline boundaries by a bounded block/socket operation.
See [recovery and resource details](docs/architecture.md).

## MCP and manual loop

```bash
uv run python experiments/mcp_client/main.py --db data/mcp-demo.sqlite
uv run python -m research_agent.mcp_server --db data/research.sqlite
uv run python experiments/manual_agent/main.py --offline \
  "What methods accelerate vision transformers on edge GPUs?"
```

The client launches a stdio server, discovers eight tools and the research input
schema, invokes the offline workflow, and inspects evidence. The second command
is the server entry point for another MCP host. The small manual example teaches
tool requests/observations using a mock catalog; it is separate from the main
workflow. [The walkthrough](docs/architecture.md) explains host/client/server
responsibilities and the deliberately pinned MCP v1 SDK.

## Reading order and limitations

1. [Learning roadmap](docs/Study%20Plan.md): a short exploration sequence.
2. [Agent engineering foundations](docs/llm-agent-engineering-foundations.md): concepts, research reasoning, and framework tradeoffs.
3. [Implementation walkthrough](docs/architecture.md): actual functions, graph, artifacts, evidence, recovery, and MCP.
4. [Requirements and statuses](docs/research-assistant-requirements.md) and [manual verification](docs/verification.md): what was observed and what remains limited.

Scope is free text for planning and support review, rather than a hard date/hardware
filter. Keyword retrieval/ranking can miss relevant work or select a poor match.
Abstracts cannot establish unreported experiments. HTML extraction loses layout,
and analysis reads at most 16,000 retained characters per source. Model support
checks are fallible judgments; inspect quotations before relying on a claim.
A partial or halted report does not establish research completeness. This project
has no vector database, broad frontend, multiple full agent implementations, or
automatic publication.

Validation commands:

```bash
uv run ruff check src experiments
uv run python -m compileall -q src experiments
git diff --check
```

[Execution progress](docs/execution-plan.md) records decisions and completion evidence.
