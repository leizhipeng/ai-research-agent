"""Deterministic tests for the Day 1 manual tool-calling loop."""

from typing import Any

from research_agent.agents import ManualResearchAgent
from research_agent.config import Settings
from research_agent.llm import ChatModelClient, ModelResponse
from research_agent.models import AgentStatus, ResearchQuestion, ToolCall
from research_agent.tools import build_default_registry


class ScriptedClient(ChatModelClient):
    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = responses
        self.calls = 0

    def complete(self, *, messages: list[Any], tools: list[dict[str, Any]]) -> ModelResponse:
        response = self._responses[self.calls]
        self.calls += 1
        return response


def test_loop_executes_tool_and_records_papers() -> None:
    client = ScriptedClient(
        [
            ModelResponse(
                tool_calls=[
                    ToolCall(
                        call_id="call-search",
                        name="search_papers",
                        arguments={"query": "vision transformer edge GPU", "max_results": 2},
                    )
                ]
            ),
            ModelResponse(content="The retrieved papers support testing compression and mixed precision."),
        ]
    )
    agent = ManualResearchAgent(
        client=client,
        tools=build_default_registry(),
        settings=Settings(max_steps=3),
    )

    state = agent.run(ResearchQuestion(question="What methods accelerate vision transformers on edge GPUs?"))

    assert state.status is AgentStatus.COMPLETED
    assert state.step_count == 2
    assert len(state.tool_executions) == 1
    assert state.tool_executions[0].succeeded is True
    assert len(state.retrieved_papers) == 2
    assert state.final_answer == "The retrieved papers support testing compression and mixed precision."


def test_loop_halts_at_the_configured_step_limit() -> None:
    repeated_tool_call = ModelResponse(
        tool_calls=[
            ToolCall(
                call_id="call-search",
                name="search_papers",
                arguments={"query": "vision transformer", "max_results": 1},
            )
        ]
    )
    client = ScriptedClient([repeated_tool_call, repeated_tool_call])
    agent = ManualResearchAgent(
        client=client,
        tools=build_default_registry(),
        settings=Settings(max_steps=2),
    )

    state = agent.run(ResearchQuestion(question="What techniques reduce Vision Transformer inference latency?"))

    assert state.status is AgentStatus.HALTED
    assert state.step_count == 2
    assert "limit" in (state.error or "")
