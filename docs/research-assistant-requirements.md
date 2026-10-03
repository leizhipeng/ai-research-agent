# Research Assistant Requirements

**Document status:** Implemented personal demo; verification scope recorded below
**Purpose:** Define the durable product, trust, and engineering requirements for the Agentic Scientific Research Assistant.
**Maintenance rule:** Update this document whenever a requirement, acceptance criterion, external interface, or architectural decision materially changes. The requirements define *what* the system must achieve. Implementation choices such as a handwritten loop, an agent SDK, LangGraph, MCP, or a particular storage engine define *how* a version achieves it.

**Current acceptance policy (2026-10-03).** The user's no-new-tests instruction
supersedes older test/evaluation-suite obligations. Validation uses installation,
imports, static checks, ordinary CLI/MCP runs, and retained-output inspection.
The primary workflow is `workflow.py` (LangGraph), contracts are
`models/workflow.py` (Pydantic), and persistence is `storage.py` (SQLite).
See [the walkthrough](architecture.md) and [observed outcomes](verification.md).
Validated means observed within this bounded demo, not proven general research
accuracy or completeness.

## 1. Product intent

The **Agentic Scientific Research Assistant** helps a researcher investigate a focused scientific or technical question through an explicit, evidence-grounded workflow. It is not intended to replace expert judgment, peer review, or access to complete scholarly databases. Its purpose is to reduce the mechanical burden of research discovery and synthesis while preserving a transparent connection between its outputs and the evidence used to support them.

The assistant must treat research as a process rather than as a single conversational response. A run begins with a question and scope. It then plans the investigation, discovers candidate sources, selects and analyzes evidence, identifies uncertainty or gaps, and produces a structured report. When evidence is insufficient, the system may recommend or perform additional bounded research rather than silently inventing a conclusion.

## 2. Scope and operating assumptions

The project is a cross-platform Python application managed with `uv`, with macOS as the primary development environment and Ubuntu/WSL 2 also supported. It uses an OpenAI-compatible language-model API, but the core domain model must not depend on a single model provider or framework. The initial target is literature research in technical fields, particularly areas where source quality, recency, and traceability matter.

The first complete version is a personal or portfolio-scale research system. It prioritizes **correctness of workflow, source traceability, reproducibility, and observability** over large-scale corpus processing. Enterprise multi-tenancy, a broad web frontend, and massive-scale indexing are explicitly outside the initial scope unless later requirements add them.

## 3. Guiding principles

| Principle | Requirement implication |
|---|---|
| Evidence before fluency | A well-written answer is insufficient unless factual research claims can be traced to retrieved source evidence. |
| Application-owned control | The application, not the language model, enforces permissions, validation, side-effect boundaries, budgets, and termination. |
| Typed boundaries | Inputs, domain artifacts, tool calls, tool results, and critical model outputs use explicit schemas. |
| Provider neutrality | External provider objects are normalized at the boundary and do not define internal domain contracts. |
| Explicit uncertainty | Unsupported, contradictory, stale, or missing evidence is surfaced rather than concealed. |
| Bounded autonomy | Iterative research is allowed only within configured resource, safety, and loop limits. |
| Inspectability | A completed, halted, or failed run must have enough trace information to explain its outcome. |
| Incremental complexity | A simple, testable implementation is preferred until additional orchestration or infrastructure demonstrably improves the requirements. |

## 4. System boundary

The assistant accepts a research question and optional constraints, uses approved information sources and application-owned tools, and returns research artifacts and a final report. The model may recommend actions through a tool-calling interface. The application validates, authorizes, and executes those actions.

```text
User question and research constraints
                  │
                  ▼
         Research workflow
  plan → retrieve → assess → synthesize
                  │
                  ├── approved research sources and tools
                  ├── typed artifacts and persistent run records
                  └── review, termination, and approval policies
                  │
                  ▼
Evidence-grounded research report and trace
```

The system must not present itself as a source of undisclosed scientific facts. It must distinguish retrieved evidence, model interpretation, and unresolved uncertainty. The system must not make high-impact domain decisions, such as medical diagnoses, legal determinations, or financial recommendations, on behalf of the user.

## 5. Functional requirements

### 5.1 Research intake and scope

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-01 | The system must accept a natural-language research question. | A run cannot start without a non-empty, validated question. | Validated |
| FR-02 | The system must support optional scope constraints. | A user can state boundaries such as date range, domain, method, hardware, source type, or maximum result count. | Validated |
| FR-03 | The system must assign every research run a unique identifier. | All emitted artifacts, events, and persisted records can be associated with one run. | Validated |
| FR-04 | The system must preserve the original request and applied constraints. | An inspector can reconstruct the research intent after a run completes or fails. | Validated |

