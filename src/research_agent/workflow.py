"""The primary research workflow: explicit stages, bounded iteration, durable artifacts."""

import hashlib
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from research_agent.config import Settings
from research_agent.discovery import (
    DiscoveryError,
    citation_identity,
    deduplicate_sources,
    offline_sources,
    read_source,
    search_papers,
)
from research_agent.model import structured_call
from research_agent.models.workflow import (
    Analysis,
    Evidence,
    Plan,
    ResearchRequest,
    Review,
    Source,
    SupportDecision,
)
from research_agent.storage import BudgetExceeded, ControlRequested, Store


class GraphState(TypedDict):
    run_id: str
    round: int
    queries: list[str]
    repeat: bool


def rank_sources(sources: list[Source], request: ResearchRequest) -> list[Source]:
    stopwords = {
        "what",
        "which",
        "how",
        "are",
        "the",
        "and",
        "for",
        "with",
        "does",
        "used",
        "being",
        "methods",
        "using",
    }
    terms = set(re.findall(r"[a-z0-9]+", request.question.lower())) - stopwords
    ranked = []
    for source in sources:
        words = set(
            re.findall(r"[a-z0-9]+", (source.title + " " + (source.abstract or "")).lower())
        )
        overlap = len(terms & words) / max(1, len(terms))
        recency = max(0, min(1, ((source.year or 2000) - 2000) / 30))
        source.score = round(0.8 * overlap + 0.1 * recency + 0.1 * bool(source.abstract), 4)
        source.selection_reasons = [
            f"question keyword overlap {len(terms & words)}/{len(terms)} (weight 0.8)",
            f"year {source.year or 'unknown'} (recency weight 0.1)",
            f"abstract available: {bool(source.abstract)} (weight 0.1)",
        ]
        if not terms.intersection(words):
            source.score = 0
            source.selection_reasons.append("Excluded: no question keyword overlap.")
        ranked.append(source)
    return sorted(ranked, key=lambda source: (-source.score, source.source_id))


