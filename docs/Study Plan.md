14-Day Intensive AI Agent Engineer Study Plan — Scientific Research Agent
# 14-Day Intensive AI Agent Engineer Study Plan

## Project: Agentic Scientific Research Assistant

**Duration:** 14 days  
**Daily study time:** 4 hours  
**Total study time:** 56 hours

---

# 1. Overall Goal

The goal of this two-week program is to learn modern AI Agent engineering by building one serious portfolio project:

# Agentic Scientific Research Assistant

The system should help a researcher:

1. Understand a research question.
2. Decompose it into subquestions.
3. Generate literature-search queries.
4. Search multiple academic sources.
5. Rank and deduplicate papers.
6. Read abstracts and paper content.
7. Extract structured evidence.
8. Compare papers.
9. Detect contradictory findings.
10. Verify citations.
11. Identify research gaps.
12. Decide whether more research is required.
13. Produce a structured literature-review report.

The final application should behave more like a research workflow than a chatbot.

---

# 2. Target Final Architecture

```text
                         User
                          |
                          v
                  Research Planner
                          |
                          v
                  Query Generator
                          |
                          v
              Literature Search Layer
                 /        |        \
                /         |         \
            arXiv      OpenAlex   Semantic Scholar
                \         |         /
                 \        |        /
                  Paper Ranking
                        |
                        v
                  Paper Reader
                        |
                        v
                Evidence Extractor
                        |
                        v
                  Evidence Store
                        |
             +----------+----------+
             |                     |
             v                     v
       Comparison Agent      Citation Verifier
             |                     |
             +----------+----------+
                        |
                        v
                  Research Writer
                        |
                        v
                  Reviewer Agent
                        |
             +----------+----------+
             |                     |
     Enough evidence?          More evidence?
             |                     |
            Yes                    No
             |                     |
             v                     v
      Final Research Report    Search Again
                                   |
                                   +-----> Search Layer
```

---

# 3. Recommended Final Technology Stack

## Core

- Python
- `uv`
- Pydantic
- OpenAI-compatible LLM API
- LangGraph
- MCP
- SQLite initially
- `pytest`
- `httpx`
- `asyncio`

## Research APIs

Use one or more of:

- arXiv
- OpenAlex
- Semantic Scholar
- Crossref

Do not try to integrate every academic database during the two weeks.

Two sources are enough for the first complete version.

---

# 4. Framework Strategy

During the two weeks:

### Days 1–4

Learn agent fundamentals and OpenAI Agents SDK.

### Days 5–7

Build research infrastructure, MCP, evidence extraction, and evaluation.

### Days 8–10

Move the workflow to LangGraph.

### Day 11

Learn PydanticAI as a comparison exercise.

### Days 12–14

Production engineering, evaluation, portfolio preparation, and interview preparation.

The final repository should have one primary production architecture.

Recommended:

```text
LangGraph
    ↓
main research workflow

Pydantic
    ↓
structured data models

MCP / Python tools
    ↓
research capabilities
```

OpenAI Agents SDK and PydanticAI can remain in:

```text
experiments/
```

rather than becoming unnecessary dependencies in the final application.

---

# 5. Final Repository Target

By Day 14, aim for:

```text
agentic-research-assistant/
│
├── src/
│   └── research_agent/
│       │
│       ├── agents/
│       │   ├── planner.py
│       │   ├── search_agent.py
│       │   ├── reader.py
│       │   ├── evidence_agent.py
│       │   ├── comparison_agent.py
│       │   ├── citation_verifier.py
│       │   ├── reviewer.py
│       │   └── writer.py
│       │
│       ├── tools/
│       │   ├── arxiv_search.py
│       │   ├── openalex_search.py
│       │   ├── paper_reader.py
│       │   └── citations.py
│       │
│       ├── models/
│       │   ├── paper.py
│       │   ├── evidence.py
│       │   ├── research_plan.py
│       │   └── report.py
│       │
│       ├── workflows/
│       │   └── research_graph.py
│       │
│       ├── mcp/
│       │   └── research_server.py
│       │
│       ├── storage/
│       │   └── repository.py
│       │
│       └── config.py
│
├── experiments/
│   ├── manual_agent/
│   ├── openai_agents_sdk/
│   └── pydantic_ai/
│
├── evals/
│   ├── cases.json
│   ├── evaluator.py
│   └── metrics.py
│
├── tests/
│
├── examples/
│
├── docs/
│   ├── architecture.md
│   ├── evaluation.md
│   └── framework-comparison.md
│
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

---

# WEEK 1

# Foundations, Tools, Research Infrastructure, and Evaluation

---

# DAY 1 — Understand the Agent Loop and Define the Research System

## Goal

Understand what an AI Agent actually does without relying on LangGraph or another framework.

At the end of today, you should have a minimal research agent that can decide to call a search tool.

---

## Hour 1 — Learn the Agent Loop

Study:

- LLM messages
- system instructions
- tool calling
- tool schemas
- observations
- reasoning/action loops
- termination conditions
- structured output
- context
- state

Understand this loop:

```text
User Question
     |
     v
     LLM
     |
     +----> Final answer
     |
     +----> Tool call
               |
               v
             Tool
               |
               v
          Observation
               |
               +------> LLM again