### 5.2 Planning and query design

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-05 | The system must convert the question into an explicit research objective. | The objective is available as a structured artifact before retrieval. | Validated |
| FR-06 | The system must decompose sufficiently broad questions into subquestions. | Each subquestion is bounded, relevant to the objective, and represented separately. | Validated |
| FR-07 | The system must generate or accept one or more source-appropriate search queries. | Queries are retained with the source, time, and round in which they were used. | Validated |
| FR-08 | The system must preserve user-provided scope when generating plans and queries. | A scope-violating query or source-selection decision is detectable in the run trace. | Validated |

### 5.3 Source discovery and normalization

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-09 | The system must query approved scholarly or technical information sources through defined adapters. | A provider failure is represented as a controlled result rather than corrupting workflow state. | Validated |
| FR-10 | The system must normalize provider results into a provider-neutral `Paper` or equivalent source model. | Core workflow code does not require a vendor-specific result object. | Validated |
| FR-11 | Each source record must retain durable provenance fields. | The source/provider, source identifier, title, authors where available, publication date or year where available, URL, and retrieval context are stored. | Validated |
| FR-12 | The system must support more than one discovery source in the complete version. | A run can retrieve candidates from at least two independently implemented source adapters. | Validated |
| FR-13 | The system must detect and reconcile duplicate candidate records. | Duplicate rate and deduplication decisions are measurable; the retained record preserves identifiers from all matched sources where available. | Validated |
| FR-14 | The system must rank or select candidate records using explainable signals and configurable selection limits. | A selected-paper list includes a score or documented selection rationale. | Validated |

### 5.4 Reading, analysis, and evidence

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-15 | The system must analyze bounded source content, beginning with metadata and abstracts and optionally using full text when legitimately available. | The analysis records the source content level used, such as metadata, abstract, or full text. | Validated |
| FR-16 | The system must extract structured source analyses. | Analyses can represent research problem, methods, datasets, metrics, findings, and limitations when present. | Validated |
| FR-17 | The system must create evidence items that link a claim or finding to specific source text or a clearly identified source location. | Every evidence item has a source identifier, evidence text or location, and a confidence or support assessment. | Validated |
| FR-18 | The system must distinguish source evidence from model interpretation. | Final reports label direct evidence, synthesis, and unresolved inference separately where appropriate. | Validated |
| FR-19 | The system must retain evidence artifacts in persistent storage. | Evidence can be retrieved by research run, source, query, or claim after process restart. | Validated |

### 5.5 Synthesis, review, and citation integrity

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-20 | The system must compare relevant sources and approaches. | The report can describe agreement, differences in setup, and material trade-offs. | Validated |
| FR-21 | The system must identify contradictory or non-comparable findings. | A difference in task, data, metric, hardware, or experimental setup is not presented as a direct contradiction without explanation. | Validated |
| FR-22 | The system must assess whether evidence sufficiently addresses the defined scope. | The review result identifies addressed subquestions, missing topics, weakly supported claims, and recommended follow-up work. | Validated |
| FR-23 | The system must limit iterative research. | Further retrieval is constrained by configured maximum rounds, source/paper limits, time, and budget policies. | Validated |
| FR-24 | The system must verify citations against source-linked evidence before asserting that a source supports a report claim. | Every citation check records the claim, source identity, exact-text linkage, support decision, evidence, and explanation. Confidence scores are not proof. | Validated |
| FR-25 | The system must generate a structured literature-review report. | The report includes the question, scope, method, findings, evidence, limitations, gaps, and references appropriate to the run. | Validated |

### 5.6 Human control and interaction

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| FR-26 | The user must be able to inspect intermediate research artifacts. | The plan, queries, candidates, selected sources, evidence, review, and run status are viewable or exportable. | Validated |
| FR-27 | The user must be able to approve, pause, or cancel work at designated decision points. | The workflow can pause before high-cost or broad-scope analysis and can resume with a recorded user decision. | Validated |
| FR-28 | The system must clearly communicate limitations and incompleteness. | A final or partial report discloses unavailable sources, failed tools, capped retrieval, unresolved subquestions, and policy stops. | Validated |

## 6. Domain model and interface requirements

The domain model is a first-class product contract. It must remain independent of an individual search provider, agent framework, or user interface. Backward-incompatible changes require a documented migration decision for persisted data. This first production format has no migration from the historical in-memory loop.

