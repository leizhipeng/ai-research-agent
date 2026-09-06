"""A deterministic paper-search tool for learning the agent loop.

The tool deliberately uses local mock records on Day 1. Its public input/output
contract is designed to remain stable when an arXiv adapter replaces it on Day 2.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from research_agent.models import Paper, ToolCall, ToolExecution


class SearchPapersArguments(BaseModel):
    """Validated inputs accepted by the paper-search function."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)


class PaperSearchTool:
    """Read-only local search over a tiny, deterministic paper catalog."""

    name = "search_papers"
    description = "Search mock academic paper metadata by research keywords."

    _catalog = [
        Paper(
            paper_id="mock-vit-compression-2024",
            title="Compression Strategies for Vision Transformer Inference",
            authors=["A. Researcher", "B. Engineer"],
            year=2024,
            abstract="A comparison of quantization, pruning, and distillation for vision transformer deployment.",
            url="https://example.org/mock-vit-compression-2024",
        ),
        Paper(
            paper_id="mock-edge-gpu-2025",
            title="Efficient Vision Transformers on Edge GPUs",
            authors=["C. Systems", "D. Vision"],
            year=2025,
            abstract="An evaluation of operator fusion and mixed precision on resource-constrained GPU devices.",
            url="https://example.org/mock-edge-gpu-2025",
        ),
        Paper(
            paper_id="mock-int8-calibration-2023",
            title="Calibration-Aware INT8 Quantization for Visual Transformers",
            authors=["E. Quantization"],
            year=2023,
            abstract="Post-training quantization can preserve accuracy when calibration data represents deployment inputs.",
            url="https://example.org/mock-int8-calibration-2023",
        ),
        Paper(
            paper_id="mock-small-object-2024",
            title="Multi-Scale Features for Small-Object Detection",
            authors=["F. Detection"],
            year=2024,
            abstract="Feature pyramids and high-resolution representations improve small-object detection recall.",
            url="https://example.org/mock-small-object-2024",
        ),
    ]

    @classmethod
    def schema(cls) -> dict[str, Any]:
        """Return the strict OpenAI function-tool declaration."""
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": SearchPapersArguments.model_json_schema(),
                "strict": True,
            },
        }

    @classmethod
    def execute(cls, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Return records with token overlap, preserving deterministic test behavior."""
        request = SearchPapersArguments.model_validate(arguments)
        terms = set(request.query.lower().split())

        def score(paper: Paper) -> int:
            haystack = f"{paper.title} {paper.abstract or ''}".lower()
            return sum(term in haystack for term in terms)

        ranked = sorted(cls._catalog, key=lambda paper: (score(paper), paper.year or 0), reverse=True)
        matched = [paper for paper in ranked if score(paper) > 0]
        selected = (matched or ranked)[: request.max_results]
        return [paper.model_dump(mode="json") for paper in selected]


ToolHandler = Callable[[dict[str, Any]], Any]


class ToolRegistry:
    """A small, explicit registry that separates tool schemas from dispatch."""

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, *, name: str, schema: dict[str, Any], handler: ToolHandler) -> None:
        if name in self._handlers:
            raise ValueError(f"tool already registered: {name}")
        self._schemas[name] = schema
        self._handlers[name] = handler

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return list(self._schemas.values())

    def execute(self, call: ToolCall) -> ToolExecution:
        handler = self._handlers.get(call.name)
        if handler is None:
            return ToolExecution(
                tool_call_id=call.call_id,
                tool_name=call.name,
                succeeded=False,
                error=f"unknown tool: {call.name}",
            )
        try:
            return ToolExecution(
                tool_call_id=call.call_id,
                tool_name=call.name,
                succeeded=True,
                result=handler(call.arguments),
            )
        except Exception as exc:  # Tool errors belong in the model's observation, not a crashed loop.
            return ToolExecution(
                tool_call_id=call.call_id,
                tool_name=call.name,
                succeeded=False,
                error=f"{type(exc).__name__}: {exc}",
            )


def build_default_registry() -> ToolRegistry:
    """Build the Day 1 read-only tool set."""
    registry = ToolRegistry()
    registry.register(name=PaperSearchTool.name, schema=PaperSearchTool.schema(), handler=PaperSearchTool.execute)
    return registry
