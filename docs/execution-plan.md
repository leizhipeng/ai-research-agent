# Completion execution plan

Objective: one small, evidence-grounded LangGraph research workflow, usable CLI/MCP,
and an implementation-grounded learning guide. No new tests, schedules, deployment,
publication, commits, or pushes. Existing tests and unrelated files are preserved.

## Milestones

1. **Done — review:** clean baseline; manual offline loop verified; mock search
   only, no production persistence. Read source/config/setup and all four docs.
2. **Done — workflow:** Pydantic contracts, arXiv/OpenAlex discovery, dedup/ranking,
   retained text, structured extraction, exact spans, separate semantic support,
   comparison checks, reviewer searches, deterministic Markdown, SQLite artifacts
   and LangGraph checkpoints.
3. **Done — operations:** bounds, selective retries, cache, events/usage, process
   ownership, CLI inspection/export/resume, explicit approval/pause/cancel, eight
   shared-function MCP tools and a discovery/invocation client demonstration.
4. **Done — teaching:** concise roadmap; extended foundations; actual function/
   artifact walkthrough; README commands; reconciled requirement statuses;
   manual verification record and saved synthetic/live report trails.
5. **Done — joint review:** atomic evidence/check writes, frozen analyzed text,
   historical ID retention, identity checks, comparison distinctness, approval
   replay, terminal/report recovery, control ownership race, budget reservations,
   redirect accounting/deadlines, metadata filtering, unused-plan cleanup.

## Decisions

- One primary graph of stage functions; no class for each conceptual agent role.
- Keep the small mock manual-loop example. SDK/PydanticAI remain comparisons.
- SQLite holds JSON artifacts/events/cache and graph checkpoints in one database.
- Claims require retained exact text plus a separate support assessment. Reports
  disclose reading depth; accepted source statements remain author-reported.
- Offline data is explicitly synthetic and cannot establish real research truth.
- Narrow known-paper searches can be steered with repeatable `--query`.
- Cancel/budget halt is terminal; paused/failed work can resume. Completed local
  operations are reused; responses lost before commit may repeat remotely.

## Completion evidence

- Setup/locked installation, imports, Ruff, compileall, and whitespace checks pass.
- Manual loop still runs offline; no changes/new files under `tests/`.
- Both real scholarly adapters, cross-provider dedup, cache, HTML reading, and
  byte-limit errors exercised. MCP client discovered/invoked tools.
- Offline report: 2 rounds, 3 exact synthetic evidence excerpts, 10 substitute
  calls, checked non-comparable setup relation, honest partial outcome.
- Focused live report: completed abstract-level FQ-ViT/PTF question, 2 accepted
  passages, 5 model calls, 4,277 observed tokens, cached responses from both APIs.
- Broader live run remains partial and records coverage/search-quality limitations.
- Approval across separate processes, generic/approved/repeated resume, terminal
  cancel, model-call exhaustion, invalid inputs, missing-key failure and exports
  exercised. Detailed commands/outcomes: [verification.md](verification.md).

## Blockers and next action

No required external blocker remains. Custom proxy/default-template-model access,
Ubuntu execution, and forced kill during remote calls were not verified; these are
explicit limits of the verification, not claimed successes. No new evaluation
suite is planned. Next action: explore README → roadmap/foundations → architecture
and the saved evidence trails.
