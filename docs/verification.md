# Manual verification record

Observed on **2026-10-03**, macOS, Python 3.13, using the repository's uv lockfile.
These are ordinary application invocations and artifact inspections, not a test
suite or a research-quality benchmark. No tests were added or executed; existing
`tests/` files were left untouched. No publishing, deployment, or push occurred.

## Installation and static checks

- `uv sync --locked` and `./scripts/setup-macos.sh`: succeeded. Setup preserved
  the existing `.env`, checked workflow/MCP imports, and did not execute tests.
- `uv run ruff check src experiments`: passed.
- `uv run python -m compileall -q src experiments`: passed.
- `git diff --check`: passed after documentation whitespace cleanup.
- The original manual example still completed offline: two model turns, one
  mock search; its output explicitly says the papers are mocked.

## Saved offline workflow

Command:

```bash
uv run research-agent run --offline \
  "How do quantization and pruning affect vision transformer inference on edge GPUs?"
uv run research-agent export RUN_ID --output examples/offline
```

The saved [report](../examples/offline/report.md) and
[artifact export](../examples/offline/artifacts.json) contain three **synthetic**
abstracts, three exact paragraph quotations, two reviews/search rounds, ten
substitute calls, no HTTP/model-token usage, and one checked `different_setup`
comparison. Outcome `partial` is intentional: fictional classroom material is
not a completed real literature review. Evidence spans were located in retained
`Source.content`, and support/check records were inspected.

## Live providers, content, and cache

These commands succeeded without model credentials or an OpenAlex API key:

```bash
uv run research-agent search "vision transformer quantization" --provider arxiv --max-results 2
uv run research-agent search "vision transformer quantization" --provider openalex --max-results 2
```

Observed arXiv records included `2609.01743` (SCULPT) and `2307.00331`, both with
abstracts. OpenAlex returned FQ-ViT (`W4285601701`, abstract available) and PTQ4ViT
(`W4313069943`, metadata only). Records retained query, retrieval timestamp,
provider URL, durable IDs, authors, and available publication metadata.

Ordinary calls to `read_source(first_arxiv)` and the MCP `read_source` tool read
24,221 characters of freely accessible arXiv HTML for SCULPT. The record marked
`full_text`, retained the HTML URL and second retrieval context, and disclosed
loss of figure/math structure. This verified retrieval; it was not a full-paper
model analysis. The application separately limits an analysis window to 16,000
characters.

Searching FQ-ViT through both adapters then calling `deduplicate_sources()` reduced
two records to one: arXiv `2111.13824v4`, OpenAlex `W4285601701`, and DOI
`10.24963/ijcai.2022/164` all survived, with both retrieval contexts. Repeating
both provider calls through `Store.cache_get/cache_set` marked cache hits and
left the request counter at two. A 32-byte response allowance produced an explicit
`DiscoveryError` rather than a successful empty result.

## Live model-backed research

The existing local `.env` supplied a configured OpenAI key and model
`gpt-5.6-luna`, using the normal OpenAI endpoint. The key was never printed,
copied into examples, or committed. Runs below used native schema parsing.

The [focused report](../examples/live-fq-vit/report.md) and
[evidence trail](../examples/live-fq-vit/artifacts.json) investigate:

```bash
uv run research-agent run "What is the PTF component proposed by FQ-ViT?" \
  --query FQ-ViT \
  --scope "Explain PTF from the author-reported abstract only. Do not assess experiments, alternatives, or LIS." \
  --max-rounds 1 --max-papers 1 --max-queries 1 --results-per-query 1 \
  --max-model-calls 8 --max-tokens 90000 --max-seconds 90 --max-http-requests 4
```

Observed outcome: `completed` for its narrow abstract-level question. Both
providers' cached records merged into one source, two exact supporting passages
survived identity/linkage/semantic checks, and the review marked its one
subquestion covered. Five model calls reported 4,277 tokens; conservative
reservations totalled 32,987. The run reused two cache entries, so it performed
zero new HTTP requests; those responses had been obtained live in the preceding
FQ-ViT run. Completion does not mean experiments or full text were verified.