def build_graph(store: Store, run_id: str, checkpointer):
    request = ResearchRequest.model_validate(store.get_run(run_id)["request"])
    limits = request.limits

    def stage(name, function):
        def execute(state):
            key = name + (
                f"/{state['round']}"
                if name in {"analyze", "review"}
                else f"/{state['round'] + 1}"
                if name == "search"
                else ""
            )
            saved = store.get(run_id, "stage/" + key)
            if saved is not None:
                return saved
            store.guard(run_id)
            store.update(run_id, stage=key)
            store.event(run_id, key, "started", {})
            started = time.monotonic()
            result = function(state)
            store.put(run_id, "stage/" + key, result)
            store.event(
                run_id, key, "completed", {"duration_seconds": round(time.monotonic() - started, 3)}
            )
            return result

        return execute

    def plan(state):
        result = structured_call(
            store,
            run_id,
            "plan",
            Plan,
            dict(question=request.question, scope=request.scope),
            "Create a focused objective and short scholarly queries of 2-5 topic keywords. Use one subquestion for a narrow factual question, 2-4 only when decomposition is useful. Preserve scope in scope_notes. Do not add abstract/full-text/paper/methods as search terms just because they describe the reading task. For example: vision transformer quantization. Avoid long AND queries that harm recall.",
        )
        result.search_queries = result.search_queries[: limits.max_queries]
        if request.search_queries:
            result.search_queries = request.search_queries[: limits.max_queries]
        store.put(run_id, "plan", result.model_dump(mode="json"))
        return {"queries": result.search_queries}

    def approval(state):
        # interrupt restarts this node; no non-idempotent operation precedes it.
        if request.pause_after_plan:
            decision = interrupt(
                {
                    "run_id": run_id,
                    "message": "Review saved plan; approve or cancel before retrieval.",
                }
            )
            store.put(run_id, "approval", {"decision": decision})
            if decision != "approve":
                raise ControlRequested("cancel")
        store.guard(run_id)
        return {}

    def options():
        settings = Settings.from_environment()
        remaining_bytes = (
            limits.max_download_bytes - store.get_run(run_id)["usage"]["download_bytes"]
        )
        if remaining_bytes <= 0:
            raise BudgetExceeded("max_download_bytes reached")
        return dict(
            timeout=min(settings.request_timeout_seconds, store.remaining_seconds(run_id)),
            max_bytes=min(2_000_000, remaining_bytes),
            remaining_seconds=lambda: store.remaining_seconds(run_id),
            openalex_api_key=settings.openalex_api_key.get_secret_value()
            if settings.openalex_api_key
            else None,
            cache_get=lambda key: cached_http(key),
            cache_set=store.cache_set,
            before_request=lambda: store.consume(run_id, "http_requests", 1, "max_http_requests"),
            on_bytes=lambda amount: store.consume(
                run_id, "download_bytes", amount, "max_download_bytes", actual=True
            ),
            on_retry=lambda reason: store.event(run_id, "retrieval", "retry", {"reason": reason}),
        )

    def cached_http(key):
        store.guard(run_id)
        cached = store.cache_get(key)
        if cached is not None:
            store.consume(run_id, "cache_hits", 1)
        return cached

    def search(state):
        round_number = state["round"] + 1
        queries = list(dict.fromkeys(state["queries"]))[: limits.max_queries]
        previous = [Source.model_validate(s) for s in store.get(run_id, "sources") or []]
        analyses = store.get(run_id, "analyses") or {}
        previous.sort(key=lambda source: source.source_id not in analyses)
        searches = [(query, provider) for query in queries for provider in request.providers]

        def retrieve(pair):
            query, provider = pair
            key = (
                "search/"
                + hashlib.sha256(f"{round_number}:{provider}:{query}".encode()).hexdigest()[:20]
            )
            saved = store.get(run_id, key)
            if saved is not None:
                return saved
            try:
                sources = (
                    offline_sources(query, round_number)
                    if request.mode == "offline"
                    else search_papers(query, provider, limits.results_per_query, **options())
                )
                result = dict(
                    query=query,
                    provider=provider,
                    round=round_number,
                    sources=[s.model_dump(mode="json") for s in sources],
                    error=None,
                )
            except DiscoveryError as exc:
                result = dict(
                    query=query, provider=provider, round=round_number, sources=[], error=str(exc)
                )
                store.event(
                    run_id, "search", "provider_error", {"provider": provider, "error": str(exc)}
                )
            store.put(run_id, key, result)
            return result

        if request.mode == "offline":
            searches = [(q, "synthetic") for q in queries]
        with ThreadPoolExecutor(max_workers=limits.concurrency) as pool:
            results = list(pool.map(retrieve, searches))
        sources = previous + [
            Source.model_validate(source) for result in results for source in result["sources"]
        ]
        ranked = rank_sources(deduplicate_sources(sources), request)
        frozen = {source.source_id: source for source in previous if source.source_id in analyses}
        for source in ranked:
            if source.source_id in frozen:
                original = frozen[source.source_id]
                for field in ("content", "content_level", "content_url", "access_note"):
                    setattr(source, field, getattr(original, field))
        # Keep historical source IDs/text if a later identifier bridge merges two analyzed records.
        ranked.extend(
            source for key, source in frozen.items() if key not in {s.source_id for s in ranked}
        )
        done = set(analyses)
        new = [s for s in ranked if s.source_id not in done and s.score > 0][
            : max(0, limits.max_papers - len(done))
        ]
        selected = [s.source_id for s in new]
        store.put(run_id, "sources", [s.model_dump(mode="json") for s in ranked])
        store.put(run_id, "selected", list(done) + selected)
        store.put(
            run_id,
            f"search_round/{round_number}",
            dict(
                queries=queries,
                results=results,
                raw_count=len(sources),
                unique_count=len(ranked),
                selected=selected,
            ),
        )
        return {"round": round_number, "repeat": False}

    def analyze(state):
        sources = [Source.model_validate(s) for s in store.get(run_id, "sources") or []]
        plan_data = store.get(run_id, "plan")
        analyses = store.get(run_id, "analyses") or {}
        evidence = store.get(run_id, "evidence") or []
        checks = store.get(run_id, "citation_checks") or []
        for source in sources:
            if (
                source.source_id not in (store.get(run_id, "selected") or [])
                or source.source_id in analyses
            ):
                continue
            store.guard(run_id)
            if request.full_text and request.mode == "live":
                source = read_source(source, **options())
                store.put(
                    run_id,
                    "sources",
                    [
                        source.model_dump(mode="json")
                        if s.source_id == source.source_id
                        else s.model_dump(mode="json")
                        for s in sources
                    ],
                )
                sources = [source if s.source_id == source.source_id else s for s in sources]
            if not source.content:
                analyses[source.source_id] = {
                    "content_level": "metadata",
                    "analysis": None,
                    "note": "No readable content; no evidence extracted.",
                }
                store.put(run_id, "analyses", analyses)
                continue
            window = source.content[:16_000]
            result = structured_call(
                store,
                run_id,
                f"analysis/{source.source_id}",
                Analysis,
                dict(
                    question=request.question,
                    scope=request.scope,
                    plan=plan_data,
                    source=dict(
                        source_id=source.source_id,
                        title=source.title,
                        year=source.year,
                        content_level=source.content_level,
                        content=window,
                    ),
                ),
                "Extract up to 3 important source statements, each with an EXACT contiguous quote and a 0-based plan subquestion index. For problem/method/limitations use verbatim source excerpts; datasets/metrics must be literal terms present in the text. Use empty strings/lists when unstated. Describe only content present in this reading window.",
            )
            for field in ("problem", "method"):
                if getattr(result, field) not in window:
                    setattr(result, field, "")
            for field in ("datasets", "metrics", "limitations"):
                setattr(
                    result,
                    field,
                    [item for item in getattr(result, field) if item and item in window],
                )
            for index, draft in enumerate(result.evidence):
                evidence_id = (
                    "ev-"
                    + hashlib.sha256(
                        f"{source.source_id}:{index}:{draft.quote}".encode()
                    ).hexdigest()[:12]
                )
                if any(check["evidence_id"] == evidence_id for check in checks):
                    continue
                start = source.content.find(draft.quote)
                valid = (
                    start >= 0
                    and start + len(draft.quote) <= len(window)
                    and draft.subquestion < len(plan_data["subquestions"])
                    and citation_identity(source)
                )
                decision = SupportDecision(
                    supported=False,
                    reason="Quote not in retained reading window or subquestion index invalid.",
                )
                if valid:
                    decision = structured_call(
                        store,
                        run_id,
                        "support/" + evidence_id,
                        SupportDecision,
                        dict(
                            question=request.question,
                            scope=request.scope,
                            source_title=source.title,
                            source_year=source.year,
                            content_level=source.content_level,
                            claim=draft.claim,
                            quote=draft.quote,
                            subquestion=plan_data["subquestions"][draft.subquestion],
                            context=source.content[
                                max(0, start - 500) : start + len(draft.quote) + 500
                            ],
                        ),
                        "Check whether the quotation supports the entire claim AND is relevant within the supplied question/scope. Keyword overlap alone is insufficient. Reject extrapolation, missing quantities, incompatible setups and invented facts. Explain the support decision; an abstract cannot establish unreported experimental details.",
                    )
                checks.append(
                    dict(
                        evidence_id=evidence_id,
                        source_id=source.source_id,
                        claim=draft.claim,
                        quote=draft.quote,
                        identity_valid=citation_identity(source),
                        linkage_valid=valid,
                        supported=valid and decision.supported,
                        reason=decision.reason,
                    )
                )
                if valid:
                    evidence.append(
                        Evidence(
                            evidence_id=evidence_id,
                            source_id=source.source_id,
                            claim=draft.claim,
                            quote=draft.quote,
                            start=start,
                            end=start + len(draft.quote),
                            content_level=source.content_level,
                            subquestion=draft.subquestion,
                            supported=decision.supported,
                            support_reason=decision.reason,
                        ).model_dump(mode="json")
                    )
                store.put_many(run_id, {"evidence": evidence, "citation_checks": checks})
            analyses[source.source_id] = dict(
                content_level=source.content_level,
                window_start=0,
                window_end=len(window),
                truncated=len(window) < len(source.content),
                analysis=result.model_dump(mode="json"),
            )
            store.put(run_id, "analyses", analyses)
        return {}

    def review(state):
        evidence = [item for item in store.get(run_id, "evidence") or [] if item["supported"]]
        plan_data = store.get(run_id, "plan")
        result = structured_call(
            store,
            run_id,
            f"review/{state['round']}",
            Review,
            dict(
                question=request.question,
                scope=request.scope,
                plan=plan_data,
                evidence=evidence,
                sources=[
                    dict(
                        source_id=s["source_id"],
                        title=s["title"],
                        content_level=s["content_level"],
                    )
                    for s in store.get(run_id, "sources") or []
                ],
                round=state["round"],
            ),
            "Assess coverage conservatively using only supported evidence. A subquestion is covered only when its evidence actually answers it. Identify gaps and useful short follow-up search queries. Compare sources using evidence IDs. Contradictions require comparable tasks/data/hardware/metrics; otherwise use different_setup or uncertain. Do not add unsupported research findings.",
        )
        valid_ids = {item["evidence_id"]: item for item in evidence}
        source_by_id = {item["source_id"]: item for item in store.get(run_id, "sources") or []}
        validated_comparisons = []
        comparison_checks = []
        for index, comparison in enumerate(result.comparisons):
            comparison.evidence_ids = list(dict.fromkeys(comparison.evidence_ids))
            valid = (
                all(key in valid_ids for key in comparison.evidence_ids)
                and len(
                    {
                        valid_ids[key]["source_id"]
                        for key in comparison.evidence_ids
                        if key in valid_ids
                    }
                )
                >= 2
            )
            if valid:
                compared_sources = {valid_ids[key]["source_id"] for key in comparison.evidence_ids}
                identities = []
                for source_id in compared_sources:
                    identifiers = source_by_id[source_id]["identifiers"]
                    identities.append(
                        {
                            (kind, value)
                            for kind, value in identifiers.items()
                            if kind in {"doi", "arxiv_unversioned", "openalex"}
                        }
                    )
                if any(
                    left & right
                    for i, left in enumerate(identities)
                    for right in identities[i + 1 :]
                ):
                    valid = False
            decision = SupportDecision(
                supported=False, reason="Comparison cites an unknown or unsupported evidence ID."
            )
            if valid:
                decision = structured_call(
                    store,
                    run_id,
                    f"comparison/{state['round']}/{index}",
                    SupportDecision,
                    dict(
                        claim=f"{comparison.relation}: {comparison.explanation}",
                        quote="\n".join(valid_ids[key]["quote"] for key in comparison.evidence_ids),
                    ),
                    "Assess whether the supplied exact source quotations support the comparison explanation AND relation. Contradiction requires comparable setups and opposing findings; absent setup details require uncertain. Reject unsupported metrics, datasets or conclusions.",
                )
            comparison_checks.append(
                dict(comparison=comparison.model_dump(mode="json"), **decision.model_dump())
            )
            if valid and decision.supported:
                validated_comparisons.append(comparison)
        result.comparisons = validated_comparisons
        actual_coverage = {item["subquestion"] for item in evidence}
        result.covered_subquestions = sorted(set(result.covered_subquestions) & actual_coverage)
        result.sufficient = (
            bool(evidence)
            and result.sufficient
            and len(result.covered_subquestions) == len(plan_data["subquestions"])
        )
        used = {
            q.casefold()
            for number in range(1, state["round"] + 1)
            for q in (store.get(run_id, f"search_round/{number}") or {}).get("queries", [])
        }
        normalized_queries = list(
            dict.fromkeys(query.strip()[:500] for query in result.followup_queries)
        )
        queries = [
            query
            for query in normalized_queries
            if len(query) >= 3 and query.casefold() not in used
        ][: limits.max_queries]
        can_repeat = (
            not result.sufficient
            and bool(queries)
            and state["round"] < limits.max_rounds
            and len(store.get(run_id, "analyses") or {}) < limits.max_papers
        )
        store.put(run_id, f"review/{state['round']}", result.model_dump(mode="json"))
        store.put(run_id, "review", result.model_dump(mode="json"))
        store.put(run_id, f"comparison_checks/{state['round']}", comparison_checks)
        if not can_repeat:
            reason = result.stop_reason
            if not result.sufficient:
                reason += " Stopped at configured rounds/papers or no useful new query; unresolved scope is disclosed."
            provider_errors = any(
                event["kind"] == "provider_error" for event in store.inspect(run_id)["events"]
            )
            store.put(
                run_id,
                "outcome",
                {
                    "status": "completed"
                    if result.sufficient and not provider_errors and request.mode == "live"
                    else "partial",
                    "reason": reason,
                },
            )
        return {"repeat": can_repeat, "queries": queries}

    def report(state):
        store.update(run_id, **store.get(run_id, "outcome"))
        save_report(store, run_id)
        return {}

    graph = StateGraph(GraphState)
    for name, function in {
        "plan": plan,
        "search": search,
        "analyze": analyze,
        "review": review,
        "report": report,
    }.items():
        graph.add_node(name, stage(name, function))
    graph.add_node("approval", approval)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "approval")
    graph.add_edge("approval", "search")
    graph.add_edge("search", "analyze")
    graph.add_edge("analyze", "review")
    graph.add_conditional_edges("review", lambda state: "search" if state["repeat"] else "report")
    graph.add_edge("report", END)
    return graph.compile(checkpointer=checkpointer)