```

You should be able to explain:

> Why is this an agent rather than a normal LLM call?

---

## Hour 2 — Implement a Framework-Free Agent Loop

Implement something conceptually similar to:

```python
messages = [...]

for step in range(MAX_STEPS):

    response = call_model(messages, tools)

    if response.has_tool_calls:
        for tool_call in response.tool_calls:
            result = execute(tool_call)
            messages.append(result)

    else:
        return response
```

Create one fake or simple research tool:

```python
search_papers(query: str)
```

It can initially return mocked data.

Example:

```python
[
    {
        "title": "Efficient Vision Transformers...",
        "year": 2025,
        "abstract": "..."
    }
]
```

---

## Hour 3 — Define the Research Domain Models

Create:

```python
class Paper(BaseModel):
    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    abstract: str | None
    url: str | None
```

Create:

```python
class ResearchQuestion(BaseModel):
    question: str
    scope: str | None
```

Create:

```python
class ResearchPlan(BaseModel):
    question: str
    subquestions: list[str]
    search_queries: list[str]
```

---

## Hour 4 — Define Project Requirements

Create:

```text
docs/project-requirements.md
```

Write:

### Functional requirements

The application must:

- accept a research question
- create a plan
- search papers
- analyze papers
- extract evidence
- verify citations
- generate a report

### Non-functional requirements

Eventually support:

- structured outputs
- retries
- timeouts
- caching
- checkpointing
- observability
- evaluation

---

## Project Milestone

You should be able to run:

```bash
uv run python experiments/manual_agent/main.py
```

Input:

```text
What methods are being used to accelerate vision transformers
on edge GPUs?
```

The agent should decide to call:

```text
search_papers(...)
```

---

## Done When

- [ ] You understand the basic agent loop.
- [ ] You have a working manual loop.
- [ ] At least one tool can be called.
- [ ] Pydantic research models exist.
- [ ] Repository structure exists.
- [ ] First Git commit is complete.

Suggested commit:

```bash
git commit -m "Day 1: implement minimal research agent loop"
```

---

# DAY 2 — OpenAI Agents SDK and Real Literature Search

## Goal

Replace the manual loop with a modern agent runtime and connect it to a real academic search source.

---

## Hour 1 — Learn OpenAI Agents SDK Fundamentals

Study:

- Agent
- Runner
- instructions
- function tools
- structured output
- run context
- tool errors
- tracing concepts

Do not memorize APIs.

Understand what the SDK does for you compared with Day 1.

---

## Hour 2 — Implement Real arXiv Search

Create:

```text
src/research_agent/tools/arxiv_search.py
```

Function:

```python
async def search_arxiv(
    query: str,
    max_results: int = 10,
) -> list[Paper]:
    ...
```

Normalize results into your own `Paper` model.

Do not let vendor-specific objects leak into the rest of the application.

Preferred architecture:

```text
arXiv API result
       |
       v
Adapter
       |
       v