| Artifact | Minimum responsibility | Required properties |
|---|---|---|
| Research question | Represents the user’s research intent. | Question text, optional scope, result and budget constraints. |
| Research plan | Represents the planned investigation. | Objective, subquestions, search queries, scope assumptions. |
| Source record | Represents normalized metadata and source provenance. | Stable internal ID, provider IDs, title, authors, date/year, URL, abstract/content reference. |
| Source analysis | Represents a structured reading of one source. | Problem, method, data, metrics, findings, limitations, source-content level. |
| Evidence item | Represents a traceable basis for a potential claim. | Claim, exact quote/span, source ID, content level, support decision and rationale. |
| Tool call and result | Represents an application-controlled action. | Unique call ID, tool name, validated inputs, status, result or error, latency. |
| Research review | Represents sufficiency and gap assessment. | Coverage, missing topics, unsupported claims, contradictions, recommended queries, reason. |
| Citation check | Represents source support for one output claim. | Claim, source ID, evidence, identity/linkage checks, support decision, explanation. |
| Research report | Represents the user-facing outcome. | Scope, methodology, findings, evidence table, limitations, gaps, references. |
| Run state | Represents durable workflow progress. | Run ID, status, stage, artifact references, counters, timestamps, termination reason. |

## 7. Trust, safety, and evidence requirements

The assistant must not fabricate papers, source identifiers, quotations, experimental results, or citations. It must not use a citation merely because the title or abstract is superficially related to a generated statement. Claims in a final report that rely on sources must be traceable to retained evidence and undergo the project’s citation-verification process before they are presented as supported.

The assistant must use approved tools with least privilege. Read-only retrieval tools and persistent write tools must have distinct interfaces. Persistent writes, external publication, large-scope processing, and other consequential operations require an explicit policy and, where appropriate, user approval. The language model is never treated as an authorization system.

| Requirement area | Mandatory behavior |
|---|---|
| Provenance | Retain a stable source identity and the retrieval or evidence context for every research-derived claim. |
| Grounding | Clearly limit factual synthesis to retrieved, retained, and applicable evidence. |
| Uncertainty | State when evidence is weak, indirect, contradictory, stale, unavailable, or outside the requested scope. |
| Scope discipline | Do not generalize across datasets, hardware, populations, tasks, or metrics without indicating the limitation. |
| Data handling | Do not expose secrets, credentials, or unnecessary personal data in prompts, logs, reports, or tool observations. |
| External actions | Make side effects explicit, validated, auditable, and approval-gated when the impact warrants it. |

## 8. Non-functional requirements

### 8.1 Reliability and recovery

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| NFR-01 | External model and source requests must have configurable timeouts. | A stalled dependency causes a controlled error or retry according to policy. | Validated |
| NFR-02 | Retry behavior must be selective and bounded. | Transient failures may retry with backoff; validation, authorization, and permanent input errors do not retry blindly. | Validated |
| NFR-03 | The workflow must be restartable after an interruption once persistence is introduced. | A saved run can resume from a recorded checkpoint without duplicating completed durable work. | Validated |
| NFR-04 | Tool and state operations that may be retried must be idempotent or explicitly de-duplicated. | A retry cannot silently create duplicate source records, evidence, or external side effects. | Validated |
| NFR-05 | Agent loops must be bounded by application-owned controls. | Maximum calls, rounds, papers, elapsed time, and cost-related limits have recorded enforcement outcomes. | Validated |

### 8.2 Performance and resource control

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| NFR-06 | Independent I/O work should execute concurrently when safe. | Multiple paper reads or source queries can run with bounded concurrency. | Validated |
| NFR-07 | The system must avoid unbounded context growth. | Large source content is referenced, summarized, chunked, or retrieved selectively rather than repeatedly injected in full. | Validated |
| NFR-08 | The system must cache safe, reproducible results where this reduces latency or provider cost. | Cache keys and freshness rules are explicit for metadata, search results, and analyses. | Validated |
| NFR-09 | Resource usage must be configurable. | Limits exist for result count, document count, concurrency, loop rounds, model calls, timeout, and budget. | Validated |

### 8.3 Observability and evaluation

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| NFR-10 | The system must emit structured execution events. | Events identify run, stage or node, model/tool, inputs or references, status, latency, errors, and usage where available. | Validated |
| NFR-11 | The system must support deterministic unit tests for core logic. | Schemas, normalization, ranking, deduplication, state transitions, limits, and error policy can be tested without a live model. | Superseded |
| NFR-12 | The system must maintain a versioned evaluation set. | Representative questions, expected retrieval/review properties, and evaluation metadata are stored in the repository. | Superseded |
| NFR-13 | The system must measure retrieval, evidence, agent behavior, and operational quality separately. | Evaluations report relevant metrics such as relevance, duplicates, claim support, citation correctness, tool errors, latency, and usage. | Superseded |
| NFR-14 | Significant behavior changes must be evaluated against a saved baseline. | A change to prompts, models, ranking, workflow, or tool policy is comparable to a prior baseline. | Superseded |

### 8.4 Maintainability and portability

