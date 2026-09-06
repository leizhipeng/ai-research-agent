"""Command-line interface for the Day 1 research agent."""

from __future__ import annotations

import argparse
import json
from typing import Any

from research_agent.agents import ManualResearchAgent
from research_agent.config import Settings
from research_agent.llm import ChatModelClient, ModelResponse, OpenAICompatibleClient
from research_agent.models import ResearchQuestion, ToolCall
from research_agent.tools import build_default_registry


class OfflineDemoClient(ChatModelClient):
    """Deterministic teaching client that demonstrates one search-tool turn."""

    def __init__(self) -> None:
        self._turn = 0

    def complete(self, *, messages: list[Any], tools: list[dict[str, Any]]) -> ModelResponse:
        self._turn += 1
        if self._turn == 1:
            user_message = next(message for message in reversed(messages) if message.role == "user")
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        call_id="offline-search-1",
                        name="search_papers",
                        arguments={"query": user_message.content or "vision transformer", "max_results": 5},
                    )
                ]
            )
        tool_message = next(message for message in reversed(messages) if message.role == "tool")
        result = json.loads(tool_message.content or "{}")
        papers = result.get("result", [])
        titles = "; ".join(paper["title"] for paper in papers[:3])
        return ModelResponse(
            content=(
                "The mock catalog returned: "
                f"{titles}. This offline demonstration verifies the agent loop only; "
                "it is not a literature review or a live search result."
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Day 1 manual research-agent loop.")
    parser.add_argument("question", help="A research question to investigate.")
    parser.add_argument("--scope", help="Optional boundary for the question.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use a deterministic local model substitute and mock paper catalog; no API call is made.",
    )
    parser.add_argument("--show-state", action="store_true", help="Print the complete JSON-safe final state.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.from_environment()
    client: ChatModelClient
    if args.offline:
        client = OfflineDemoClient()
    else:
        client = OpenAICompatibleClient(settings)

    agent = ManualResearchAgent(client=client, tools=build_default_registry(), settings=settings)
    state = agent.run(ResearchQuestion(question=args.question, scope=args.scope, max_results=settings.max_search_results))

    print(f"Run ID: {state.run_id}")
    print(f"Status: {state.status}")
    print(f"Model steps: {state.step_count}")
    print(f"Tool executions: {len(state.tool_executions)}")
    print("\nFinal answer:\n")
    print(state.final_answer or state.error or "No final answer was produced.")
    if args.show_state:
        print("\nFinal state:\n")
        print(json.dumps(state.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
