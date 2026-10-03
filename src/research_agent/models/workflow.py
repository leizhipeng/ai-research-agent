"""Provider-independent contracts for the saved research workflow."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Limits(Contract):
    max_rounds: int = Field(default=2, ge=1, le=5)
    max_papers: int = Field(default=6, ge=1, le=20)
    results_per_query: int = Field(default=4, ge=1, le=20)
    max_queries: int = Field(default=3, ge=1, le=8)
    max_model_calls: int = Field(default=24, ge=0, le=100)
    max_tokens: int = Field(default=100_000, ge=0, le=500_000)
    max_seconds: float = Field(default=300, gt=0, le=7200)
    max_http_requests: int = Field(default=30, ge=0, le=200)
    max_download_bytes: int = Field(default=12_000_000, ge=0, le=100_000_000)
    concurrency: int = Field(default=2, ge=1, le=4)


class ResearchRequest(Contract):
    question: str = Field(min_length=10, max_length=2000)
    scope: str = Field(default="", max_length=1000)
    mode: Literal["offline", "live"] = "live"
    limits: Limits = Field(default_factory=Limits)
    pause_after_plan: bool = False
    full_text: bool = False
    search_queries: list[str] = Field(default_factory=list, max_length=8)
    providers: list[Literal["arxiv", "openalex"]] = Field(
        default_factory=lambda: ["arxiv", "openalex"], min_length=1
    )

    @field_validator("providers")
    @classmethod
    def unique_providers(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @field_validator("search_queries")
    @classmethod
    def valid_queries(cls, value: list[str]) -> list[str]:
        if any(not 3 <= len(item.strip()) <= 500 for item in value):
            raise ValueError("search queries must contain 3 to 500 characters")
        return list(dict.fromkeys(item.strip() for item in value))


class Plan(Contract):
    objective: str = Field(min_length=1, max_length=1500)
    subquestions: list[str] = Field(min_length=1, max_length=8)
    search_queries: list[str] = Field(min_length=1, max_length=8)
    scope_notes: str

    @field_validator("subquestions", "search_queries")
    @classmethod
    def bounded_text(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 500 for item in value):
            raise ValueError("items must contain 1 to 500 characters")
        return list(dict.fromkeys(item.strip() for item in value))


class Retrieval(Contract):
    provider: str
    query: str
    url: str
    retrieved_at: str
    cache_hit: bool = False


class Source(Contract):
    source_id: str
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    url: str
    abstract: str | None = None
    providers: list[str] = Field(default_factory=list)
    retrievals: list[Retrieval] = Field(default_factory=list)
    content_level: Literal["metadata", "abstract", "full_text"] = "metadata"
    content: str = ""
    content_url: str = ""
    citations: int | None = None
    access_note: str = ""
    score: float = 0
    selection_reasons: list[str] = Field(default_factory=list)


class EvidenceDraft(Contract):
    claim: str = Field(min_length=1, max_length=1500)
    quote: str = Field(min_length=1, max_length=1500)
    subquestion: int = Field(ge=0)


class Analysis(Contract):
    problem: str
    method: str
    datasets: list[str]
    metrics: list[str]
    limitations: list[str]
    evidence: list[EvidenceDraft] = Field(max_length=5)


class SupportDecision(Contract):
    supported: bool
    reason: str


class Evidence(Contract):
    evidence_id: str
    source_id: str
    claim: str
    quote: str
    start: int
    end: int
    content_level: Literal["abstract", "full_text"]
    subquestion: int
    supported: bool
    support_reason: str


class Comparison(Contract):
    evidence_ids: list[str] = Field(min_length=2, max_length=6)
    relation: Literal["agreement", "contradiction", "different_setup", "uncertain"]
    explanation: str


class Review(Contract):
    covered_subquestions: list[int]
    gaps: list[str]
    followup_queries: list[str] = Field(max_length=8)
    comparisons: list[Comparison] = Field(max_length=10)
    sufficient: bool
    stop_reason: str