def save_report(store: Store, run_id: str):
    data = store.inspect(run_id)
    run, artifacts = data["run"], data["artifacts"]
    request = run["request"]
    sources = {s["source_id"]: s for s in artifacts.get("sources", [])}
    accepted = [e for e in artifacts.get("evidence", []) if e["supported"]]
    review = artifacts.get("review", {})
    lines = [
        "# Research report",
        "",
        f"Run: `{run_id}` · Outcome: **{run['status']}**",
        "",
        f"**Question:** {request['question']}",
        "",
        f"**Scope:** {request['scope'] or 'No additional scope supplied.'}",
        "",
    ]
    if request["mode"] == "offline":
        lines += [
            "**SYNTHETIC OFFLINE DEMONSTRATION.** Papers and statements are invented teaching data. Deterministic model substitutes exercise the workflow. This is not a real literature review.",
            "",
        ]
    lines += [
        "## Search method",
        "",
        "Keyword discovery; deduplication by identifiers and conservative title matching. Ranking uses question word overlap (0.8), recency (0.1), and abstract availability (0.1). Citation counts do not establish relevance or truth.",
        "",
    ]
    for key, item in sorted(artifacts.items()):
        if key.startswith("search_round/"):
            lines += [f"Round {key.split('/')[-1]}: " + "; ".join(item["queries"]), ""]
            for result in item["results"]:
                lines += [
                    f"- {result['provider']}: {len(result['sources'])} records"
                    + (f"; error: {result['error']}" if result["error"] else "")
                ]
            lines.append("")
    lines += [
        "## Findings and direct evidence",
        "",
        "Statements below are attributed to retained source text. A support check establishes a bounded textual assessment, not independent experimental validation.",
        "",
    ]
    for item in accepted:
        source = sources[item["source_id"]]
        lines += [
            f"- **{item['evidence_id']}** — {item['claim']} [{source['title']}]({source['url']})",
            f"  - Basis: {item['content_level']}; retained text characters {item['start']}:{item['end']}; source `{item['source_id']}`.",
            "  - Exact quotation: " + item["quote"].replace("\n", " "),
            "  - Support assessment: " + item["support_reason"],
            "",
        ]
    if not accepted:
        lines += [
            "No supported research claim was retained. See saved artifacts for rejected claims and retrieval failures.",
            "",
        ]
    lines += ["## Comparisons and synthesis", ""]
    for comparison in review.get("comparisons", []):
        lines += [
            f"- **{comparison['relation']}**: {comparison['explanation']} (evidence: {', '.join(comparison['evidence_ids'])})"
        ]
    if not review.get("comparisons"):
        lines += [
            "No checked cross-source comparison is available. Differences in tasks, datasets, hardware, and metrics must be resolved before calling results contradictory."
        ]
    lines += ["", "## Coverage, gaps and uncertainty", ""]
    plan = artifacts.get("plan", {})
    covered = review.get("covered_subquestions", [])
    for index, subquestion in enumerate(plan.get("subquestions", [])):
        lines += [
            f"- {'Addressed within the retrieved evidence' if index in covered else 'Unresolved'}: {subquestion}"
        ]
    lines += ["- " + gap for gap in review.get("gaps", [])]
    lines += [
        "",
        "## Limitations and stopping condition",
        "",
        run["reason"] or "Run has not finished.",
        "",
        "Searches are bounded and do not establish systematic-review completeness. Metadata is not evidence of a result. Abstracts omit experimental detail. Accessible HTML may omit equations/figures and is read through a bounded window. Source statements remain author-reported. Model support judgments can be wrong; inspect exact quotations and scope before relying on the report.",
        "",
        f"Limits: `{request['limits']}`",
        "",
        f"Usage: `{run['usage']}`",
        "",
        "## References and reading depth",
        "",
    ]
    for source in sources.values():
        analysis = artifacts.get("analyses", {}).get(source["source_id"], {})
        depth = (
            f" Analysis read characters 0:{analysis['window_end']} of {len(source['content'])}; reading window truncated: {analysis['truncated']}."
            if "window_end" in analysis
            else " No text analysis was completed."
        )
        lines += [
            f"- [{source['title']}]({source['url']}) ({source.get('year') or 'year unknown'}), `{source['source_id']}`; IDs: `{source['identifiers']}`; **{source['content_level']}**. {source['access_note']}{depth}"
        ]
    lines.append("")
    store.put(
        run_id,
        "report",
        dict(markdown="\n".join(lines), evidence_ids=[e["evidence_id"] for e in accepted]),
    )