Paper model
```

---

## Hour 3 — Build a Single Research Agent

Create an agent with tools:

```text
search_arxiv
```

and possibly:

```text
get_paper_details
```

The instructions should require the agent to:

1. Understand the question.
2. Generate useful academic queries.
3. Search papers.
4. Summarize only retrieved information.

Test:

```text
What are recent methods for efficient small-object detection?
```

---

## Hour 4 — Compare Manual Loop vs SDK

Create:

```text
docs/framework-comparison.md
```

Document:

| Feature | Manual Loop | Agents SDK |
|---|---|---|
| Tool dispatch | Manual | Built in |
| Tool schema | Manual | Easier |
| Tracing | Manual | Supported |
| Error handling | Manual | Better abstraction |
| Learning value | Excellent | Production useful |

---

## Project Milestone

The Research Agent can search a real literature source.

---

## Done When

- [ ] Real paper search works.
- [ ] Search results use your `Paper` schema.
- [ ] Agent calls the search tool correctly.
- [ ] At least five research questions have been tested.
- [ ] Framework comparison notes exist.

---

# DAY 3 — Search Quality, Ranking, Deduplication, and Query Expansion

## Goal

Turn simple API search into a genuine literature-discovery subsystem.

---

## Hour 1 — Learn Information Retrieval Concepts

Study:

- precision
- recall
- keyword search
- semantic relevance
- query expansion
- ranking
- duplicate detection
- metadata normalization

Also think about:

> Finding 100 papers is not useful if 80 are irrelevant.

---

## Hour 2 — Add a Second Search Provider

Recommended:

```text
OpenAlex
```

or:

```text
Semantic Scholar
```

Create:

```python
search_openalex(...)
```

Return the same:

```python
Paper
```

model.

Architecture:

```text
                  Search Service
                  /            \
                 /              \
              arXiv           OpenAlex
                 \              /
                  \            /
                normalize
                    |
                    v
               list[Paper]
```

---

## Hour 3 — Deduplication and Ranking

Implement:

```python
deduplicate_papers()
```

Use identifiers when available:

- DOI
- arXiv ID
- title normalization

Implement a simple ranking function.

Possible signals:

```text
keyword overlap
publication year
title similarity
abstract relevance
citation count
```

Do not over-engineer ranking yet.

---

## Hour 4 — Query Expansion

Given:

```text
"edge transformer inference optimization"
```

the Planner might generate:

```text
vision transformer edge inference
efficient ViT edge GPU
transformer TensorRT optimization
vision transformer quantization edge device
ViT pruning embedded GPU
```

Create:

```python
generate_search_queries()
```

Then run parallel searches.

---

## Project Milestone

```text
Research Question
       |
       v
Query Expansion
       |
       +------ query 1
       +------ query 2
       +------ query 3
       |
       v
Multiple Search Sources
       |
       v
Deduplication
       |
       v
Ranking
```

---

## Done When

- [ ] Two literature providers work.
- [ ] Duplicate papers are removed.
- [ ] Query expansion exists.
- [ ] Papers are ranked.
- [ ] Search result count is configurable.
- [ ] Tests exist for deduplication.

---

# DAY 4 — Multi-Agent Architecture

## Goal

Learn when multiple agents are useful and implement a Research Manager.

---

## Hour 1 — Learn Multi-Agent Patterns

Study:

### Handoff

```text
Planner → Search Agent
```

Responsibility moves.

### Agent as Tool

```text
Research Manager
      |
      +---- Search Specialist
      |
      +---- Analysis Specialist
```

Manager retains control.

### Supervisor pattern

```text
Supervisor
    |
    +---- Agent A
    +---- Agent B
    +---- Agent C
```

---

## Hour 2 — Create Research Planner

Input:

```text
How effective is INT8 quantization for vision transformers
on edge GPUs?
```

Expected structured output:

```json
{
  "objective": "...",
  "subquestions": [
    "...",
    "...",
    "..."
  ],
  "search_queries": [
    "...",
    "...",
    "..."
  ]
}
```

---

## Hour 3 — Create Search Specialist

Responsibilities:

- receive search plan
- execute searches
- deduplicate
- rank
- return candidate papers

Do not allow the Search Agent to write the final literature review.

Agent responsibilities should remain narrow.

---

## Hour 4 — Manager Agent

Create:

```text
Research Manager
      |
      +---- Planner
      |
      +---- Search Agent
```

Later you will add:

```text
Reader
Evidence Agent
Reviewer
Writer
```

---

## Project Milestone

The project is now multi-agent:

```text
User
 |
 v
Research Manager
 |
 +---- Planner
 |
 +---- Search Specialist
```

---

## Done When

- [ ] Research Planner works.
- [ ] Search Specialist works.
- [ ] Planner output is structured.
- [ ] Manager can coordinate both.
- [ ] You can explain Handoff vs Agent-as-Tool.

---

# DAY 5 — Paper Reading and Evidence Extraction

## Goal

Move from "search engine agent" to actual scientific analysis.

---

## Hour 1 — Learn Research Grounding

Understand the distinction between:

```text
Paper metadata
Paper summary
Claim
Evidence
Citation
Interpretation
```

Critical principle:

> A generated claim should be traceable to source evidence.

---

## Hour 2 — Build Paper Reader

Initially support:

```text
title
abstract
authors
year
URL
```

If full text is easily available, support it optionally.

Create:

```python
class PaperAnalysis(BaseModel):
    problem: str
    methodology: str
    datasets: list[str]
    metrics: list[str]
    findings: list[str]
    limitations: list[str]
