"""Decision Log - Structured tracking of architecture and design decisions."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class Decision(BaseModel):
    """A recorded design or architecture decision."""

    id: str
    title: str
    description: str
    rationale: str
    decided_by: str  # agent role
    category: str = "general"  # architecture, api, frontend, backend, devops, testing, security
    alternatives_considered: List[str] = Field(default_factory=list)
    impact: str = ""  # what this affects
    reversible: bool = True
    timestamp: float = Field(default_factory=time.time)
    status: str = "active"  # active, superseded, reverted
    superseded_by: Optional[str] = None
    related_tasks: List[str] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)


class DecisionLog:
    """
    Tracks all architecture and design decisions made during a project build.

    This gives agents visibility into WHY things were decided,
    preventing contradictory choices and enabling informed trade-offs.
    """

    def __init__(self, persist_path: str = ".jeph2sworm/decisions.json"):
        self.persist_path = Path(persist_path)
        self._decisions: Dict[str, Decision] = {}
        self._counter = 0

    async def initialize(self) -> None:
        """Load existing decisions from disk."""
        if self.persist_path.exists():
            try:
                data = json.loads(self.persist_path.read_text())
                for d in data:
                    decision = Decision(**d)
                    self._decisions[decision.id] = decision
                self._counter = len(self._decisions)
                logger.info("decision_log_loaded", count=self._counter)
            except Exception as e:
                logger.error("decision_log_load_failed", error=str(e))

    def record(
        self,
        title: str,
        description: str,
        rationale: str,
        decided_by: str,
        category: str = "general",
        alternatives: Optional[List[str]] = None,
        impact: str = "",
        related_tasks: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None,
    ) -> Decision:
        """Record a new decision."""
        self._counter += 1
        decision = Decision(
            id=f"DEC-{self._counter:04d}",
            title=title,
            description=description,
            rationale=rationale,
            decided_by=decided_by,
            category=category,
            alternatives_considered=alternatives or [],
            impact=impact,
            related_tasks=related_tasks or [],
            related_files=related_files or [],
        )
        self._decisions[decision.id] = decision

        logger.info(
            "decision_recorded",
            id=decision.id,
            title=title,
            by=decided_by,
            category=category,
        )

        # Auto-persist
        self._persist()

        return decision

    def supersede(self, old_id: str, new_decision: Decision) -> None:
        """Mark an old decision as superseded by a new one."""
        old = self._decisions.get(old_id)
        if old:
            old.status = "superseded"
            old.superseded_by = new_decision.id
            self._persist()

    def revert(self, decision_id: str, reason: str = "") -> Optional[Decision]:
        """Revert a decision."""
        decision = self._decisions.get(decision_id)
        if decision:
            decision.status = "reverted"
            if reason:
                decision.rationale += f"\n\n[REVERTED]: {reason}"
            self._persist()
        return decision

    def get(self, decision_id: str) -> Optional[Decision]:
        """Get a specific decision."""
        return self._decisions.get(decision_id)

    def get_active(self) -> List[Decision]:
        """Get all active (non-superseded, non-reverted) decisions."""
        return [d for d in self._decisions.values() if d.status == "active"]

    def get_by_category(self, category: str) -> List[Decision]:
        """Get decisions in a specific category."""
        return [
            d for d in self._decisions.values()
            if d.category == category and d.status == "active"
        ]

    def get_by_agent(self, agent_role: str) -> List[Decision]:
        """Get decisions made by a specific agent."""
        return [d for d in self._decisions.values() if d.decided_by == agent_role]

    def search(self, query: str) -> List[Decision]:
        """Simple text search across decisions."""
        query_lower = query.lower()
        results = []
        for d in self._decisions.values():
            if (
                query_lower in d.title.lower()
                or query_lower in d.description.lower()
                or query_lower in d.rationale.lower()
            ):
                results.append(d)
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all decisions."""
        categories: Dict[str, int] = {}
        agents: Dict[str, int] = {}

        for d in self._decisions.values():
            if d.status == "active":
                categories[d.category] = categories.get(d.category, 0) + 1
                agents[d.decided_by] = agents.get(d.decided_by, 0) + 1

        return {
            "total": len(self._decisions),
            "active": len([d for d in self._decisions.values() if d.status == "active"]),
            "superseded": len([d for d in self._decisions.values() if d.status == "superseded"]),
            "reverted": len([d for d in self._decisions.values() if d.status == "reverted"]),
            "by_category": categories,
            "by_agent": agents,
        }

    def to_context_string(self, max_decisions: int = 20) -> str:
        """Export active decisions as a context string for LLM prompts."""
        active = self.get_active()[-max_decisions:]
        if not active:
            return "No decisions recorded yet."

        lines = ["## Project Decisions\n"]
        for d in active:
            lines.append(f"### {d.id}: {d.title}")
            lines.append(f"- Category: {d.category}")
            lines.append(f"- Decided by: {d.decided_by}")
            lines.append(f"- Rationale: {d.rationale}")
            if d.impact:
                lines.append(f"- Impact: {d.impact}")
            lines.append("")

        return "\n".join(lines)

    def _persist(self) -> None:
        """Save decisions to disk."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = [d.model_dump() for d in self._decisions.values()]
            self.persist_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error("decision_log_persist_failed", error=str(e))
