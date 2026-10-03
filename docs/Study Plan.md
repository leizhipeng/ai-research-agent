# Research-agent learning roadmap

This project began as a daily study plan. The existing document used 14 days; the original plan may have used 20. That calendar is historical context. The project is organized around capabilities you can run and explain, without another daily schedule.

The central learning goal is to understand how a bounded application uses model judgment while retaining control of execution, source evidence, persistence, and stopping. You need Python knowledge; you do not need to learn several agent frameworks before exploring this repository.

## Read and explore in this order

1. **[README](../README.md): get one run working.** Install the locked environment, run the full offline demonstration, inspect the run, and export its report. Keep the synthetic-data label in mind: this establishes application behavior without proving research quality.
2. **[LLM Agent Engineering Foundations](llm-agent-engineering-foundations.md): learn the vocabulary.** Start with model calls, controlled workflows, messages, instructions, tools, structured output, context, and state. Run the small manual-loop example so you can recognize a tool request and its observation.
3. **[Foundations: research questions and evidence](llm-agent-engineering-foundations.md#research-questions-and-search-queries): understand the scientific contract.** Follow retrieval, ranking, deduplication, RAG, content levels, claim support, comparisons, and honest gaps. Open a saved evidence item and locate its quotation in retained content.
4. **[Implementation walkthrough](architecture.md): follow the actual program.** Trace one question through graph nodes, conditional routing, SQLite artifacts, checkpoints, review, and the report. Identify which operations need a model and which are ordinary Python functions. Follow the pause/resume and MCP client examples.
5. **[Requirements](research-assistant-requirements.md): judge the result against its contract.** Read implementation statuses and verification limits alongside the saved representative output. Distinguish implemented behavior, manually observed behavior, and external blockers.

The README owns installation and command instructions. Foundations owns conceptual definitions and framework comparisons. The walkthrough owns function-level behavior, recovery, and MCP integration. Requirements owns scope and acceptance statuses. Use those locations instead of maintaining parallel explanations in this roadmap.

## Capabilities to understand

| Capability | Concrete artifact or code to explore | Explain it in your own words |
|---|---|---|
| Validated intake and planning | `ResearchRequest`, `Limits`, `Plan`, saved planning artifact. | How do scope and resource limits become application data rather than only prose in a prompt? |
| Scholarly discovery | arXiv/OpenAlex adapters, source records, retrieval contexts, selection reasons. | Why are provider identifiers preserved when duplicates merge, and why is ranking separate from evidence support? |
| Reading and evidence | Content level, retained source text, exact evidence spans, support decisions. | What can an abstract establish, and what cannot be inferred from it? |
| Iterative review | Saved coverage/gaps, proposed queries, graph routing, stopping reason. | What can the reviewer propose, and what limits can the application enforce independently? |
| Durable execution | SQLite artifacts and LangGraph checkpoints for a stable run ID. | Which completed work can resume reuse, and where can an interrupted external request still repeat? |
| Human control | Plan approval and pause/cancel commands. | What changes at the next workflow boundary when a user asks to stop or continue? |
| Interoperability | MCP server and the ordinary client demonstration. | How do discovery and invocation differ from merely starting a server? |
| Honest reporting | Markdown report plus structured export. | How can a reader trace a finding back to a source, and where does the report disclose incomplete evidence? |

## A practical exploration path

First inspect the complete offline run. Follow one source ID through normalization, retained content, evidence, support, and the final reference. Then inspect the review that proposes additional retrieval. This shows the whole workflow before live credentials or provider latency complicate the picture.

Next pause a fresh run after planning. Inspect the plan, close the process, and resume with explicit approval. Compare the run ID and retained artifacts before and after. Experiment with a small round or paper limit on another fresh run and read the stopping reason; having a report file does not automatically mean the scope was answered.

After that, use the direct discovery command with each live provider. It does not require an LLM. Compare abstract availability and provider identifiers, and inspect a repeated retrieval's cache behavior. If a configured model is available, use the README's small live example and inspect its evidence quotations before accepting a finding.

Finally run the MCP client example and inspect the tool definitions and returned artifacts. The CLI and MCP tools should lead to the same underlying research functions. You now have enough context to explain why the main workflow uses LangGraph and why additional agent classes, a vector database, or a second full implementation would add little to this demo.

## Optional practice

The [foundations exercises](llm-agent-engineering-foundations.md#optional-hands-on-exercises) suggest short application runs and evidence audits. Record your observations in your own notes. No new unit, integration, end-to-end, regression, or evaluation suite is part of this project; older study-plan clauses requesting them are superseded. Existing test files are historical work and are not a setup prerequisite.

Use these questions to check your understanding:

- Why does a valid citation identifier fail to prove that a claim is supported?
- Why is a model's context different from the durable workflow state?
- Why can two different experimental results be non-comparable rather than contradictory?
- Why does a resumed interrupt re-enter a node, and how does artifact reuse avoid duplicate completed work?
- What prevents reviewer-directed searches from continuing forever?
- What remains uncertain when only an abstract is available?

An explanation grounded in one saved run is more useful than memorizing framework names. Any description of this project's results should use observed behavior and disclose whether its data was synthetic, live metadata, abstract text, or accessible full text.
