"""Pydantic contracts for research data and the Day 1 agent state."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchQuestion(BaseModel):
    """The bounded question submitted to a research run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=10, max_length=2_000)
    scope: str | None = Field(default=None, max_length=1_000)
    max_results: int = Field(default=5, ge=1, le=20)


class ResearchPlan(BaseModel):
    """A future structured output contract for the research planner."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=10)
    objective: str | None = Field(default=None, max_length=1_000)
    subquestions: list[str] = Field(default_factory=list, max_length=10)
    search_queries: list[str] = Field(default_factory=list, max_length=10)


class Paper(BaseModel):
    """Provider-neutral paper metadata used throughout the application."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    paper_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=1_000)
    authors: list[str] = Field(default_factory=list, max_length=100)
    year: int | None = Field(default=None, ge=1000, le=2100)
    abstract: str | None = Field(default=None, max_length=20_000)
    url: str | None = Field(default=None, max_length=2_000)
    doi: str | None = Field(default=None, max_length=300)
    source: Literal["mock", "arxiv", "openalex"] = "mock"


class ToolCall(BaseModel):
    """A normalized tool-call request emitted by the language model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    call_id: str = Field(min_length=1)
    name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecution(BaseModel):
    """An auditable record of one application-side tool execution."""

    model_config = ConfigDict(extra="forbid")

    tool_call_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    succeeded: bool
    result: Any | None = None
    error: str | None = None

    @model_validator(mode="after")
    def require_result_or_error(self) -> "ToolExecution":
        if self.succeeded and self.error is not None:
            raise ValueError("a successful tool execution cannot include an error")
        if not self.succeeded and not self.error:
            raise ValueError("a failed tool execution must include an error message")
        return self


class ConversationMessage(BaseModel):
    """A provider-neutral record that can be converted to Chat Completions input."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None

    @model_validator(mode="after")
    def validate_tool_message_shape(self) -> "ConversationMessage":
        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("tool messages must identify the tool call they answer")
        if self.role != "assistant" and self.tool_calls:
            raise ValueError("only assistant messages may contain tool calls")
        return self

    def to_openai_message(self) -> dict[str, Any]:
        """Serialize the normalized record into a Chat Completions message."""
        message: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.call_id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": __import__("json").dumps(call.arguments)},
                }
                for call in self.tool_calls
            ]
        if self.tool_call_id:
            message["tool_call_id"] = self.tool_call_id
        return message


class AgentStatus(StrEnum):
    """Lifecycle states for a bounded agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    HALTED = "halted"
    FAILED = "failed"


class AgentState(BaseModel):
    """The complete, inspectable state of a single Day 1 agent run."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    run_id: str = Field(default_factory=lambda: f"research-{uuid4().hex[:12]}")
    question: ResearchQuestion
    plan: ResearchPlan | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    tool_executions: list[ToolExecution] = Field(default_factory=list)
    retrieved_papers: list[Paper] = Field(default_factory=list)
    step_count: int = Field(default=0, ge=0)
    status: AgentStatus = AgentStatus.PENDING
    final_answer: str | None = None
    error: str | None = None

    def record_papers(self, papers: list[Paper]) -> None:
        """Append only papers not already represented by a provider-neutral identifier."""
        existing_ids = {paper.paper_id for paper in self.retrieved_papers}
        self.retrieved_papers.extend(paper for paper in papers if paper.paper_id not in existing_ids)
