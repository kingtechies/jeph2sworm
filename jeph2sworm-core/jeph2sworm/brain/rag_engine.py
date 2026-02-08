"""RAG Engine - Retrieval-Augmented Generation using the Vector Store."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.brain.vector_store import VectorStore

logger = structlog.get_logger()


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.

    Queries the vector store for relevant context before sending
    prompts to the LLM, reducing hallucinations and improving
    code accuracy by grounding responses in actual project data.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def enrich_prompt(
        self,
        prompt: str,
        role: str,
        max_context_items: int = 8,
    ) -> str:
        """
        Enrich a prompt with relevant context from the vector store.

        Searches across collections based on the agent role and query,
        then prepends the retrieved context to the original prompt.
        """
        context_parts: List[str] = []

        # Search relevant collections based on role
        search_collections = self._get_collections_for_role(role)

        for collection in search_collections:
            results = await self.vector_store.query(
                collection=collection,
                query_text=prompt,
                n_results=max_context_items // len(search_collections),
            )
            for result in results:
                context_parts.append(
                    f"[{collection}] {result.get('metadata', {}).get('filepath', '')}:\n"
                    f"{result['content']}"
                )

        if not context_parts:
            return prompt

        context_block = "\n\n---\n\n".join(context_parts)
        return (
            f"## Relevant Project Context\n\n"
            f"{context_block}\n\n"
            f"---\n\n"
            f"## Current Task\n\n"
            f"{prompt}"
        )

    async def find_similar_code(
        self, code_snippet: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find code similar to a given snippet (for consistency/reuse)."""
        return await self.vector_store.search_code(code_snippet, n_results)

    async def find_error_solution(self, error_msg: str) -> Optional[str]:
        """Look up past solutions for a similar error."""
        results = await self.vector_store.search_errors(error_msg, n_results=3)
        if not results:
            return None

        solutions = []
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("solution"):
                solutions.append(
                    f"Error: {meta.get('error', 'unknown')}\n"
                    f"Solution: {meta['solution']}"
                )

        return "\n\n".join(solutions) if solutions else None

    async def index_project_file(
        self, filepath: str, content: str, language: str = "unknown"
    ) -> None:
        """Index a project file for RAG retrieval."""
        await self.vector_store.index_file(filepath, content, language)
        logger.debug("file_indexed", filepath=filepath, language=language)

    async def store_error_solution(
        self, error_msg: str, solution: str, context: Optional[str] = None
    ) -> None:
        """Store an error and its solution for future RAG lookups."""
        import hashlib

        doc_id = hashlib.sha256(error_msg.encode()).hexdigest()[:16]
        await self.vector_store.add_document(
            collection="errors_and_solutions",
            doc_id=f"error_{doc_id}",
            content=f"Error: {error_msg}\nSolution: {solution}",
            metadata={
                "error": error_msg[:500],
                "solution": solution[:2000],
                "context": (context or "")[:1000],
            },
        )

    async def store_decision(
        self, decision: str, rationale: str, agent: str
    ) -> None:
        """Store an architecture/design decision for RAG retrieval."""
        import hashlib
        import time

        doc_id = hashlib.sha256(f"{decision}{time.time()}".encode()).hexdigest()[:16]
        await self.vector_store.add_document(
            collection="architecture",
            doc_id=f"decision_{doc_id}",
            content=f"Decision: {decision}\nRationale: {rationale}\nBy: {agent}",
            metadata={
                "type": "decision",
                "agent": agent,
                "decision": decision[:500],
            },
        )

    async def store_api_contract(
        self, endpoint: str, contract: Dict[str, Any]
    ) -> None:
        """Store an API contract for RAG retrieval."""
        import hashlib

        doc_id = hashlib.sha256(endpoint.encode()).hexdigest()[:16]
        await self.vector_store.add_document(
            collection="api_contracts",
            doc_id=f"api_{doc_id}",
            content=json.dumps(contract, indent=2),
            metadata={"endpoint": endpoint, "method": contract.get("method", "GET")},
        )

    def _get_collections_for_role(self, role: str) -> List[str]:
        """Determine which collections are most relevant for a given agent role."""
        role_collections = {
            "pm": ["conversations", "architecture"],
            "brain": ["architecture", "api_contracts", "code_chunks"],
            "backend": ["code_chunks", "api_contracts", "errors_and_solutions"],
            "frontend": ["code_chunks", "api_contracts", "errors_and_solutions"],
            "ux": ["architecture", "code_chunks"],
            "tester": ["code_chunks", "test_results", "errors_and_solutions"],
            "devops": ["architecture", "errors_and_solutions"],
        }
        return role_collections.get(role, ["code_chunks", "architecture"])
