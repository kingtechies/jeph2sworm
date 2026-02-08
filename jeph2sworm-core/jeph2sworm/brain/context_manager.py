"""Context Manager - per-agent context extraction from the Brain."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.brain.memory import Brain
from jeph2sworm.brain.vector_store import VectorStore

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

    def __init__(self, brain: Brain, vector_store: Optional[VectorStore] = None):
        self.brain = brain
        self.vector_store = vector_store

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

    async def get_context_for_task(
        self,
        role: str,
        task_description: str,
        max_chars: int = MAX_CONTEXT_CHARS,
    ) -> dict:
        """
        Get context for a specific task using RAG to find relevant code/docs.

        Args:
            role: The agent's role
            task_description: What the agent is working on
            max_chars: Maximum context size

        Returns:
            Context dict with role-specific sections plus RAG results
        """
        # Start with base context
        context = self.get_context(role, max_chars=max_chars // 2)

        # If vector store is available, add relevant code/docs
        if self.vector_store:
            rag_results = await self._query_relevant_context(role, task_description)
            if rag_results:
                context["relevant_code"] = rag_results.get("code", [])
                context["relevant_errors"] = rag_results.get("errors", [])

        return context

    async def _query_relevant_context(
        self,
        role: str,
        query: str,
        n_results: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Query vector store for context relevant to the task."""
        if not self.vector_store:
            return {}

        results: Dict[str, List[Dict[str, Any]]] = {}

        # Search code chunks for developer roles
        if role in ("backend", "frontend", "tester", "devops", "brain"):
            try:
                code_results = await self.vector_store.search_code(query, n_results)
                results["code"] = [
                    {
                        "file": r.get("metadata", {}).get("filepath", "unknown"),
                        "content": r.get("content", "")[:500],  # Truncate long chunks
                    }
                    for r in code_results
                ]
            except Exception as e:
                logger.warning("vector_search_failed", collection="code", error=str(e))

        # Search past errors for all roles
        try:
            error_results = await self.vector_store.search_errors(query, n_results=3)
            results["errors"] = [
                {
                    "error": r.get("content", "")[:300],
                    "solution": r.get("metadata", {}).get("solution", ""),
                }
                for r in error_results
            ]
        except Exception as e:
            logger.warning("vector_search_failed", collection="errors", error=str(e))

        return results

    async def index_project_file(self, filepath: str, content: str) -> None:
        """Index a project file for RAG retrieval."""
        if not self.vector_store:
            return

        # Detect language from extension
        lang_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
        }
        ext = "." + filepath.split(".")[-1] if "." in filepath else ""
        language = lang_map.get(ext, "unknown")

        await self.vector_store.index_file(filepath, content, language)

    async def index_error_solution(
        self, error: str, solution: str, context: Optional[str] = None
    ) -> None:
        """Index an error and its solution for future retrieval."""
        if not self.vector_store:
            return

        import hashlib
        doc_id = hashlib.md5(error.encode()).hexdigest()[:16]

        await self.vector_store.add_document(
            collection="errors_and_solutions",
            doc_id=f"error:{doc_id}",
            content=error,
            metadata={
                "solution": solution,
                "context": context or "",
            },
        )
