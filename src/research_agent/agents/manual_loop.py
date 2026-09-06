"""A framework-free, bounded tool-calling loop for the research assistant."""

from __future__ import annotations

import json

from research_agent.config import Settings
from research_agent.llm import ChatModelClient
from research_agent.models import (
    AgentState,
    AgentStatus,
    ConversationMessage,
    Paper,
    ResearchQuestion,
)
from research_agent.tools import ToolRegistry

SYSTEM_INSTRUCTIONS = """You are a scientific literature research assistant.
Use the search_papers tool before making factual claims about research literature.
Formulate a concise academic search query from the user's question. Base the final
answer only on papers returned by tools. Name the papers you rely on and clearly
state that Day 1 uses a local mock catalog rather than live literature sources."""


class ManualResearchAgent:
    """Coordinates one LLM, explicit tools, and a typed research-run state."""

    def __init__(self, *, client: ChatModelClient, tools: ToolRegistry, settings: Settings) -> None:
        self._client = client
        self._tools = tools
        self._settings = settings

    def run(self, question: ResearchQuestion) -> AgentState:
        """Run until the model answers, an error occurs, or the step bound is reached."""
        state = AgentState(question=question, status=AgentStatus.RUNNING)
        state.messages.extend(
            [
                ConversationMessage(role="system", content=SYSTEM_INSTRUCTIONS),
                ConversationMessage(role="user", content=self._user_prompt(question)),
            ]
        )

        try:
            for _ in range(self._settings.max_steps):
                state.step_count += 1
                model_response = self._client.complete(messages=state.messages, tools=self._tools.schemas)
                assistant_message = ConversationMessage(
                    role="assistant",
                    content=model_response.content,
                    tool_calls=model_response.tool_calls,
                )
                state.messages.append(assistant_message)

                if not model_response.tool_calls:
                    state.final_answer = model_response.content or "The model returned no final answer."
                    state.status = AgentStatus.COMPLETED
                    return state

                for tool_call in model_response.tool_calls:
                    execution = self._tools.execute(tool_call)
                    state.tool_executions.append(execution)
                    if execution.succeeded and tool_call.name == "search_papers":
                        papers = [Paper.model_validate(item) for item in execution.result]
                        state.record_papers(papers)
                    state.messages.append(
                        ConversationMessage(
                            role="tool",
                            tool_call_id=tool_call.call_id,
                            content=json.dumps(
                                {
                                    "ok": execution.succeeded,
                                    "result": execution.result,
                                    "error": execution.error,
                                },
                                ensure_ascii=False,
                            ),
                        )
                    )

            state.status = AgentStatus.HALTED
            state.error = f"Stopped after the configured limit of {self._settings.max_steps} model steps."
            return state
        except Exception as exc:
            state.status = AgentStatus.FAILED
            state.error = f"{type(exc).__name__}: {exc}"
            return state

    @staticmethod
    def _user_prompt(question: ResearchQuestion) -> str:
        scope = f"\nScope: {question.scope}" if question.scope else ""
        return f"Research question: {question.question}{scope}\nReturn at most {question.max_results} papers."