```

---

## Hour 3 — Evidence Extraction

Create:

```python
class EvidenceItem(BaseModel):
    claim: str
    evidence_text: str
    paper_id: str
    location: str | None
    confidence: float
```

Architecture:

```text
Paper
 |
 v
Reader
 |
 v
Structured Paper Analysis
 |
 v
Evidence Extractor
 |
 v
EvidenceItem[]
```

---

## Hour 4 — Evidence Storage

Start simple.

Use:

```text
SQLite
```

Tables:

```text
papers

research_runs

evidence

queries
```

Avoid introducing a vector database unless you truly need one.

---

## Project Milestone

The agent can now produce evidence-backed findings rather than free-form paper summaries.

---

## Done When

- [ ] Paper analysis schema exists.
- [ ] Evidence schema exists.
- [ ] At least five papers can be analyzed.
- [ ] Evidence is stored.
- [ ] Every evidence object references a paper.

---

# DAY 6 — MCP for Research Tools

## Goal

Understand MCP and expose your research infrastructure through a standard tool interface.

---

## Hour 1 — Learn MCP Concepts

Understand:

```text
MCP Host
MCP Client
MCP Server

Tools
Resources
Prompts
Transport
```

Conceptually:

```text
Research Agent
      |
      v
  MCP Client
      |
      v
Research MCP Server
      |
   +--+------+------+
   |         |      |
 Search    Papers  Notes
```

---

## Hour 2 — Build Research MCP Server

Expose tools such as:

```text
search_papers
get_paper
list_saved_papers
save_research_note
find_evidence
```

---

## Hour 3 — Connect an Agent to MCP

Instead of directly importing:

```python
search_arxiv()
```

let the Agent discover and invoke the MCP research tools.

Observe the difference between:

```text
internal Python tool
```

and:

```text
remote/standardized MCP tool
```

---

## Hour 4 — Security and Tool Design

Think about:

```text
What should an Agent be allowed to do?

Which tools are read only?

Which tools modify persistent data?

What information should tools return?

Should one tool do many things?
```

Keep MCP tools small and explicit.

---

## Project Milestone

A standalone:

```text
Research MCP Server
```

exists.

---

## Done When

- [ ] MCP server starts successfully.
- [ ] Agent connects to MCP.
- [ ] Search works over MCP.
- [ ] Stored evidence can be retrieved.
- [ ] Tool interfaces are documented.

---

# DAY 7 — Evaluation System V1

## Goal

Build evaluation before the Agent becomes complicated.

This is extremely important.

---

## Hour 1 — Define Evaluation Dimensions

Measure separately:

### Search quality

- paper relevance
- duplicate rate
- search coverage

### Agent behavior

- correct tool selection
- routing quality
- unnecessary tool calls
- number of iterations

### Research quality

- citation correctness
- claim support
- summary faithfulness
- research coverage

### System metrics

- latency
- token usage
- number of model calls
- number of tool calls

---

## Hour 2 — Build Evaluation Dataset

Create at least:

```text
20 evaluation questions
```

Prefer research areas you understand well.

Examples:

```text
What techniques improve small-object detection?

What methods reduce Vision Transformer inference latency?

How is INT8 quantization applied to ViTs?

What are recent approaches to monocular 3D reconstruction?

How do DETR-based detectors handle small objects?
```

---

## Hour 3 — Implement Automated Evaluation

Create:

```python
run_eval_case()
```

Capture:

```python
class EvalResult(BaseModel):
    case_id: str
    retrieved_papers: int
    relevant_papers: int
    tool_calls: int
    latency_seconds: float
    success: bool
```

Add deterministic checks where possible.

---

## Hour 4 — Week 1 Demo

Run:

```text
5 representative research questions
```

Document failures.

Create:

```text
docs/week1-review.md
```

Include:

```text
What works

What fails

What produces hallucinations

What is too slow

