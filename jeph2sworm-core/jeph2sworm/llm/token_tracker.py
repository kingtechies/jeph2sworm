"""Token Tracker - Tracks LLM usage across agents and providers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class UsageRecord:
    """A single LLM usage record."""

    __slots__ = (
        "agent", "provider", "model", "prompt_tokens",
        "completion_tokens", "total_tokens", "timestamp", "task_type",
    )

    def __init__(
        self,
        agent: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str = "general",
    ):
        self.agent = agent
        self.provider = provider
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.timestamp = time.time()
        self.task_type = task_type

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp,
            "task_type": self.task_type,
        }


# Approximate cost per 1M tokens (input/output)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o1": {"input": 15.00, "output": 60.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "codestral-latest": {"input": 0.30, "output": 0.90},
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "grok-2": {"input": 2.00, "output": 10.00},
    "command-r-plus": {"input": 2.50, "output": 10.00},
    "command-r": {"input": 0.15, "output": 0.60},
}


class TokenTracker:
    """
    Tracks token usage and estimated costs across all agents and providers.

    Provides real-time usage stats, cost estimates, and budget warnings.
    """

    def __init__(self, persist_path: str = ".jeph2sworm/token_usage.json"):
        self.persist_path = Path(persist_path)
        self._records: List[UsageRecord] = []
        self._session_start = time.time()

        # Running totals for fast access
        self._totals_by_agent: Dict[str, int] = {}
        self._totals_by_provider: Dict[str, int] = {}
        self._totals_by_model: Dict[str, int] = {}

    def record(
        self,
        agent: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_type: str = "general",
    ) -> UsageRecord:
        """Record a new token usage event."""
        record = UsageRecord(
            agent=agent,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            task_type=task_type,
        )
        self._records.append(record)

        # Update running totals
        self._totals_by_agent[agent] = self._totals_by_agent.get(agent, 0) + record.total_tokens
        self._totals_by_provider[provider] = self._totals_by_provider.get(provider, 0) + record.total_tokens
        self._totals_by_model[model] = self._totals_by_model.get(model, 0) + record.total_tokens

        return record

    def get_total_tokens(self) -> int:
        """Total tokens used this session."""
        return sum(r.total_tokens for r in self._records)

    def get_estimated_cost(self) -> float:
        """Estimate total cost in USD."""
        total = 0.0
        for r in self._records:
            pricing = MODEL_PRICING.get(r.model, {"input": 1.0, "output": 3.0})
            total += (r.prompt_tokens / 1_000_000) * pricing["input"]
            total += (r.completion_tokens / 1_000_000) * pricing["output"]
        return round(total, 4)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        return {
            "session_duration_seconds": round(time.time() - self._session_start, 1),
            "total_requests": len(self._records),
            "total_tokens": self.get_total_tokens(),
            "estimated_cost_usd": self.get_estimated_cost(),
            "by_agent": dict(self._totals_by_agent),
            "by_provider": dict(self._totals_by_provider),
            "by_model": dict(self._totals_by_model),
        }

    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get usage stats for a specific agent."""
        records = [r for r in self._records if r.agent == agent]
        total = sum(r.total_tokens for r in records)

        cost = 0.0
        for r in records:
            pricing = MODEL_PRICING.get(r.model, {"input": 1.0, "output": 3.0})
            cost += (r.prompt_tokens / 1_000_000) * pricing["input"]
            cost += (r.completion_tokens / 1_000_000) * pricing["output"]

        return {
            "agent": agent,
            "requests": len(records),
            "total_tokens": total,
            "estimated_cost_usd": round(cost, 4),
        }

    def persist(self) -> None:
        """Save usage records to disk."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = [r.to_dict() for r in self._records]
            self.persist_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("token_tracker_persist_failed", error=str(e))

    def load(self) -> None:
        """Load previous usage records."""
        if self.persist_path.exists():
            try:
                data = json.loads(self.persist_path.read_text())
                for d in data:
                    record = UsageRecord(
                        agent=d["agent"],
                        provider=d["provider"],
                        model=d["model"],
                        prompt_tokens=d["prompt_tokens"],
                        completion_tokens=d["completion_tokens"],
                        task_type=d.get("task_type", "general"),
                    )
                    record.timestamp = d.get("timestamp", time.time())
                    self._records.append(record)
            except Exception as e:
                logger.error("token_tracker_load_failed", error=str(e))


# Global singleton
token_tracker = TokenTracker()
