"""Discover and invoke the local MCP tools, then inspect an offline evidence trail."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demonstrate(db: Path, question: str) -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "research_agent.mcp_server", "--db", str(db.resolve())],
        env={},
    )
    async with (
        stdio_client(parameters) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        print("Discovered tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
        research_tool = next(tool for tool in tools.tools if tool.name == "run_research")
        print("\nDiscovered run_research input schema:")
        print(json.dumps(research_tool.inputSchema, indent=2, ensure_ascii=False))
        result = await session.call_tool(
            "run_research", {"question": question, "offline": True}
        )
        if result.isError:
            print(result.model_dump_json(indent=2))
            raise SystemExit(1)
        run = result.structuredContent
        if run is None:
            raise RuntimeError("The server did not return a structured run record.")
        print("\nSaved offline run:")
        print(json.dumps(run, indent=2, ensure_ascii=False))
        inspection = await session.call_tool(
            "inspect_research", {"run_id": run["run_id"]}
        )
        if inspection.isError:
            print(inspection.model_dump_json(indent=2))
            raise SystemExit(1)
        print("\nRetained artifacts and evidence:")
        print(json.dumps(inspection.structuredContent, indent=2, ensure_ascii=False))
        if run.get("status") == "failed":
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/mcp-demo.sqlite"))
    parser.add_argument(
        "--question",
        default="How do quantization and pruning affect vision transformer inference on edge GPUs?",
    )
    args = parser.parse_args()
    asyncio.run(demonstrate(args.db, args.question))


if __name__ == "__main__":
    main()
