"""Runtime configuration for the research agent."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Settings(BaseModel):
    """Settings read explicitly from environment variables.

    The application accepts either ``OPENAI_API_BASE`` (the Manus-compatible
    convention) or ``OPENAI_BASE_URL`` (the OpenAI SDK convention).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_name: str = Field(default="gpt-5-mini", min_length=1)
    api_key: SecretStr | None = None
    api_base_url: str | None = None
    max_steps: int = Field(default=5, ge=1, le=20)
    max_search_results: int = Field(default=5, ge=1, le=20)
    request_timeout_seconds: float = Field(default=45.0, gt=0, le=300)
    openalex_api_key: SecretStr | None = None
    json_mode: bool = False
    max_output_tokens: int = Field(default=2400, ge=200, le=8000)

    @classmethod
    def from_environment(cls) -> "Settings":
        """Create settings from conventional, platform-neutral environment variables."""
        return cls(
            model_name=os.getenv("RESEARCH_AGENT_MODEL", "gpt-5-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base_url=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL"),
            max_steps=int(os.getenv("RESEARCH_AGENT_MAX_STEPS", "5")),
            max_search_results=int(os.getenv("RESEARCH_AGENT_MAX_SEARCH_RESULTS", "5")),
            request_timeout_seconds=float(os.getenv("RESEARCH_AGENT_TIMEOUT_SECONDS", "45")),
            openalex_api_key=os.getenv("OPENALEX_API_KEY"),
            json_mode=os.getenv("RESEARCH_AGENT_JSON_MODE", "false").lower() == "true",
            max_output_tokens=int(os.getenv("RESEARCH_AGENT_MAX_OUTPUT_TOKENS", "2400")),
        )

    @property
    def is_llm_configured(self) -> bool:
        """Return whether an API key is available without exposing the secret."""
        return self.api_key is not None and self.api_key.get_secret_value() not in {
            "",
            "replace-with-your-api-key",
        }
