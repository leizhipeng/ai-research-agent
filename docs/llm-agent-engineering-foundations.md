# LLM Agent Engineering Foundations

**Purpose.** This document establishes a durable vocabulary and design method for building reliable LLM agents. It applies whether the runtime is handwritten Python, OpenAI Agents SDK, LangGraph, PydanticAI, or another orchestration framework. Framework APIs change; the engineering decisions described here do not.

An **LLM agent** is an application in which a language model repeatedly interprets a goal, selects from constrained capabilities, receives observations from the outside world, and either acts again or produces a final result. The model is one component of the system. The application provides the rules, tools, state, security boundaries, and termination policy that make its behavior useful and safe. An agent is therefore not simply a prompt with a chat history. [1] [2]

## A mental model for an agent

An agent execution alternates between a decision boundary and an application boundary. The model decides what information or operation it needs next. The application decides what is actually allowed, validates every request, executes the operation, and records the result. This distinction is fundamental: **models propose; applications authorize and execute**.

```text
Goal + current context
          │
          ▼
  Model decides next step
     │              │
     │              └── final response
     ▼
Tool request with typed arguments
          │
          ▼
Application validates and executes
          │
          ▼
Observation, trace, and state update
          │
          └──────────────► next model decision
```

The loop may involve zero, one, or many tool calls. It must be controlled by application-owned policies rather than assuming the model will always stop at the right time. In a mature system, the same run also includes guardrails, logging, cost accounting, error handling, and possibly a human approval gate.

## Core concepts at a glance

| Concept | Definition | Primary design question |
|---|---|---|
| LLM messages | The ordered input records given to a model for one turn. | Which information must the model see now? |
| System instructions | Developer-controlled behavior and operating rules for the model. | What role, limits, and decision policy should govern this run? |
| Tool calling | A model request for an application-owned capability. | Which capabilities should be available, and under what constraints? |
| Tool schema | A machine-readable contract for a tool’s name, purpose, and parameters. | Can the model invoke this tool correctly and safely? |
| Observation | The tool result or other external feedback returned to the model. | Is the result sufficient, truthful, bounded, and traceable? |
| Reasoning/action loop | Repeated model decisions and tool executions toward a goal. | How does the run make progress rather than repeat itself? |
| Termination conditions | Application-enforced rules that end, pause, or fail a run. | When must the system stop regardless of the model’s preference? |
| Structured output | A response constrained to a declared schema. | Which results are data contracts rather than prose? |
| Context | The information and capabilities supplied for a particular model decision. | What is the smallest complete input for a reliable decision? |
| State | Durable facts accumulated and updated during a workflow. | What must survive across turns, nodes, failures, and restarts? |

## LLM messages: the conversational protocol

A **message** is a typed record in the interaction protocol between an application and a model. Although exact field names differ across APIs, a tool-using conversation generally includes system, user, assistant, and tool messages.

| Message type | Origin | Purpose | Example content |
|---|---|---|---|
| System | Developer or application | Defines behavior, boundaries, and high-level operating policy. | “Use retrieved sources only for factual claims.” |
| User | End user | States the task, goal, question, or feedback. | “Compare methods for low-latency vision inference.” |
| Assistant | Model | Contains natural-language output and/or tool-call requests. | A request to search a scholarly index. |
| Tool | Application | Returns the result of one particular tool call. | Normalized search records, an error, or an approval request. |

Message ordering is meaningful. A tool response is not a generic note. It is an answer to a specific assistant tool call. When multiple tools are requested in one turn, each response must retain the identifier of the corresponding request. This pairing preserves causal history and lets the model correctly interpret parallel or repeated operations. [1]

Messages are often treated as “memory,” but raw history is not a complete memory design. It can become long, repetitive, and poorly structured. A robust agent decides which messages belong in a prompt, summarizes information that has lost tactical value, and preserves important facts separately in typed state.

## System instructions: behavior policy, not task data

**System instructions** are the application’s highest-level guidance to the model. They establish the model’s role, expected method, constraints, style, and safety boundaries. User input normally supplies a task; system instructions define how the task is approached.

Good instructions are concrete and testable. They describe a decision policy instead of relying on vague aspirations. For example, “use a search tool before making time-sensitive claims; cite only retrieved sources; state uncertainty when evidence is unavailable; do not execute a write operation without confirmation” gives the model operational guidance. “Be accurate and helpful” is useful as tone, but it does not specify reliable behavior.

