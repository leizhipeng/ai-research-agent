"""Contract tests for research-state model invariants."""

import pytest
from pydantic import ValidationError

from research_agent.models import ConversationMessage, ToolExecution


def test_tool_message_requires_a_call_identifier() -> None:
    with pytest.raises(ValidationError, match="identify the tool call"):
        ConversationMessage(role="tool", content="{}")


def test_failed_tool_execution_requires_an_error_message() -> None:
    with pytest.raises(ValidationError, match="must include an error"):
        ToolExecution(tool_call_id="call-1", tool_name="search_papers", succeeded=False)


def test_successful_tool_execution_cannot_include_an_error() -> None:
    with pytest.raises(ValidationError, match="cannot include an error"):
        ToolExecution(
            tool_call_id="call-1",
            tool_name="search_papers",
            succeeded=True,
            result=[],
            error="unexpected",
        )