What needs redesign
```

---

# WEEK 1 CHECKPOINT

You should now have:

- [ ] Manual agent loop
- [ ] OpenAI Agents SDK prototype
- [ ] Multi-source academic search
- [ ] Query expansion
- [ ] Deduplication
- [ ] Ranking
- [ ] Research Planner
- [ ] Search Agent
- [ ] Paper Reader
- [ ] Evidence extraction
- [ ] Evidence persistence
- [ ] MCP server
- [ ] Basic evaluation suite

---

# WEEK 2

# Stateful Orchestration, Review Loops, Reliability, and Portfolio Quality

---

# DAY 8 — LangGraph Fundamentals and Workflow Migration

## Goal

Understand why graph-based orchestration is useful for a Research Agent.

---

## Hour 1 — LangGraph Concepts

Study:

```text
State
Node
Edge
Conditional edge
Command
START
END
```

The important concept is:

```text
Agent workflow = state transformations
```

---

## Hour 2 — Design Research State

Create something similar to:

```python
class ResearchState(TypedDict):
    question: str
    plan: ResearchPlan | None

    search_queries: list[str]

    candidate_papers: list[Paper]
    selected_papers: list[Paper]

    evidence: list[EvidenceItem]

    draft: str | None

    review_feedback: list[str]

    search_round: int
```

Think carefully about what belongs in persistent state.

---

## Hour 3 — Implement Nodes

Start with:

```text
plan_research

search_literature

rank_papers

read_papers

extract_evidence
```

Build:

```text
START
 |
 v
Planner
 |
 v
Search
 |
 v
Rank
 |
 v
Read
 |
 v
Evidence
 |
 v
END
```

---

## Hour 4 — Test State Transitions

Inspect the state after every node.

You should understand:

```text
Who modifies the state?

What is persisted?

What should not be put in state?

How large can state become?
```

---

## Project Milestone

The main Research Agent now runs through LangGraph.

---

## Done When

- [ ] Research state is clearly defined.
- [ ] Five nodes exist.
- [ ] State transitions work.
- [ ] Search workflow completes.
- [ ] The old prototype remains in `experiments/`.

---

# DAY 9 — Persistence, Checkpoints, Human-in-the-Loop

## Goal

Make the research workflow durable.

A serious research workflow may take minutes or hours and should not restart from zero after failure.

---

## Hour 1 — Checkpointing

Study:

```text
checkpoint
thread/run ID
resume
persistence
```

Test:

```text
Planner
 ↓
Search
 ↓
Checkpoint
 ↓
application stops
 ↓
restart
 ↓
continue
```

---

## Hour 2 — Add Persistent Workflow State

Create a unique:

```text
research_run_id
```

Store:

```text
research question

workflow state

selected papers

completed stages
```

---

## Hour 3 — Human-in-the-Loop

Before analyzing 50 papers, pause.

Example:

```text
The system found 83 candidate papers.

I recommend analyzing the top 15 papers.

Research scope:
2022–2026
Edge inference optimization

Continue?
```

Allow:

```text
approve
modify scope
cancel
```

---

## Hour 4 — Resume Experiment

Perform this intentionally:

1. Start research.
2. Search papers.
3. Reach approval stage.
4. Stop the program.
5. Restart.
6. Resume the same research run.

---

## Project Milestone

The Research Agent supports durable research sessions.

---

## Done When

- [ ] Workflow state is persistent.
- [ ] Research runs have IDs.
- [ ] Interrupt works.
- [ ] Human approval works.
- [ ] Resume works after restart.

---

# DAY 10 — Reviewer Agent and Iterative Research

## Goal

Introduce the most important agentic behavior in the project:

> The system should decide when its evidence is insufficient.

---

## Hour 1 — Research Review Concepts

The Reviewer should check:

- Have the subquestions been addressed?
- Are enough sources available?
- Are claims supported?
- Are important perspectives missing?
- Are sources too old?
- Are findings contradictory?
- Is another search needed?

---

## Hour 2 — Build Reviewer Agent

Structured output:

```python
class ResearchReview(BaseModel):
    sufficient: bool

    missing_topics: list[str]

    unsupported_claims: list[str]

    contradictory_findings: list[str]

    recommended_queries: list[str]

    reason: str
```

---

## Hour 3 — Add Research Loop

Graph:

```text
Search
  |
  v
Analyze
  |
  v
Synthesize
  |
  v
Reviewer
  |
  +------ sufficient ------> Final
  |
  +------ insufficient
             |
             v
       Generate New Queries
             |
             v
           Search