| Instruction component | What it controls | Reliable form |
|---|---|---|
| Role and objective | The kind of work the model performs. | “Act as a literature research assistant.” |
| Grounding policy | Permitted evidence for factual claims. | “Base claims on tool results available in this run.” |
| Tool policy | When and how tools are used. | “Search before answering questions about recent papers.” |
| Output policy | Format, audience, uncertainty, and citation behavior. | “Return an evidence table and mark unsupported claims.” |
| Safety and authority | Prohibited behavior and approval requirements. | “Never perform a persistent write without explicit approval.” |
| Completion policy | What a satisfactory outcome looks like. | “Finish after each subquestion has evidence or is explicitly unresolved.” |

Instructions should be versioned and evaluated as production assets. Small wording changes can affect routing, grounding, cost, and safety. They should not contain credentials, broad untrusted input, or detailed data that is already better represented as a tool result or a state field.

## Tool calling: the controlled action interface

**Tool calling** lets a model request external information or an operation through a formal interface. A tool can retrieve data, transform content, perform a computation, query a database, call another service, or request a human decision. It does not give the model direct execution privileges. The application receives the request and remains responsible for validation, authorization, execution, and recording.

A standard tool-call interaction has five stages: the application sends available tool definitions with a model request; the model returns one or more tool-call requests; the application executes the requested functions; the application sends associated outputs back; and the model either produces a final response or requests more tools. [1]

The model’s choice may be **automatic**, where it decides between answering and using a tool; **required**, where it must select some available tool; or **forced**, where it must call a particular tool. Automatic selection is usually appropriate for general research work. Required and forced choices are useful for controlled pipeline stages, tests, and flows where an answer without retrieval would be invalid. [2]

Tool use must be treated as untrusted input. The model can choose an unavailable name, omit fields, produce malformed JSON, request an action that violates policy, or call a valid tool with an unsafe parameter. Tool execution must validate the request independently of the model’s apparent confidence.

## Tool schemas: contracts for model-to-application requests

A **tool schema** defines a tool’s interface in a format the model can use. For function tools, the contract usually contains a clear name, a concise behavior-oriented description, an object schema for arguments, required fields, allowed value types, and a rule that undeclared properties are rejected.

| Schema element | Engineering role | Design guidance |
|---|---|---|
| Name | Stable programmatic identity. | Use an action-oriented, unambiguous name such as `search_papers`. |
| Description | The primary natural-language routing signal. | State what the tool does, what it does not do, and when it is appropriate. |
| Parameters | Typed input contract. | Use meaningful field names, descriptions, ranges, and enumerations. |
| Required fields | Minimum valid request. | Require the fields necessary for a safe, useful execution. |
| Extra-field policy | Defense against silent changes in behavior. | Reject undeclared fields for strict structured interfaces. |
| Result contract | The observation structure returned after execution. | Normalize useful output and include provenance, status, and errors. |

A schema should make the correct action easy and the incorrect action difficult. A tool that combines search, database writes, web scraping, and report publication into one ambiguous interface is difficult for a model to route, difficult to secure, and difficult to evaluate. Prefer small tools with one responsibility and an explicit side-effect boundary.

Schema validation can use Pydantic models in Python. A Pydantic model produces a valid in-memory object after validation, supports serialization, and can generate JSON Schema. This makes one contract useful at the application boundary, in tests, and in tool declarations. [3]

## Observations: the agent’s connection to the world

An **observation** is information returned to the model after an action. A database record, a scholarly search result, a calculation result, a web retrieval, a tool error, a rate-limit message, and a human approval decision are all observations. They are not model thoughts; they are application-produced records that update the model’s knowledge of the current situation.

An observation should be **relevant, bounded, structured, and attributable**. Returning hundreds of raw search records can dilute the useful evidence and spend prompt tokens. Returning only “search succeeded” leaves the model unable to reason about the result. A good search observation contains a bounded list of normalized records, source identifiers, a query, metadata that supports ranking, and a clear statement if no results were found.

| Observation quality | Reliable behavior | Failure mode when absent |
|---|---|---|
| Relevance | Include information needed for the next decision. | The model guesses or issues redundant calls. |
| Provenance | Identify source, timestamp, record IDs, and query where appropriate. | Claims cannot be audited or verified. |
| Bounded size | Limit results and summarize large payloads. | Context becomes expensive and attention degrades. |
| Structural clarity | Use a stable data contract. | The model misreads data or downstream code cannot consume it. |
| Error transparency | Return actionable errors as tool results when recovery is possible. | The model hallucinates success or the run crashes prematurely. |

