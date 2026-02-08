"""Vector Store - ChromaDB integration for RAG-based context retrieval."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class VectorStore:
    """
    ChromaDB-backed vector store for semantic search across project knowledge.

    Stores embeddings for:
    - Code files (chunked by function/class)
    - Architecture decisions
    - Conversation history
    - API contracts
    - Error logs and solutions
    """

    COLLECTIONS = [
        "code_chunks",
        "architecture",
        "conversations",
        "api_contracts",
        "errors_and_solutions",
        "test_results",
    ]

    def __init__(self, persist_dir: str = ".jeph2sworm/vectordb"):
        self.persist_dir = persist_dir
        self._client = None
        self._collections: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collections."""
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_dir,
                    anonymized_telemetry=False,
                )
            )

            for name in self.COLLECTIONS:
                self._collections[name] = self._client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )

            logger.info("vector_store_initialized", collections=self.COLLECTIONS)

        except ImportError:
            logger.warning("chromadb_not_installed", msg="Vector store disabled")
        except Exception as e:
            logger.error("vector_store_init_failed", error=str(e))

    async def add_document(
        self,
        collection: str,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a document to a collection."""
        if collection not in self._collections:
            logger.warning("collection_not_found", collection=collection)
            return

        coll = self._collections[collection]
        coll.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {}],
        )

    async def add_documents(
        self,
        collection: str,
        doc_ids: List[str],
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add multiple documents to a collection."""
        if collection not in self._collections:
            return

        coll = self._collections[collection]
        coll.upsert(
            ids=doc_ids,
            documents=contents,
            metadatas=metadatas or [{} for _ in doc_ids],
        )

    async def query(
        self,
        collection: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search within a collection."""
        if collection not in self._collections:
            return []

        coll = self._collections[collection]
        kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        results = coll.query(**kwargs)

        docs = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                entry: Dict[str, Any] = {
                    "id": results["ids"][0][i],
                    "content": doc,
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
                if results.get("metadatas") and results["metadatas"][0]:
                    entry["metadata"] = results["metadatas"][0][i]
                docs.append(entry)

        return docs

    async def search_code(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search across code chunks."""
        return await self.query("code_chunks", query, n_results)

    async def search_errors(self, error_msg: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar past errors and their solutions."""
        return await self.query("errors_and_solutions", error_msg, n_results)

    async def index_file(self, filepath: str, content: str, language: str = "unknown") -> None:
        """Index a source file by splitting into chunks."""
        chunks = self._chunk_code(content, filepath, language)
        if not chunks:
            return

        ids = [f"{filepath}::{i}" for i in range(len(chunks))]
        metadatas = [
            {"filepath": filepath, "language": language, "chunk_index": i}
            for i in range(len(chunks))
        ]

        await self.add_documents("code_chunks", ids, chunks, metadatas)

    def _chunk_code(
        self, content: str, filepath: str, language: str, max_chunk: int = 1000
    ) -> List[str]:
        """Split code into meaningful chunks (by function/class boundaries)."""
        lines = content.split("\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        boundary_markers = {
            "python": ("def ", "class ", "async def "),
            "typescript": ("function ", "class ", "export ", "const ", "interface "),
            "javascript": ("function ", "class ", "export ", "const "),
        }
        markers = boundary_markers.get(language, ("function ", "class ", "def "))

        for line in lines:
            stripped = line.strip()

            # Check if this line starts a new logical block
            is_boundary = any(stripped.startswith(m) for m in markers)

            if is_boundary and current_chunk and current_size > 100:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += len(line)

            if current_size >= max_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    async def delete_collection(self, collection: str) -> None:
        """Delete an entire collection."""
        if self._client and collection in self._collections:
            self._client.delete_collection(collection)
            del self._collections[collection]

    async def get_stats(self) -> Dict[str, int]:
        """Get document counts per collection."""
        stats = {}
        for name, coll in self._collections.items():
            try:
                stats[name] = coll.count()
            except Exception:
                stats[name] = 0
        return stats
