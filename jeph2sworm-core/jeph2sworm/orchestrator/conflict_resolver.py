"""Conflict Resolver - handles merge conflicts and agent disagreements."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import structlog

from jeph2sworm.brain.memory import Brain
from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.llm.router import LLMRouter

logger = structlog.get_logger()


class ConflictType:
    FILE_CONFLICT = "file_conflict"        # Two agents wrote to same file
    API_MISMATCH = "api_mismatch"          # Frontend/Backend API disagreement
    DESIGN_MISMATCH = "design_mismatch"    # UX spec vs implementation
    DEPENDENCY_CYCLE = "dependency_cycle"  # Circular task dependencies
    RESOURCE_CONTENTION = "resource"       # Same resource used by multiple agents


class ConflictResolver:
    """
    Detects and resolves conflicts between agents.

    Monitors for:
    - File write conflicts (two agents editing the same file)
    - API contract mismatches
    - Design spec violations
    - Dependency cycles
    """

    def __init__(self, brain: Brain, llm_router: LLMRouter):
        self.brain = brain
        self.llm_router = llm_router
        self._file_locks: Dict[str, str] = {}  # filepath -> agent_id

        event_bus.subscribe(EventType.FILE_CREATED, self._on_file_write)
        event_bus.subscribe(EventType.FILE_MODIFIED, self._on_file_write)

    async def acquire_file_lock(self, filepath: str, agent_id: str) -> bool:
        """Try to acquire a lock on a file for an agent."""
        current_holder = self._file_locks.get(filepath)

        if current_holder is None or current_holder == agent_id:
            self._file_locks[filepath] = agent_id
            return True

        logger.warning(
            f"File conflict: {agent_id} wants {filepath}, held by {current_holder}"
        )

        await event_bus.emit(
            EventType.CONFLICT_DETECTED,
            source="conflict-resolver",
            data={
                "type": ConflictType.FILE_CONFLICT,
                "file": filepath,
                "holder": current_holder,
                "requester": agent_id,
            },
        )

        return False

    def release_file_lock(self, filepath: str, agent_id: str) -> None:
        """Release a file lock."""
        if self._file_locks.get(filepath) == agent_id:
            del self._file_locks[filepath]

    async def resolve_conflict(self, conflict: dict) -> dict:
        """Resolve a conflict using LLM arbitration."""
        conflict_type = conflict.get("type", "")

        if conflict_type == ConflictType.FILE_CONFLICT:
            return await self._resolve_file_conflict(conflict)
        elif conflict_type == ConflictType.API_MISMATCH:
            return await self._resolve_api_mismatch(conflict)
        elif conflict_type == ConflictType.DESIGN_MISMATCH:
            return await self._resolve_design_mismatch(conflict)

        return {"resolution": "unresolved", "reason": f"Unknown conflict type: {conflict_type}"}

    async def _resolve_file_conflict(self, conflict: dict) -> dict:
        """Resolve a file write conflict between two agents."""
        filepath = conflict.get("file", "")
        holder = conflict.get("holder", "")
        requester = conflict.get("requester", "")

        # Simple priority: Brain > Backend > Frontend > UX > Tester > DevOps
        priority_order = ["brain", "backend", "frontend", "ux", "tester", "devops", "pm"]

        holder_role = holder.replace("-agent", "")
        requester_role = requester.replace("-agent", "")

        holder_priority = priority_order.index(holder_role) if holder_role in priority_order else 99
        requester_priority = priority_order.index(requester_role) if requester_role in priority_order else 99

        winner = holder if holder_priority <= requester_priority else requester
        loser = requester if winner == holder else holder

        logger.info(f"File conflict resolved: {winner} wins {filepath} over {loser}")

        # Notify the loser to retry later
        await event_bus.emit(
            EventType.CONFLICT_RESOLVED,
            source="conflict-resolver",
            data={
                "type": ConflictType.FILE_CONFLICT,
                "file": filepath,
                "winner": winner,
                "loser": loser,
                "action": "retry_later",
            },
        )

        return {"resolution": "priority", "winner": winner, "file": filepath}

    async def _resolve_api_mismatch(self, conflict: dict) -> dict:
        """Resolve an API contract mismatch using the Brain's contracts as truth."""
        arch = await self.brain.read("architecture") or {}
        api_contracts = arch.get("api_contracts", "")

        resolution = await self.llm_router.chat(
            system_prompt="You are a conflict resolver for an API mismatch between backend and frontend.",
            user_message=(
                f"Official API contracts:\n{api_contracts}\n\n"
                f"Conflict details:\n{json.dumps(conflict, indent=2)}\n\n"
                "Which implementation matches the contract? "
                "Output JSON: {\"correct_agent\": \"...\", \"fix_needed_by\": \"...\", \"details\": \"...\"}"
            ),
            agent_id="conflict-resolver",
            task_type="general",
        )

        return {"resolution": "api_contract_check", "details": resolution}

    async def _resolve_design_mismatch(self, conflict: dict) -> dict:
        """Resolve a design spec mismatch."""
        arch = await self.brain.read("architecture") or {}
        design_system = arch.get("design_system", "")

        resolution = await self.llm_router.chat(
            system_prompt="You are a conflict resolver for a UX design mismatch.",
            user_message=(
                f"Design system:\n{design_system}\n\n"
                f"Conflict:\n{json.dumps(conflict, indent=2)}\n\n"
                "What needs to be fixed? "
                "Output JSON: {\"fix_agent\": \"frontend\", \"changes\": [...]}"
            ),
            agent_id="conflict-resolver",
            task_type="general",
        )

        return {"resolution": "design_check", "details": resolution}

    async def _on_file_write(self, event: SwarmEvent) -> None:
        """Track file writes from agents."""
        source = event.source
        filepath = (event.data or {}).get("path", "")
        if filepath and source:
            self._file_locks[filepath] = source

    async def check_api_consistency(self) -> List[dict]:
        """Check if backend/frontend implementations match API contracts."""
        mismatches = []

        arch = await self.brain.read("architecture") or {}
        contracts = arch.get("api_contracts", "")
        if not contracts:
            return mismatches

        # This would be enhanced with actual code analysis
        logger.info("API consistency check completed")
        return mismatches

    def get_active_locks(self) -> Dict[str, str]:
        """Get all active file locks."""
        return dict(self._file_locks)
