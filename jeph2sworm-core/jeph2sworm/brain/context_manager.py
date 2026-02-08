"""Context Manager - per-agent context extraction from the Brain."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.brain.memory import Brain

logger = structlog.get_logger()


# Maximum context size in characters per agent
MAX_CONTEXT_CHARS = 12000


class ContextManager:
    """
    Extracts role-specific context from the Brain for each agent.

    Instead of giving every agent the entire Brain, we slice relevant
    sections and compress them to fit within LLM context windows.
    """

    # Which Brain sections each role needs
    ROLE_CONTEXT_MAP: Dict[str, List[str]] = {
        "pm": [
            "project_spec",
            "task_board",
            "agent_states",
            "conversation_history",
            "decisions_log",
            "errors_log",
        ],
        "brain": [
            "project_spec",
            "architecture",
            "api_contracts",
            "task_board",
            "decisions_log",
        ],
        "backend": [
            "project_spec",
            "architecture",
            "api_contracts",
            "task_board",
            "errors_log",
            "credentials",
        ],
        "frontend": [
            "project_spec",
            "architecture",
            "api_contracts",
            "task_board",
            "errors_log",
        ],
        "ux": [
            "project_spec",
            "architecture",
            "task_board",
        ],
        "tester": [
            "project_spec",
            "architecture",
            "api_contracts",
            "task_board",
            "test_results",
            "errors_log",
        ],
        "devops": [
            "project_spec",
            "architecture",
            "task_board",
            "credentials",
            "errors_log",
        ],
    }

    def __init__(self, brain: Brain):
        self.brain = brain

    def get_context(self, role: str, max_chars: int = MAX_CONTEXT_CHARS) -> dict:
        """
        Build a context payload for a specific agent role.

        Returns a dict with only the sections relevant to that role,
        trimmed to fit within max_chars when serialized.
        Uses brain.data (sync cached access) for speed.
        """
        sections = self.ROLE_CONTEXT_MAP.get(role, ["project_spec", "task_board"])
        context: Dict[str, Any] = {}

        for section in sections:
            value = self.brain.data.get(section)
            if value is not None:
                context[section] = value

        # Add role-specific computed fields
        context["my_tasks"] = self._get_tasks_for_role(role)
        context["task_board_summary"] = self._summarize_task_board()

        # Trim if too large
        serialized = json.dumps(context, default=str)
        if len(serialized) > max_chars:
            context = self._compress_context(context, max_chars)

        return context

    def _get_tasks_for_role(self, role: str) -> List[dict]:
        """Get tasks assigned to a specific role."""
        board = self.brain.data.get("task_board", {})
        tasks: List[dict] = []

        for status in ("backlog", "assigned", "in_progress"):
            for task in board.get(status, []):
                if task.get("assigned_to") == role:
                    tasks.append({**task, "status": status})

        return tasks

    def _summarize_task_board(self) -> Dict[str, int]:
        """Get a count summary of the task board."""
        board = self.brain.data.get("task_board", {})
        return {
            status: len(tasks)
            for status, tasks in board.items()
            if isinstance(tasks, list)
        }

    def _compress_context(self, context: dict, max_chars: int) -> dict:
        """Compress context to fit within max_chars."""
        compressed = {}

        # Priority order: project_spec > architecture > task_board > rest
        priority = [
            "project_spec",
            "architecture",
            "api_contracts",
            "my_tasks",
            "task_board_summary",
            "task_board",
            "agent_states",
            "errors_log",
            "test_results",
            "decisions_log",
            "conversation_history",
            "credentials",
        ]

        remaining = max_chars
        for key in priority:
            if key not in context:
                continue

            value = context[key]
            serialized = json.dumps(value, default=str)

            if len(serialized) <= remaining:
                compressed[key] = value
                remaining -= len(serialized)
            else:
                # Truncate lists
                if isinstance(value, list) and value:
                    truncated = value[: max(1, remaining // 200)]
                    compressed[key] = truncated
                    remaining -= len(json.dumps(truncated, default=str))
                elif isinstance(value, dict):
                    # Include keys only
                    compressed[key] = {k: "..." for k in list(value.keys())[:10]}
                    remaining -= 100

                if remaining <= 0:
                    break

        return compressed

    def get_diff_since(self, role: str, last_seen_version: int) -> dict:
        """Get only changes since the agent last checked the Brain."""
        # Simple version-based diff
        current_version = self.brain.data.get("_version", 0)
        if last_seen_version >= current_version:
            return {}

        # For now, return full context (future: track per-field versions)
        return self.get_context(role)