```

---

## Hour 4 — Prevent Infinite Loops

Implement:

```python
MAX_SEARCH_ROUNDS = 3
MAX_PAPERS = 30
```

Also define termination based on:

```text
coverage

evidence quality

search rounds

cost budget
```

Never rely exclusively on:

```text
"LLM says it is done."
```

---

## Project Milestone

You now have a genuinely agentic research loop.

---

## Done When

- [ ] Reviewer exists.
- [ ] Reviewer output is structured.
- [ ] More research can be triggered.
- [ ] New queries are generated.
- [ ] Maximum search rounds exist.
- [ ] Infinite loops are prevented.

---

# DAY 11 — PydanticAI and Strongly Typed Agent Engineering

## Goal

Study another modern Agent design philosophy without rewriting your entire project.

---

## Hour 1 — Learn PydanticAI Concepts

Focus on:

```text
Agent
Dependencies
Tools
Structured outputs
Validation
Model abstraction
```

---

## Hour 2 — Build a Small PydanticAI Paper Analyst

Use:

```python
class PaperAnalysis(BaseModel):
    problem: str
    method: str
    datasets: list[str]
    findings: list[str]
    limitations: list[str]
```

Provide dependencies such as:

```python
@dataclass
class ResearchDependencies:
    paper_repository: PaperRepository
    evidence_repository: EvidenceRepository
```

---

## Hour 3 — Validation Experiments

Intentionally create cases where output is:

```text
missing fields

wrong types

invalid confidence scores

empty citations
```

Observe validation behavior.

---

## Hour 4 — Framework Comparison

Update:

```text
docs/framework-comparison.md
```

Compare:

```text
OpenAI Agents SDK

LangGraph

PydanticAI
```

Your expected conclusion should not be:

> Framework X is always better.

Instead:

```text
Simple model-driven Agent
→ lightweight SDK

Typed Python Agent application
→ PydanticAI is attractive

Complex stateful research workflow
→ LangGraph is attractive
```

---

## Project Milestone

You understand three distinct Agent architecture philosophies.

The final application still primarily uses LangGraph.

---

# DAY 12 — Production Engineering

## Goal

Turn the Research Agent from an experiment into a reliable application.

---

## Hour 1 — Failure Modes

Identify:

```text
LLM timeout

LLM rate limit

academic API timeout

PDF unavailable

invalid metadata

duplicate papers

malformed model output

MCP unavailable

tool returns empty result

review loop never converges
```

---

## Hour 2 — Retry and Timeout Policies

Implement reusable infrastructure.

Example:

```python
async def with_retry(...):
    ...
```

Configure:

```text
request timeout

max retries

exponential backoff

maximum agent iterations
```

Do not retry every error blindly.

---

## Hour 3 — Async and Parallelism

Parallelize operations such as:

```text
Read Paper A
Read Paper B
Read Paper C
Read Paper D
```

using:

```python
asyncio.gather(...)
```

But control concurrency:

```text
Semaphore
```

to avoid API rate-limit problems.

---

## Hour 4 — Caching and Observability

Cache:

```text
paper metadata

search results

paper analyses
```

Record:

```text
research_run_id

node

model

latency

tokens

tool

status

error
```

Example event:

```json
{
  "run_id": "research-123",
  "node": "paper_reader",
  "paper_id": "abc",
  "latency_ms": 1843,
  "status": "success"
}
```

---

## Project Milestone

The Research Agent now tolerates common production failures.

---

## Done When

- [ ] Timeouts exist.
- [ ] Retry strategy exists.
- [ ] Concurrency is bounded.
- [ ] Caching works.
- [ ] Failures are logged.
- [ ] Run IDs appear in logs.

---

# DAY 13 — Citation Verification and Evaluation V2

## Goal

Build the feature that makes the project credible as a research system:

# Citation verification.

---

## Hour 1 — Citation Verification Design

The final report should never simply contain:

```text
Claim + plausible-looking citation
```

Instead:

```text
Claim
  |
  v
Citation ID
  |
  v
Evidence record
  |
  v
Original paper
```

---

## Hour 2 — Build Citation Verifier

Create:

```python
class CitationCheck(BaseModel):
    claim: str
    paper_id: str

    supported: bool

    evidence: str | None

    confidence: float

    explanation: str
```

The verifier must answer:

> Does this source actually support this claim?

---

## Hour 3 — Evaluation Suite V2

Expand to:

```text
20–30 cases
```

Measure:

### Retrieval

```text
Precision@K

relevant papers retrieved
```

### Evidence

```text
claim support rate

