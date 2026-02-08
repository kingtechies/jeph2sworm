"""Tests for LLM module - router, token_tracker, context_optimizer, providers."""

import pytest

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse
from jeph2sworm.llm.token_tracker import TokenTracker, UsageRecord
from jeph2sworm.llm.context_optimizer import ContextOptimizer


class TestTokenTracker:
    """Tests for token usage tracking."""

    @pytest.fixture
    def tracker(self):
        return TokenTracker()

    def test_record_usage(self, tracker):
        record = tracker.record("backend", "openai", "gpt-4o", 100, 50)
        assert record.total_tokens == 150
        assert record.agent == "backend"

    def test_total_tokens(self, tracker):
        tracker.record("backend", "openai", "gpt-4o", 100, 50)
        tracker.record("frontend", "anthropic", "claude-sonnet-4-20250514", 200, 100)
        assert tracker.get_total_tokens() == 450

    def test_estimated_cost(self, tracker):
        tracker.record("backend", "openai", "gpt-4o", 1_000_000, 0)
        cost = tracker.get_estimated_cost()
        assert cost > 0

    def test_agent_stats(self, tracker):
        tracker.record("backend", "openai", "gpt-4o", 100, 50)
        tracker.record("backend", "openai", "gpt-4o", 200, 100)
        stats = tracker.get_agent_stats("backend")
        assert stats["requests"] == 2
        assert stats["total_tokens"] == 450

    def test_stats_overview(self, tracker):
        tracker.record("backend", "openai", "gpt-4o", 100, 50)
        stats = tracker.get_stats()
        assert stats["total_requests"] == 1
        assert "by_agent" in stats
        assert "by_provider" in stats


class TestContextOptimizer:
    """Tests for context compression."""

    @pytest.fixture
    def optimizer(self):
        return ContextOptimizer(max_tokens=1000)

    def test_no_optimization_needed(self, optimizer):
        messages = [{"role": "user", "content": "Hello"}]
        result = optimizer.optimize(messages, max_tokens=1000)
        assert len(result) == 1

    def test_truncation(self, optimizer):
        # Create many messages that exceed limit
        messages = [
            {"role": "user", "content": f"Message {i} " * 50}
            for i in range(50)
        ]
        result = optimizer.optimize(messages, max_tokens=500)
        assert len(result) < len(messages)

    def test_compress_code_context(self, optimizer):
        blocks = ["def foo():\n    # comment\n    pass\n"] * 5
        result = optimizer.compress_code_context(blocks, max_chars=1000)
        assert isinstance(result, str)

    def test_strip_comments(self, optimizer):
        code = "# This is a comment\ndef foo():\n    return 1\n"
        result = optimizer._strip_comments(code)
        assert "# This is a comment" not in result
        assert "def foo():" in result

    def test_optimal_max_tokens(self, optimizer):
        result = optimizer.get_optimal_max_tokens(100_000, model_limit=128_000)
        assert 1000 <= result <= 4096


class TestBaseProvider:
    """Tests for the abstract provider interface."""

    def test_llm_message(self):
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"

    def test_llm_response(self):
        resp = LLMResponse(
            content="Hi there",
            model="gpt-4o",
            provider="openai",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert resp.content == "Hi there"
        assert resp.usage["total_tokens"] == 15

    def test_token_estimation(self):
        # Can't instantiate ABC, test via a concrete implementation
        from jeph2sworm.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider()
        tokens = provider.estimate_tokens("Hello world, this is a test.")
        assert tokens > 0
