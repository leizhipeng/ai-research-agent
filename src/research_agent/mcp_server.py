"""Local stdio MCP tools backed by the same workflow and SQLite store as the CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from research_agent.models.workflow import Limits, ResearchRequest, Source
from research_agent.storage import Store
from research_agent.workflow import run_research as execute_research


def create_server(db: str) -> FastMCP:
    server = FastMCP(
        "Research Agent",
        instructions="Research tools retain sources and evidence in a local database. Offline research uses labeled synthetic data.",
    )
    store = Store(db)

    @server.tool()
    async def run_research(
        question: str,
        scope: str = "",
        search_queries: list[str] | None = None,
        offline: bool = True,
        limits: Limits | None = None,
        providers: list[Literal["arxiv", "openalex"]] | None = None,
        pause_after_plan: bool = False,
        full_text: bool = False,
    ) -> dict[str, Any]:
        """Run the bounded research workflow and return its saved run record. Live mode requires model credentials."""
        request = ResearchRequest(
            question=question,
            scope=scope,
            search_queries=search_queries or [],
            mode="offline" if offline else "live",
            limits=limits or Limits(),
            providers=providers or ["arxiv", "openalex"],
            pause_after_plan=pause_after_plan,
            full_text=full_text,
        )
        return await asyncio.to_thread(execute_research, request, db)

    @server.tool()
    def inspect_research(run_id: str | None = None) -> dict[str, Any]:
        """Inspect one run's retained artifacts and events, or list all local runs."""
        return store.inspect(run_id) if run_id else {"runs": store.list_runs()}

    @server.tool()
    async def resume_research(run_id: str, approve: bool = False) -> dict[str, Any]:
        """Continue an existing checkpoint; approve explicitly accepts a plan awaiting approval."""
        saved = store.get_run(run_id)
        request = ResearchRequest.model_validate(saved["request"])
        return await asyncio.to_thread(
            execute_research,
            request,
            db,
            run_id=run_id,
            resume_decision="approve" if approve else None,
        )

    @server.tool()
    def pause_research(run_id: str) -> dict[str, Any]:
        """Request a pause at the next workflow boundary, retaining completed work."""
        return store.control(run_id, "pause")

    @server.tool()
    def cancel_research(run_id: str) -> dict[str, Any]:
        """Request cancellation at the next workflow boundary, retaining existing artifacts."""
        return store.control(run_id, "cancel")

    @server.tool()
    def export_research(run_id: str, directory: str) -> dict[str, Any]:
        """Export a saved run's Markdown report and structured artifacts to a local directory."""
        return store.export(run_id, directory)

    @server.tool()
    async def search_literature(
        query: str,
        provider: Literal["arxiv", "openalex"] = "arxiv",
        max_results: int = 4,
    ) -> dict[str, Any]:
        """Retrieve normalized scholarly records directly from one provider without an LLM."""
        from research_agent.discovery import search_papers

        sources = await asyncio.to_thread(
            search_papers,
            query,
            provider,
            max_results,
            openalex_api_key=os.getenv("OPENALEX_API_KEY"),
            cache_get=store.cache_get,
            cache_set=store.cache_set,
        )
        return {"sources": [source.model_dump(mode="json") for source in sources]}

    @server.tool()
    async def read_source(source: Source) -> dict[str, Any]:
        """Read legitimately accessible source content; its returned content_level records the actual depth."""
        from research_agent.discovery import read_source as retrieve_source

        result = await asyncio.to_thread(
            retrieve_source,
            source,
            openalex_api_key=os.getenv("OPENALEX_API_KEY"),
            cache_get=store.cache_get,
            cache_set=store.cache_set,
        )
        return result.model_dump(mode="json")

    return server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expose the local research workflow over MCP stdio."
    )
    parser.add_argument("--db", default=os.getenv("RESEARCH_AGENT_DB", "data/research.sqlite"))
    args = parser.parse_args()
    create_server(args.db).run(transport="stdio")


if __name__ == "__main__":
    main()