citation correctness
```

### Agent behavior

```text
routing accuracy

unnecessary search rounds

tool errors
```

### Operational

```text
p50 latency

p95 latency

model calls

tool calls

token usage
```

---

## Hour 4 — Regression Testing

Save a baseline:

```text
eval_results/baseline.json
```

Whenever you modify:

```text
prompt

model

ranking

workflow
```

rerun evaluations.

Compare:

```text
before

vs

after
```

---

## Project Milestone

You now have an Agent system that can be quantitatively evaluated.

---

## Done When

- [ ] Citation verifier exists.
- [ ] Unsupported claims can be flagged.
- [ ] 20–30 eval cases exist.
- [ ] Baseline metrics exist.
- [ ] Regression evaluation runs automatically.

---

# DAY 14 — Final Research Report, Portfolio, Demo, and Interview Preparation

## Goal

Turn the system into something you can confidently show another engineer or interviewer.

---

# Hour 1 — Final Research Report

Generate a report with sections such as:

```text
Research Question

Executive Summary

Research Scope

Search Methodology

Key Findings

Evidence Table

Comparison of Approaches

Contradictory Findings

Limitations

Research Gaps

Future Research Directions

References
```

Example evidence table:

| Claim | Paper | Evidence | Confidence |
|---|---|---|---:|
| INT8 reduces inference cost | Paper A | Experiment section | 0.95 |
| Accuracy degradation depends on calibration | Paper B | Results section | 0.88 |

---

# Hour 2 — README and Architecture Documentation

README should explain:

## Problem

Why scientific literature research is difficult.

## Solution

What your Agent does.

## Architecture

Include graph diagram.

## Agent Roles

Explain:

```text
Planner

Searcher

Reader

Evidence Extractor

Reviewer

Citation Verifier

Writer
```

## Reliability

Explain:

```text
retry

timeouts

checkpointing

loop limits
```

## Evaluation

Show real metrics.

## Running the Project

Example:

```bash
uv sync

uv run research-agent \
  "What techniques accelerate vision transformers on edge GPUs?"
```

---

# Hour 3 — Record a Complete Demo

Use one strong research question.

Recommended example:

```text
What are the most effective approaches for optimizing
Vision Transformer inference on edge GPUs, and what
trade-offs do they introduce?
```

Show:

```text
1. Research plan created

2. 6 search queries generated

3. Candidate papers retrieved

4. Duplicates removed

5. Top papers selected

6. Papers analyzed

7. Evidence extracted

8. Findings compared

9. Reviewer identifies missing evidence

10. Second search executed

11. Citations verified

12. Final literature review generated
```

Save:

```text
examples/demo_output.md
```

---

# Hour 4 — Interview Preparation

Practice explaining the architecture without looking at code.

You should be able to answer all of these.

---

## Question 1

Why is this an Agent rather than a RAG application?

You should discuss:

```text
dynamic planning

tool selection

iterative search

state

review loop

termination decisions
```

---

## Question 2

Why use LangGraph?

Discuss:

```text
explicit workflow

state

conditional branching

checkpointing

pause/resume

research loops

durable execution
```

---

## Question 3

Why not use one giant Agent?

Discuss:

```text
separation of responsibilities

better prompts

evaluation

observability

failure isolation
```

But also acknowledge:

> Multi-Agent architecture should only be introduced when it improves the system.

---

## Question 4

How do you prevent hallucinated citations?

Explain:

```text
claim
 ↓
evidence ID
 ↓
paper
 ↓
citation verifier
```

---

## Question 5

How does the Agent know when research is complete?

Explain:

```text
coverage

evidence quality

reviewer

maximum search rounds

paper limits

budget
```

---

## Question 6

How do you prevent infinite Agent loops?

Discuss:

```text
MAX_SEARCH_ROUNDS

MAX_MODEL_CALLS

MAX_PAPERS

timeout

budget

explicit termination conditions
```

---

## Question 7

How would you scale from 20 papers to 100,000 papers?

Discuss:

```text
retrieval indexing

batch processing

queues

distributed workers

persistent storage

caching

embedding search