A tool error is often a valid observation. For example, “provider timed out; no records returned; retry after 30 seconds” lets the agent select another source or report an incomplete result. An internal invariant violation or corrupt workflow state is different: it should normally halt or fail the run rather than invite the model to improvise around an application bug.

## The reasoning/action loop: controlled iterative work

A **reasoning/action loop** is the repeated sequence in which the model uses its current context to decide whether to answer, call a tool, ask for clarification, delegate, or stop. “Reasoning” here means decision-making at the application boundary. Production systems should not rely on or store hidden chain-of-thought. They should retain **observable rationale** where useful: chosen queries, tool calls, source IDs, result summaries, and structured review findings.

A single tool call does not make a good agent. The loop becomes agentic when it can adapt to an observation. For example, a research agent may search for a question, notice missing evidence for a subquestion, generate a narrower query, retrieve more material, and then synthesize only the supported findings. Its agency is the ability to choose the next bounded operation in response to external feedback.

The loop should be designed around progress. Every iteration should either reduce uncertainty, acquire a required artifact, satisfy a coverage criterion, surface a recoverable constraint, or end the run. When an iteration does none of these, the system needs a guardrail: perhaps duplicate-call detection, better tool descriptions, a smaller context, or a termination rule.

| Loop stage | Model decision | Application responsibility | Record to retain |
|---|---|---|---|
| Prepare | Interpret goal and available information. | Assemble the minimum relevant context. | Prompt version and context summary. |
| Decide | Answer, call tool, delegate, request clarification, or pause. | Check that the requested transition is allowed. | Model response and selected action. |
| Validate | Supply arguments or a structured result. | Validate schema, authority, and policy. | Validated request or validation failure. |
| Execute | None. | Invoke bounded capability with timeouts and retries where appropriate. | Status, latency, provider metadata, result reference. |
| Observe | Interpret the returned result. | Attach result to the correct request and update state. | Observation and provenance. |
| Evaluate progress | Decide whether another step is needed. | Apply deterministic limits and quality gates. | Metrics, coverage status, termination reason. |

## Termination conditions: stopping is engineered

An LLM must not be the only authority that decides when an agent stops. A model can continue calling a tool because it is uncertain, because a forced tool choice persists, because an observation is unclear, or because it has entered a repetitive pattern. The application needs explicit, measurable termination conditions.

| Condition type | Examples | Why it exists |
|---|---|---|
| Success condition | All required fields are present; every research subquestion is addressed or declared unresolved. | Defines useful completion rather than merely a fluent response. |
| Step and loop bounds | Maximum model calls, tool calls, search rounds, or repeated-action count. | Prevents infinite or low-value loops. |
| Resource budget | Maximum cost, tokens, wall-clock time, API calls, or documents processed. | Makes the system operationally predictable. |
| Error threshold | Maximum retries; non-retryable schema or authorization failure. | Stops unrecoverable or harmful repetition. |
| Human approval gate | Request confirmation before processing a large corpus or executing a write. | Keeps consequential decisions under user control. |
| Cancellation and deadline | User cancellation, expired job deadline, shutdown signal. | Preserves user control and system health. |

Termination should produce a first-class outcome: **completed**, **paused awaiting input**, **halted by policy**, **cancelled**, or **failed**. “No answer” is not a sufficient operational status. A durable run record identifies the exact termination reason and the artifacts gathered before termination.

## Structured output: type safety for model results

**Structured output** asks the model to return data conforming to a declared schema instead of unconstrained prose. Typical use cases include research plans, paper analyses, evidence records, routing decisions, evaluation results, and citation checks. It is especially valuable whenever a model response drives application logic.

Structured Outputs can enforce adherence to a supplied JSON Schema, including required keys and permitted enum values. This is stronger than asking the model to “respond in JSON,” but it does not make the contents factually correct. A schema can ensure a `confidence` field is a number in the expected position; it cannot ensure that the number is calibrated or that an extracted claim is supported by evidence. [4]

