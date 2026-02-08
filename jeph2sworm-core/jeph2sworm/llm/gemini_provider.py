"""Google Gemini Provider - Gemini 2.0 Flash, Gemini 1.5 Pro."""

from __future__ import annotations

from typing import List

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

TASK_BEST = {
    "coding": "gemini-2.0-flash",
    "planning": "gemini-1.5-pro",
    "reasoning": "gemini-1.5-pro",
    "design": "gemini-2.0-flash",
    "testing": "gemini-2.0-flash-lite",
    "general": "gemini-2.0-flash",
}


class GeminiProvider(BaseProvider):
    provider_name = "gemini"
    supports_function_calling = True
    supports_vision = True
    max_context_window = 1_000_000  # Gemini 1.5 Pro has 1M context

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "gemini-2.0-flash")

    async def complete(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        import litellm

        response = await litellm.acompletion(
            model=f"gemini/{model}" if not model.startswith("gemini/") else model,
            messages=[m.model_dump() for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            **kwargs,
        )

        choice = response.choices[0]
        usage = dict(response.usage) if response.usage else {}

        return LLMResponse(
            content=choice.message.content or "",
            model=model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
        )
