"""LLM Router - intelligent multi-provider routing for the agent swarm."""

from __future__ import annotations

import time
from typing import Any, Optional

import structlog
from litellm import acompletion
import litellm

logger = structlog.get_logger()

# Suppress litellm verbose logging
litellm.suppress_debug_info = True


# Provider configurations with model mappings
PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4.1", "o3", "gpt-4o-mini"],
    "anthropic": ["claude-opus-4-20250514", "claude-sonnet-4-20250514"],
    "xai": ["xai/grok-3"],
    "google": ["gemini/gemini-2.0-flash", "gemini/gemini-2.5-pro"],
    "deepseek": ["deepseek/deepseek-chat", "deepseek/deepseek-reasoner"],
    "mistral": ["mistral/mistral-large-latest", "mistral/codestral-latest"],
    "together": ["together_ai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"],
    "cohere": ["cohere/command-r-plus"],
}

# Task-type to model preference mapping
TASK_MODEL_PREFERENCE: dict[str, list[str]] = {
    "coding": ["claude-opus-4-20250514", "gpt-4.1", "deepseek/deepseek-chat"],
    "planning": ["o3", "claude-opus-4-20250514", "gpt-4o"],
    "design": ["gpt-4o", "gemini/gemini-2.5-pro", "claude-sonnet-4-20250514"],
    "testing": ["gpt-4o", "claude-sonnet-4-20250514", "deepseek/deepseek-chat"],
    "devops": ["gpt-4o", "claude-sonnet-4-20250514"],
    "quick": ["gpt-4o-mini", "deepseek/deepseek-chat"],
    "general": ["gpt-4o", "claude-sonnet-4-20250514"],
}


class TokenUsage:
    """Track token usage per agent, per provider."""

    def __init__(self) -> None:
        self.total_input: int = 0
        self.total_output: int = 0
        self.per_agent: dict[str, dict[str, int]] = {}
        self.per_provider: dict[str, dict[str, int]] = {}
        self.call_count: int = 0

    def record(
        self,
        agent_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self.total_input += input_tokens
        self.total_output += output_tokens
        self.call_count += 1

        if agent_id not in self.per_agent:
            self.per_agent[agent_id] = {"input": 0, "output": 0, "calls": 0}
        self.per_agent[agent_id]["input"] += input_tokens
        self.per_agent[agent_id]["output"] += output_tokens
        self.per_agent[agent_id]["calls"] += 1

        if provider not in self.per_provider:
            self.per_provider[provider] = {"input": 0, "output": 0, "calls": 0}
        self.per_provider[provider]["input"] += input_tokens
        self.per_provider[provider]["output"] += output_tokens
        self.per_provider[provider]["calls"] += 1

    def summary(self) -> dict:
        return {
            "total_input_tokens": self.total_input,
            "total_output_tokens": self.total_output,
            "total_calls": self.call_count,
            "per_agent": self.per_agent,
            "per_provider": self.per_provider,
        }


class LLMRouter:
    """
    Routes LLM requests to the best available provider/model.

    Supports multiple API keys, task-based model selection,
    automatic fallback, and token tracking.
    """

    def __init__(self) -> None:
        self.api_keys: dict[str, str] = {}  # provider -> api_key
        self.default_provider: str = "openai"
        self.default_model: str = "gpt-4o"
        self.token_usage = TokenUsage()
        self._available_models: list[str] = []

    def configure_provider(self, provider: str, api_key: str) -> None:
        """Register an API key for a provider."""
        self.api_keys[provider] = api_key

        # Set the environment variable that litellm expects
        import os
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "xai": "XAI_API_KEY",
            "google": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "together": "TOGETHER_API_KEY",
            "cohere": "COHERE_API_KEY",
        }
        if provider in env_key_map:
            os.environ[env_key_map[provider]] = api_key

        # Update available models
        self._available_models = []
        for prov, models in PROVIDER_MODELS.items():
            if prov in self.api_keys:
                self._available_models.extend(models)

        logger.info("llm_provider_configured", provider=provider)

    def get_available_providers(self) -> list[str]:
        """Return list of configured providers."""
        return list(self.api_keys.keys())

    def select_model(
        self,
        task_type: str = "general",
        preferred_model: Optional[str] = None,
    ) -> str:
        """Select the best model for a given task type."""
        if preferred_model and preferred_model in self._available_models:
            return preferred_model

        preferences = TASK_MODEL_PREFERENCE.get(task_type, TASK_MODEL_PREFERENCE["general"])
        for model in preferences:
            if model in self._available_models:
                return model

        # Fallback to default
        if self._available_models:
            return self._available_models[0]

        return self.default_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        agent_id: str = "system",
        task_type: str = "general",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        tools: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """
        Send a completion request to the best available LLM.

        Returns:
            {
                "content": str,
                "model": str,
                "input_tokens": int,
                "output_tokens": int,
                "tool_calls": list | None,
            }
        """
        selected_model = model or self.select_model(task_type)
        errors: list[str] = []

        # Try the selected model, then fallbacks
        models_to_try = [selected_model]
        fallbacks = [m for m in self._available_models if m != selected_model]
        models_to_try.extend(fallbacks[:2])  # max 2 fallbacks

        for try_model in models_to_try:
            try:
                start = time.time()

                kwargs: dict[str, Any] = {
                    "model": try_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                if tools:
                    kwargs["tools"] = tools

                response = await acompletion(**kwargs)
                elapsed = time.time() - start

                # Extract usage
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0

                self.token_usage.record(agent_id, try_model, input_tokens, output_tokens)

                choice = response.choices[0]
                content = choice.message.content or ""
                tool_calls = None
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in choice.message.tool_calls
                    ]

                await logger.ainfo(
                    "llm_completion",
                    model=try_model,
                    agent=agent_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    elapsed_ms=int(elapsed * 1000),
                )

                return {
                    "content": content,
                    "model": try_model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "tool_calls": tool_calls,
                }

            except Exception as e:
                error_msg = f"{try_model}: {str(e)}"
                errors.append(error_msg)
                await logger.awarning(
                    "llm_completion_failed",
                    model=try_model,
                    error=str(e),
                )
                continue

        # All models failed
        raise RuntimeError(
            f"All LLM providers failed. Errors: {'; '.join(errors)}"
        )

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        agent_id: str = "system",
        task_type: str = "general",
        **kwargs: Any,
    ) -> str:
        """Simplified chat interface. Returns just the content string."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        result = await self.complete(
            messages=messages,
            agent_id=agent_id,
            task_type=task_type,
            **kwargs,
        )
        return result["content"]

    def get_usage_summary(self) -> dict:
        """Get token usage summary."""
        return self.token_usage.summary()