| Requirement | Prompted JSON | Schema-constrained output | Application validation |
|---|---|---|---|
| Produces parseable JSON | Often, but not guaranteed. | Designed to do so, subject to refusal or incompleteness. | Always required at the trust boundary. |
| Includes required keys | Not guaranteed. | Enforced by the supported schema subset. | Confirm business invariants. |
| Respects types and enums | Not guaranteed. | Enforced by the schema. | Validate provider response and domain constraints. |
| Is factually grounded | Not guaranteed. | Not guaranteed. | Check against sources and evidence. |
| Is authorized or safe | Not guaranteed. | Not guaranteed. | Apply policy and permission checks. |

A schema-constrained call can still fail because the model refuses, output is cut off, the provider rejects an unsupported schema, or the returned content cannot be trusted semantically. Every structured-output path needs an explicit refusal and incomplete-response policy. Strict schemas also have provider-specific limits; for example, nested object depth and unsupported JSON Schema keywords may be constrained. [4]

## Context: the input selected for one decision

**Context** is the set of information and capabilities made available to a model for a particular turn. It typically includes system instructions, relevant messages, tool schemas, retrieved evidence, a response schema, selected state fields, and sometimes a short summary of earlier work. Context engineering is the deliberate process of selecting and formatting that information so that the model can make a reliable decision. [5]

Context is not synonymous with conversation history. It is a curated view. The full history may contain important facts but also irrelevant discussion, repeated tool payloads, superseded plans, and secrets that should never reach the model. An agent should construct context from explicit sources rather than indiscriminately replay every event.

| Context source | Scope | Typical content | Handling principle |
|---|---|---|---|
| System instructions | Run or agent scope | Role, policy, tool-use rules, completion standards. | Stable, versioned, and concise. |
| Recent messages | Turn scope | Latest user request, questions, and tool observations. | Keep causal order; summarize obsolete detail. |
| Workflow state | Run scope | Plan, selected papers, evidence coverage, budgets. | Select only fields needed by this node. |
| Long-term store | Cross-run scope | User preferences, saved research artifacts, prior conclusions. | Retrieve deliberately; do not blindly inject. |
| Runtime context | Execution scope | User identity, tenant, permissions, API clients, configuration. | Supply to tools and application logic; never expose secrets to the model. |
| Tool definitions | Turn scope | Available action interfaces. | Offer only relevant, permitted tools. |

The right context is often the biggest determinant of agent reliability. More tokens are not automatically more helpful. Good context reduces ambiguity, shows the model the evidence it needs, exposes only applicable actions, and leaves enough space for the model’s response.

## State: durable workflow facts

**State** is the application-owned record of facts accumulated during a workflow. It is distinct from the text sent to the model. State should be structured, validated, and updated by well-defined transitions. It supports inspection, resume, evaluation, concurrency control, and reliable handoffs between workflow nodes.

A useful distinction separates three data scopes.

| Data scope | Lifetime | Examples | Where it belongs |
|---|---|---|---|
| Runtime context | One execution environment | API clients, credential handles, logger, tenant permissions, feature flags. | Dependency injection or runtime container. |
| Workflow state | One agent run or conversation | Question, plan, selected papers, tool trace, approvals, current stage, counters. | Typed state object and checkpoint store. |
| Long-term store | Across runs | Persisted evidence, user preferences, historical evaluation baselines, saved reports. | Database, object store, or dedicated memory service. |

A field belongs in workflow state when a later decision, user, evaluator, or recovery process needs it. A field does not belong there merely because it was once available. Large raw documents, credentials, transient HTTP clients, and redundant derived fields usually increase serialization cost and make checkpointing fragile. Instead, state can keep durable identifiers and references to externally stored content.

State must have ownership rules. A planner may create or update a research plan. A search component may append normalized candidate records. A reviewer may add coverage findings. A tool should not silently rewrite another component’s authoritative data. Clear ownership makes node-level testing and later graph orchestration much easier.

## Context and state are related but not interchangeable

Context is **what the model sees now**. State is **what the application remembers and manages across time**. State may inform context, but it is not automatically sent to the model. This distinction helps control cost, protects sensitive data, and prevents a large workflow from becoming a single unbounded prompt.

> A practical rule: persist information because the workflow must retain it; place information in a prompt because the model needs it for the next decision.

For a literature-research workflow, the current search plan, selected source identifiers, evidence coverage metrics, and search-round count belong in state. The next model call may see only the question, unresolved subquestions, a concise evidence table, and the few tools applicable at that stage. The full paper PDFs and service credentials should not be passed automatically.