A [broader saved run](../examples/live-quantization/report.md), with its
[artifact trail](../examples/live-quantization/artifacts.json), used the README's
post-training-quantization question: two rounds, three analyzed abstracts,
15 model calls, 14,141 observed tokens, 103,622 reserved tokens, four HTTP
requests. It remained `partial` and reported missing evidence for specific
quantization methods. Early query wording included `abstract`, unnecessarily
narrowing arXiv's AND search and yielding poor matches; the planner instruction
now asks for short topic keywords, and `--query` provides explicit steering.
The preserved partial report is evidence of an actual limitation, not a claimed
retrieval-quality success.

A deliberately smaller 28,000 reservation budget halted an earlier live run at
analysis. Its measured tokens were much lower than reserved capacity. This
verified that budget enforcement uses reservations rather than model optimism.

## Controls, restart, export, and failure paths

Separate CLI processes exercised:

```bash
uv run research-agent run --offline --pause-after-plan --db /tmp/research-controls.sqlite \
  "How do quantization and pruning affect vision transformer inference?"
uv run research-agent --db /tmp/research-controls.sqlite inspect RUN_ID
uv run research-agent --db /tmp/research-controls.sqlite resume RUN_ID
uv run research-agent --db /tmp/research-controls.sqlite resume RUN_ID --approve
uv run research-agent --db /tmp/research-controls.sqlite resume RUN_ID
uv run research-agent --db /tmp/research-controls.sqlite export RUN_ID --output /tmp/research-export
```

The first resume stayed paused with one completed planner call. Approval finished
with ten substitute calls and a report. Repeated resume retained the same run ID,
source/evidence records, and call count. Markdown/JSON export succeeded. `pause`
and `cancel` on a separate approval-paused run preserved its plan; cancellation
produced terminal `halted`. Cancelling an already finished run was rejected.

A too-short question, concurrency zero, and unknown run ID were rejected with
nonzero CLI exits. Live mode without an environment-loaded key produced a saved
`failed` outcome and exit 1. Offline `--max-model-calls 1` halted at analysis with
its plan retained and a report explaining the bound.

Crash-safe artifact replay, stale-owner reclaim, and conservative crash-time
charging were reviewed in code. A forced process kill during a paid request was
not exercised. No exactly-once remote-call guarantee is claimed. Synthetic
runtime substitutions are not invalid-output fixtures or an evaluation harness.

## MCP discovery and invocation

```bash
uv run python experiments/mcp_client/main.py --db /tmp/research-mcp.sqlite
```

The real stdio client initialized a session, listed all eight tools, printed the
research input schema, invoked offline `run_research`, and invoked
`inspect_research`. Structured results included three exact synthetic evidence
items and the checked setup comparison. Separate real client calls also invoked
`search_literature` for arXiv and `read_source`, receiving the 24,221-character
HTML record. Server startup alone was not counted as verification.

## Current limits and external blockers

No external blocker remains for the verified paths: configured live model calls
and both discovery providers worked. Keyless OpenAlex availability/quotas and
model availability remain account/provider conditions. The default `.env.example`
model and custom proxy JSON compatibility mode were not separately live-verified.
Ubuntu/WSL portability follows ordinary Python/uv APIs but was not executed on
another host. No exhaustive retrieval-quality, adversarial-injection, or general
semantic-accuracy claim follows from these runs.

Current official references consulted for the implementation:

- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html) and [API terms](https://info.arxiv.org/help/api/tou.html).
- [OpenAlex authentication](https://help.openalex.org/api/authentication/) and [work search](https://docs.openalex.org/api-entities/works/search-works).
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) and [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
- [MCP Python SDK v1](https://py.sdk.modelcontextprotocol.io/v1/) and [stdio client example](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/examples/snippets/clients/stdio_client.py).