def run_research(
    question: ResearchRequest,
    db: str | Path,
    *,
    run_id: str | None = None,
    resume_decision: str | None = None,
) -> dict:
    store = Store(db)
    if run_id is None:
        run_id = store.create(question)
    else:
        saved = store.get_run(run_id)
        if saved["status"] == "halted":
            if store.get(run_id, "report") is None:
                save_report(store, run_id)
            return store.get_run(run_id)
        if (
            saved["status"] in {"completed", "partial", "halted"}
            and store.get(run_id, "report") is not None
        ):
            return saved
    store.acquire(run_id)
    conn = sqlite3.connect(store.path, check_same_thread=False, timeout=30)
    try:
        store.control(run_id, "continue")
        graph = build_graph(store, run_id, SqliteSaver(conn))
        config = {"configurable": {"thread_id": run_id}, "recursion_limit": 50}
        snapshot = graph.get_state(config)
        if snapshot.tasks and any(task.interrupts for task in snapshot.tasks):
            if resume_decision not in {"approve", "cancel"}:
                store.update(
                    run_id,
                    status="paused",
                    reason="Awaiting plan approval; resume with approve or cancel.",
                )
                graph_input = None
            else:
                graph_input = Command(resume=resume_decision)
        else:
            graph_input = (
                None
                if snapshot.values
                else {"run_id": run_id, "round": 0, "queries": [], "repeat": False}
            )
        result = (
            graph.invoke(graph_input, config) if store.get_run(run_id)["status"] != "paused" else {}
        )
        if result.get("__interrupt__"):
            store.update(
                run_id,
                status="paused",
                reason="Awaiting plan approval; inspect the plan, then resume --approve.",
            )
        elif store.get_run(run_id)["status"] == "running" and store.get(run_id, "outcome"):
            store.update(run_id, **store.get(run_id, "outcome"))
    except ControlRequested as exc:
        action = str(exc)
        store.update(run_id, status="paused" if action == "pause" else "halted", reason=action)
        store.event(run_id, "control", "stopped", {"action": action})
    except BudgetExceeded as exc:
        store.update(run_id, status="halted", reason=str(exc))
        store.event(run_id, "budget", "halted", {"reason": str(exc)})
    except KeyboardInterrupt:
        store.update(
            run_id,
            status="paused",
            reason="Interrupted at the active stage; resume reuses saved work.",
        )
    except Exception as exc:
        # API exception text may contain response bodies or credentials; persist only class/status.
        reason = f"{type(exc).__name__}" + (
            f" (HTTP {exc.status_code})" if hasattr(exc, "status_code") else ""
        )
        if (
            isinstance(exc, ValueError)
            and str(exc) == "OPENAI_API_KEY is required for live research"
        ):
            reason = str(exc)
        store.update(run_id, status="failed", reason=reason)
        store.event(
            run_id,
            "workflow",
            "error",
            {"type": type(exc).__name__, "status": getattr(exc, "status_code", None)},
        )
    finally:
        conn.close()
        store.release(run_id)
    if store.get_run(run_id)["status"] != "paused":
        save_report(store, run_id)
    return store.get_run(run_id)
