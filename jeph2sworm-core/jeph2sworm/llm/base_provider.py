"""Base LLM Provider - Abstract interface for all LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """A single message in a conversation."""

    role: str  # system, user, assistant
    content: str


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    usage: Dict[str, int] = Field(default_factory=dict)  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str = "stop"
    raw: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """
    Abstract base for all LLM providers.

    Each provider wraps a specific API (OpenAI, Anthropic, etc.)
    and normalizes responses into a common LLMResponse format.
    """

    provider_name: str = "base"

    # Model capabilities
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    max_context_window: int = 128_000

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self._configured = False

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """Send a completion request to the provider."""
        ...

    @abstractmethod
    def available_models(self) -> List[str]:
        """List available models for this provider."""
        ...

    @abstractmethod
    def best_model_for(self, task: str) -> str:
        """Return the best model for a given task type."""
        ...

    def configure(self, api_key: str, **kwargs) -> None:
        """Configure the provider with an API key."""
        self.api_key = api_key
        self._configured = True

    @property
    def is_configured(self) -> bool:
        return self._configured and bool(self.api_key)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars per token heuristic)."""
        return len(text) // 4

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} configured={self.is_configured}>"