| Identifier | Requirement | Acceptance criterion | Status |
|---|---|---|---|
| NFR-15 | The application must be installable and runnable on supported macOS environments through `uv`. | A new developer can bootstrap the environment and execute the documented import checks and example command from the standard macOS Terminal. | Validated |
| NFR-16 | Configuration must be externalized. | Secrets, endpoints, model choices, limits, and provider settings are supplied through environment or configuration, not source code. | Validated |
| NFR-17 | The implementation must separate domain models, tools/adapters, orchestration, persistence, and presentation. | A provider or orchestration replacement does not require broad changes to unrelated components. | Validated |
| NFR-18 | Public interfaces and important design decisions must be documented. | Documentation explains interfaces, assumptions, configuration, reliability policy, and known limitations. | Validated |

### Verification boundaries

- FR-01–28 and NFR-01–10,15–18 have exercised application paths; the
  [verification record](verification.md) specifies offline versus live evidence.
- Cross-source comparison/reviewer-directed iteration use the labelled synthetic
  corpus; live discovery and model-backed source analysis are also exercised.
  These runs do not establish comprehensive retrieval quality.
- FR-08 scope is retained in plan/support prompts and source metadata for
  inspection; date/hardware constraints are not hard filters.
- FR-15 full text means freely accessible extracted HTML with disclosed windows.
- FR-24 identity checks syntax/provenance consistency and exact evidence linkage;
  semantic support is a separate fallible model assessment.
- NFR-03/04 completed local artifacts replay safely. An external response lost
  before commit can repeat. NFR-05/09 byte/time controls stop at boundaries;
  in-flight socket reads can overrun, and actual read bytes are recorded.
- NFR-11–14 are superseded: no new tests, evaluation sets, automated metrics suite,
  or regression baselines. Historical test files remain untouched.

## 9. Quality gates

A feature is not complete merely because a demonstration appears plausible. The following quality gates apply to the relevant capabilities.

| Capability | Manual acceptance evidence |
|---|---|
| Tool/provider | Validated arguments, bounded I/O, controlled error, retained identifiers/query/retrieval context, actual invocation. |
| Structured output | Pydantic schema validation, refusal/incomplete-output handling, exact text and support checks. |
| Workflow | Ordinary run, review route, limits, approval, resume and saved-state inspection. |
| Persistence | Restarted CLI reuses artifacts/checkpoints; exported source/evidence text is inspectable. |
| Research claim | Source identity, quote linkage and separate support decision; unsupported drafts excluded. |
| Documentation | Commands run, module references checked, limitations tied to actual behavior. |

## 10. Delivery artifacts

The repository must progressively maintain the following reusable artifacts. Their exact file layout may evolve, but each artifact must have an obvious documented location.

| Artifact | Purpose |
|---|---|
| Project README | Explains problem, solution, installation, configuration, running, reliability, and current limitations. |
| Architecture documentation | Explains components, state/data flow, interfaces, trust boundaries, and key design decisions. |
| Requirements specification | This document; defines the product and engineering contract. |
| Source and domain models | Validated, provider-neutral contracts for research artifacts and run state. |
| Tool and provider adapters | Explicit, testable capabilities for retrieval and other research operations. |
| Workflow implementation | The primary orchestration logic and state transition definitions. |
| Example research output | A representative, clearly bounded report with its evidence trail. |
| Configuration template | Safe instructions for supplying environment-specific configuration without committing secrets. |

## 11. Requirement governance and change log

Requirements are intentionally expected to evolve. A change should update the relevant identifier, acceptance criterion, status, and affected documentation and verification record. Preserve identifiers once used in code, tests, or issue tracking; mark obsolete requirements as **Superseded** with a short reason rather than silently deleting them.

| Status | Meaning |
|---|---|
| Proposed | Under consideration; not yet committed to the project target. |
| Planned | Accepted requirement that has not started implementation. |
| In progress | Active work is changing implementation or documentation. |
| Partially implemented | Some acceptance criteria are met, but material work remains. |
| Implemented | Acceptance criteria are implemented and documented. |
| Validated | Implemented and verified through the applicable quality gate or evaluation. |
| Superseded | Replaced by a documented later requirement. |

| Version | Date | Change summary |
|---|---|---|
| 2.0 | 2026-10-03 | Implemented LangGraph/SQLite/CLI/MCP; superseded automated test/evaluation obligations with manual verification; recorded actual scope and recovery/resource limits. |
| 1.0 | 2026-09-05 | Recast the initial project notes as a living, architecture-agnostic requirements specification covering the complete research workflow and engineering quality attributes. |

## References

[1]: https://developers.openai.com/api/docs/guides/function-calling "Function calling | OpenAI API"
[2]: https://docs.pydantic.dev/latest/concepts/models/ "Models | Pydantic Documentation"
[3]: https://developers.openai.com/api/docs/guides/structured-outputs "Structured model outputs | OpenAI API"
