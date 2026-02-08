"""Context Optimizer - Compresses and manages LLM context windows."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class ContextOptimizer:
    """
    Optimizes context sent to LLMs to maximize useful information
    within token limits.

    Techniques:
    - Conversation summarization (older messages -> summary)
    - Code deduplication (remove repeated imports/boilerplate)
    - Priority-based truncation (keep most relevant sections)
    - Dead context removal (completed tasks, resolved errors)
    """

    # Approximate chars per token
    CHARS_PER_TOKEN = 4

    def __init__(self, max_tokens: int = 100_000):
        self.max_tokens = max_tokens
        self._summaries: Dict[str, str] = {}

    def optimize(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Optimize a message list to fit within token budget.

        Strategy:
        1. Always keep system prompt + last N messages
        2. Summarize older conversation chunks
        3. Remove duplicate/redundant content
        """
        limit = max_tokens or self.max_tokens
        system_tokens = self._estimate_tokens(system_prompt)
        available = limit - system_tokens - 500  # buffer

        if not messages:
            return messages

        # Calculate current token usage
        total_tokens = sum(self._estimate_tokens(m.get("content", "")) for m in messages)

        if total_tokens <= available:
            return messages  # fits, no optimization needed

        # Strategy: keep last 10 messages, summarize the rest
        keep_last = min(10, len(messages))
        recent = messages[-keep_last:]
        older = messages[:-keep_last]

        recent_tokens = sum(self._estimate_tokens(m.get("content", "")) for m in recent)
        remaining = available - recent_tokens

        if older and remaining > 200:
            # Summarize older messages
            summary = self._summarize_messages(older, max_chars=remaining * self.CHARS_PER_TOKEN)
            summary_msg = {"role": "system", "content": f"[Previous conversation summary]: {summary}"}
            return [summary_msg] + recent
        else:
            return recent

    def compress_code_context(self, code_blocks: List[str], max_chars: int = 20000) -> str:
        """Compress multiple code blocks into a concise context string."""
        if not code_blocks:
            return ""

        total = "\n\n---\n\n".join(code_blocks)

        if len(total) <= max_chars:
            return total

        # Remove comments and empty lines to save space
        compressed_blocks = []
        for block in code_blocks:
            compressed = self._strip_comments(block)
            compressed = self._remove_empty_lines(compressed)
            compressed_blocks.append(compressed)

        total = "\n\n---\n\n".join(compressed_blocks)

        if len(total) <= max_chars:
            return total

        # Truncate from the beginning (keep most recent)
        return "...[truncated]...\n" + total[-max_chars:]

    def _summarize_messages(self, messages: List[Dict[str, str]], max_chars: int = 2000) -> str:
        """Create a concise summary of a list of messages."""
        parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Extract key points
            if len(content) > 200:
                # Take first and last sentences
                sentences = content.split(". ")
                if len(sentences) > 2:
                    content = f"{sentences[0]}. ... {sentences[-1]}"
                else:
                    content = content[:200] + "..."

            parts.append(f"{role}: {content}")

        summary = "\n".join(parts)
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "..."

        return summary

    def _strip_comments(self, code: str) -> str:
        """Remove single-line comments from code."""
        lines = code.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            # Skip pure comment lines (Python, JS, TS)
            if stripped.startswith("#") and not stripped.startswith("#!"):
                continue
            if stripped.startswith("//"):
                continue
            # Remove inline comments (simple heuristic)
            if "  #" in line and not line.strip().startswith('"') and not line.strip().startswith("'"):
                line = line[: line.index("  #")]
            result.append(line)
        return "\n".join(result)

    def _remove_empty_lines(self, text: str) -> str:
        """Collapse multiple empty lines into one."""
        return re.sub(r"\n{3,}", "\n\n", text)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text) // self.CHARS_PER_TOKEN

    def get_optimal_max_tokens(self, prompt_tokens: int, model_limit: int = 128_000) -> int:
        """Calculate the best max_tokens for completion given prompt size."""
        available = model_limit - prompt_tokens
        # Reserve at least 1000 tokens for response, cap at 4096
        return max(1000, min(4096, available))
