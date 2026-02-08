"""Together AI / Llama Provider - Llama 3.1 405B, 70B, 8B."""

from __future__ import annotations

from typing import List

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
]

TASK_BEST = {
    "coding": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "planning": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "reasoning": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "design": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "testing": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "general": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
}


class LlamaProvider(BaseProvider):
    provider_name = "together_ai"
    supports_function_calling = True
    supports_vision = True  # Llama 3.2 Vision
    max_context_window = 128_000

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")

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
            model=f"together_ai/{model}" if not model.startswith("together_ai/") else model,
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