hierarchical summarization
```

---

# FINAL PROJECT ARCHITECTURE

By the end of Day 14:

```text
                         USER
                           |
                           v
                    Research Question
                           |
                           v
                  +-----------------+
                  | Research Planner|
                  +-----------------+
                           |
                           v
                   Search Queries
                           |
                  +--------+--------+
                  |                 |
                  v                 v
               arXiv            OpenAlex
                  |                 |
                  +--------+--------+
                           |
                           v
                    Deduplication
                           |
                           v
                       Ranking
                           |
                           v
                     Paper Reader
                           |
                           v
                  Evidence Extraction
                           |
                           v
                     Evidence Store
                           |
               +-----------+-----------+
               |                       |
               v                       v
         Comparison Agent       Citation Verifier
               |                       |
               +-----------+-----------+
                           |
                           v
                     Draft Report
                           |
                           v
                     Reviewer Agent
                           |
                +----------+----------+
                |                     |
             Enough?              Need more?
                |                     |
               YES                    NO
                |                     |
                v                     |
          Final Report                |
                                      |
                               Generate Queries
                                      |
                                      +----> Search
```

---

# FINAL SUCCESS CRITERIA

At the end of the two weeks, you should have completed:

### Agent Engineering

- [ ] Manual Agent loop
- [ ] Tool calling
- [ ] Structured outputs
- [ ] Multi-Agent concepts
- [ ] Context engineering
- [ ] Stateful workflows
- [ ] Conditional routing
- [ ] Research loops
- [ ] Checkpointing
- [ ] Human-in-the-loop
- [ ] MCP
- [ ] Evaluation
- [ ] Observability

### Research System

- [ ] Research Planner
- [ ] Query Generator
- [ ] Two academic search sources
- [ ] Deduplication
- [ ] Ranking
- [ ] Paper Reader
- [ ] Evidence Extractor
- [ ] Evidence database
- [ ] Comparison Agent
- [ ] Reviewer Agent
- [ ] Citation Verifier
- [ ] Research Writer

### Production Engineering

- [ ] Timeout handling
- [ ] Retry policy
- [ ] Async execution
- [ ] Bounded concurrency
- [ ] Caching
- [ ] Logging
- [ ] Persistent research state
- [ ] Maximum Agent loops
- [ ] Error handling

### Evaluation

- [ ] 20–30 evaluation cases
- [ ] Retrieval metrics
- [ ] Citation metrics
- [ ] Agent-behavior metrics
- [ ] Latency measurements
- [ ] Regression baseline

### Portfolio

- [ ] Professional GitHub README
- [ ] Architecture diagram
- [ ] Dockerfile
- [ ] `.env.example`
- [ ] Automated tests
- [ ] Example research report
- [ ] Evaluation report
- [ ] Framework comparison
- [ ] Interview explanation

---

# Recommended Time Allocation Across the 56 Hours

```text
Agent fundamentals             5 hours
OpenAI Agents SDK              5 hours
Research/search infrastructure 7 hours
Paper/evidence processing      6 hours
MCP                            4 hours
Evaluation                     7 hours
LangGraph                      8 hours
PydanticAI                     3 hours
Production engineering         5 hours
Portfolio/interview            6 hours
                              --------
Total                         56 hours
```

---

# What Not to Learn During These Two Weeks

Do not add:

```text
CrewAI
Agno
Microsoft Agent Framework
Google ADK
Pi Agents
five vector databases
three web frameworks
a complicated React frontend
Kubernetes
```

unless the core project is already finished.

These topics are useful later, but they distract from the primary objective.

The two-week goal is not:

> Learn as many Agent frameworks as possible.

The goal is:

> Learn how to engineer a stateful, tool-using, evidence-grounded, evaluable AI Agent system.

---

# Recommended Portfolio Positioning

A resume bullet can eventually look like:

> Built an agentic scientific research assistant that autonomously plans literature searches, retrieves and ranks academic papers, extracts structured evidence, compares findings, verifies citations, and iteratively expands research through reviewer-driven workflows using Python, LangGraph, MCP, and structured LLM outputs.

After collecting real evaluation results, improve it with measured numbers such as:

> Evaluated the system across 30 research tasks, measuring retrieval relevance, citation support, workflow success rate, token usage, and end-to-end latency.

Only include actual measured results.

---

# The Most Important Learning Outcome

At the end of these two weeks, you should not merely be able to say:

> I know LangGraph.

You should be able to say:

> I can design an Agent system from first principles, decide what belongs in context and persistent state, expose capabilities through tools and MCP, orchestrate a multi-stage workflow, enforce termination conditions, recover from failures, verify evidence, evaluate the system quantitatively, and explain why a particular framework is appropriate for the architecture.

That is the level of understanding you should target for an AI Agent Engineer role.