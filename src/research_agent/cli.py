"""Command-line access to the persistent research workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from research_agent.models.workflow import Limits, ResearchRequest
from research_agent.storage import Store
from research_agent.workflow import run_research


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research a question and retain its evidence trail."
    )
    parser.add_argument(
        "--db",
        default=os.getenv("RESEARCH_AGENT_DB", "data/research.sqlite"),
        help="SQLite database path.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser(
        "run",
        help="Plan, discover sources, analyze evidence, review, and save a report.",
    )
    run.add_argument("question")
    run.add_argument("--scope", default="")
    run.add_argument(
        "--query",
        action="append",
        default=[],
        help="Use a specific initial query; repeat for several.",
    )
    run.add_argument(
        "--offline",
        action="store_true",
        help="Use labeled synthetic sources and deterministic model substitutes.",
    )
    run.add_argument(
        "--pause-after-plan",
        action="store_true",
        help="Require explicit approval before discovery.",
    )
    run.add_argument(
        "--full-text",
        action="store_true",
        help="Read legitimately accessible full text where available.",
    )
    run.add_argument("--provider", action="append", choices=["arxiv", "openalex"], dest="providers")
    for field, default in Limits().model_dump().items():
        run.add_argument(
            f"--{field.replace('_', '-')}",
            type=Limits.model_fields[field].annotation,
            default=default,
        )

    inspect = commands.add_parser(
        "inspect", help="List runs, or inspect one run with artifacts and events."
    )
    inspect.add_argument("run_id", nargs="?")
    resume = commands.add_parser("resume", help="Continue saved work from its latest checkpoint.")
    resume.add_argument("run_id")
    resume.add_argument(
        "--approve",
        action="store_true",
        help="Approve a saved plan awaiting permission to continue.",
    )
    for command in ("pause", "cancel"):
        control = commands.add_parser(
            command, help=f"Request {command} at the next workflow boundary."
        )
        control.add_argument("run_id")
    export = commands.add_parser(
        "export", help="Write Markdown and structured artifacts for a saved run."
    )
    export.add_argument("run_id")
    export.add_argument("--output", type=Path, required=True)
    search = commands.add_parser(
        "search", help="Retrieve scholarly records directly without an LLM."
    )
    search.add_argument("query")
    search.add_argument("--provider", choices=["arxiv", "openalex"], default="arxiv")
    search.add_argument("--max-results", type=int, default=4)

    # Accept the storage option before or after the command without overwriting it.
    for command in commands.choices.values():
        command.add_argument("--db", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        store = Store(args.db)
        if args.command == "run":
            request = ResearchRequest(
                question=args.question,
                scope=args.scope,
                search_queries=args.query,
                mode="offline" if args.offline else "live",
                providers=args.providers or ["arxiv", "openalex"],
                limits=Limits(**{field: getattr(args, field) for field in Limits.model_fields}),
                pause_after_plan=args.pause_after_plan,
                full_text=args.full_text,
            )
            result = run_research(request, args.db)
        elif args.command == "inspect":
            result = store.inspect(args.run_id) if args.run_id else store.list_runs()
        elif args.command == "resume":
            saved = store.get_run(args.run_id)
            request = ResearchRequest.model_validate(saved["request"])
            result = run_research(
                request,
                args.db,
                run_id=args.run_id,
                resume_decision="approve" if args.approve else None,
            )
        elif args.command in {"pause", "cancel"}:
            result = store.control(args.run_id, args.command)
        elif args.command == "export":
            result = store.export(args.run_id, args.output)
        else:
            from research_agent.discovery import search_papers

            sources = search_papers(
                args.query,
                args.provider,
                args.max_results,
                openalex_api_key=os.getenv("OPENALEX_API_KEY"),
                cache_get=store.cache_get,
                cache_set=store.cache_set,
            )
            result = [source.model_dump(mode="json") for source in sources]
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        if args.command in {"run", "resume"} and result.get("status") == "failed":
            raise SystemExit(1)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"research-agent: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        print(
            "Interrupted. Inspect the saved run and use resume to continue its checkpoint.",
            file=sys.stderr,
        )
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