## An implementation-neutral design checklist

Before adding a capability, review its interface and lifecycle against these questions.

| Design area | Questions to answer |
|---|---|
| Goal | What concrete artifact or decision marks success? |
| Instructions | What should the model do, avoid, and disclose? |
| Tools | What is the smallest useful tool set? Which tools have side effects? |
| Schemas | Which input and output fields are required, constrained, and versioned? |
| Validation | What happens when arguments are malformed, unauthorized, or semantically invalid? |
| Observations | How will results preserve provenance, errors, size bounds, and causal linkage? |
| State | Which facts must survive another turn, a retry, and a restart? Who owns each field? |
| Context | Which state fields, messages, tools, and instructions are necessary for this one decision? |
| Termination | What success, budget, loop, error, and approval policies stop the run? |
| Evaluation | Which traces and metrics reveal whether this capability improved the workflow? |

## Common failure patterns and corrective actions

| Failure pattern | Likely cause | Corrective action |
|---|---|---|
| The model answers from general knowledge instead of searching. | Instructions or tool policy are weak; search is optional without a grounding requirement. | State an explicit grounding policy; use a deterministic pipeline stage or required tool mode where appropriate. |
| The model repeatedly calls the same tool. | Ambiguous observations, persistent forced tool choice, or no loop guard. | Return clearer status; reset tool choice; detect duplicate requests; enforce step and budget limits. |
| Tool calls contain unusable arguments. | Schema is vague, tool description is unclear, or validation is missing. | Improve parameter descriptions, constrain types, reject extras, and return actionable validation errors. |
| The context window fills with raw outputs. | Tool payloads are unbounded and all history is replayed. | Limit results, store large artifacts externally, summarize selectively, and retrieve by relevance. |
| State becomes inconsistent after retries. | Multiple components mutate fields without ownership or idempotency. | Use explicit transitions, stable identifiers, append-only event records where useful, and idempotent writes. |
| Valid structured output contains an unsupported claim. | Format validation has been confused with evidence validation. | Link claims to retrieved evidence and run citation or evidence-support checks. |
| A run appears to succeed after a provider error. | Errors are swallowed or represented as ordinary empty results. | Preserve status, error type, retryability, and provenance in the observation and final outcome. |

## How these concepts fit together

The concepts in this guide form one engineering chain. System instructions and curated context give the model a bounded decision environment. Tool schemas express the actions it may request. The application validates and performs those requests, then returns observations. Typed workflow state preserves the durable facts created by the loop. Structured output makes critical model-produced artifacts machine-consumable. Termination conditions ensure that the loop is governed by measurable product policy.

A framework should be chosen only after this chain is clear. A handwritten loop is valuable for learning its mechanics. An agent SDK can package recurring orchestration. A graph runtime can make multi-stage state transitions, conditional routing, checkpoints, and human approval explicit. None of those choices removes the need to design messages, instructions, schemas, observations, context, state, and termination deliberately.

## Recommended study exercises

| Exercise | Learning objective | Evidence of understanding |
|---|---|---|
| Trace a single tool call end to end. | Distinguish model request, application execution, observation, and final response. | Explain each message and its originating component. |
| Design two tool schemas for the same task. | Learn how names, descriptions, and input constraints affect routing. | Defend why one interface is safer and easier to evaluate. |
| Convert a prose research plan into a structured-output contract. | Separate format reliability from factual reliability. | Identify semantic checks that remain necessary after schema validation. |
| Audit a workflow state object. | Distinguish context, state, and long-term storage. | Move credentials, large raw payloads, and derived fields to more appropriate locations. |
| Simulate a non-converging loop. | Design deterministic termination. | Show the exact recorded status and reason after the limit is reached. |
| Compare a raw tool result with a normalized observation. | Understand grounding and context size. | Identify source IDs, errors, ranking data, and irrelevant fields. |

## References

[1]: https://developers.openai.com/api/docs/guides/function-calling "Function calling | OpenAI API"
[2]: https://openai.github.io/openai-agents-python/agents/ "Agents | OpenAI Agents SDK"
[3]: https://docs.pydantic.dev/latest/concepts/models/ "Models | Pydantic Documentation"
[4]: https://developers.openai.com/api/docs/guides/structured-outputs "Structured model outputs | OpenAI API"
[5]: https://docs.langchain.com/oss/python/langchain/context-engineering "Context engineering in agents | LangChain Documentation"
