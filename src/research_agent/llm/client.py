"""Minimal adapter around the OpenAI-compatible Chat Completions API."""

from __future__ import annotations

import json
from typing import Any, Protocol

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from research_agent.config import Settings
from research_agent.models import ConversationMessage, ToolCall


class ModelResponse(BaseModel):
    """The subset of a model response required by the framework-free loop."""

    model_config = ConfigDict(extra="forbid")

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)


class ChatModelClient(Protocol):
    """Port that permits a live LLM client or a deterministic test double."""

    def complete(
        self,
        *,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        """Request one assistant turn from the model."""


class OpenAICompatibleClient:
    """Chat Completions adapter with explicit configuration and response normalization."""

    def __init__(self, settings: Settings) -> None:
        if not settings.is_llm_configured:
            raise ValueError("OPENAI_API_KEY is required to use the live model client")
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.api_key.get_secret_value() if settings.api_key else None,
            base_url=settings.api_base_url,
            timeout=settings.request_timeout_seconds,
        )

    def complete(
        self,
        *,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        response = self._client.chat.completions.create(
            model=self._settings.model_name,
            messages=[message.to_openai_message() for message in messages],
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        calls: list[ToolCall] = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError as exc:
                raise ValueError(f"model returned invalid JSON arguments for {call.function.name}") from exc
            calls.append(ToolCall(call_id=call.id, name=call.function.name, arguments=arguments))
        return ModelResponse(content=message.content, tool_calls=calls)
