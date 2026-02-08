"""Task Board - Kanban-style task management for the swarm."""

from __future__ import annotations

import asyncio
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class Task(BaseModel):
    """A unit of work for an agent."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    description: str = ""
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.BACKLOG
    dependencies: List[str] = Field(default_factory=list)
    subtasks: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    files_affected: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class TaskBoard:
    """
    Centralized task management board used by SwarmManager and all agents.

    Implements a Kanban-style board: backlog -> assigned -> in_progress -> review -> done
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    @property
    def tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_to: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Create a new task and add it to the board."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            dependencies=dependencies or [],
            parent_id=parent_id,
            metadata=metadata or {},
            status=TaskStatus.ASSIGNED if assigned_to else TaskStatus.BACKLOG,
        )
        self._tasks[task.id] = task

        # If this is a subtask, link it to the parent
        if parent_id and parent_id in self._tasks:
            self._tasks[parent_id].subtasks.append(task.id)

        asyncio.ensure_future(event_bus.emit(
            EventType.TASK_CREATED,
            source="task_board",
            data=task.model_dump(),
        ))

        logger.info("task_created", task_id=task.id, title=title, assigned_to=assigned_to)
        return task

    def assign_task(self, task_id: str, agent_role: str) -> Optional[Task]:
        """Assign a task to an agent."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        task.assigned_to = agent_role
        task.status = TaskStatus.ASSIGNED
        task.updated_at = time.time()

        asyncio.ensure_future(event_bus.emit(
            EventType.TASK_ASSIGNED,
            source="task_board",
            data={"task_id": task_id, "assigned_to": agent_role},
        ))

        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        """Move a task to in_progress."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        # Check dependencies
        if not self._dependencies_met(task):
            task.status = TaskStatus.BLOCKED
            task.error = "Dependencies not met"
            return task

        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = time.time()

        asyncio.ensure_future(event_bus.emit(
            EventType.TASK_STARTED,
            source=task.assigned_to or "task_board",
            data={"task_id": task_id},
        ))

        return task

    def complete_task(self, task_id: str, files_affected: Optional[List[str]] = None) -> Optional[Task]:
        """Mark a task as done."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        task.status = TaskStatus.DONE
        task.completed_at = time.time()
        task.updated_at = time.time()
        if files_affected:
            task.files_affected = files_affected

        asyncio.ensure_future(event_bus.emit(
            EventType.TASK_COMPLETED,
            source=task.assigned_to or "task_board",
            data={"task_id": task_id, "files_affected": task.files_affected},
        ))

        logger.info("task_completed", task_id=task_id, title=task.title)
        return task

    def block_task(self, task_id: str, reason: str) -> Optional[Task]:
        """Mark a task as blocked."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        task.status = TaskStatus.BLOCKED
        task.error = reason
        task.updated_at = time.time()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_tasks_for_agent(self, agent_role: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        return [t for t in self._tasks.values() if t.assigned_to == agent_role]

    def get_pending_tasks(self, agent_role: Optional[str] = None) -> List[Task]:
        """Get tasks that are ready to be worked on."""
        pending = []
        for task in self._tasks.values():
            if task.status in (TaskStatus.BACKLOG, TaskStatus.ASSIGNED):
                if agent_role and task.assigned_to and task.assigned_to != agent_role:
                    continue
                if self._dependencies_met(task):
                    pending.append(task)

        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        pending.sort(key=lambda t: priority_order.get(t.priority, 2))
        return pending

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a given status."""
        return [t for t in self._tasks.values() if t.status == status]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the board state."""
        summary: Dict[str, int] = {}
        for task in self._tasks.values():
            summary[task.status.value] = summary.get(task.status.value, 0) + 1

        return {
            "total": len(self._tasks),
            "by_status": summary,
            "by_agent": self._count_by_agent(),
        }

    def _count_by_agent(self) -> Dict[str, int]:
        """Count active tasks per agent."""
        counts: Dict[str, int] = {}
        for task in self._tasks.values():
            if task.assigned_to and task.status not in (TaskStatus.DONE, TaskStatus.BACKLOG):
                counts[task.assigned_to] = counts.get(task.assigned_to, 0) + 1
        return counts

    def _dependencies_met(self, task: Task) -> bool:
        """Check if all dependency tasks are completed."""
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if not dep or dep.status != TaskStatus.DONE:
                return False
        return True

    def to_dict(self) -> Dict[str, List[dict]]:
        """Export board state as dict for Brain storage."""
        board: Dict[str, List[dict]] = {s.value: [] for s in TaskStatus}
        for task in self._tasks.values():
            board[task.status.value].append(task.model_dump())
        return board

    def load_from_dict(self, data: Dict[str, List[dict]]) -> None:
        """Load board state from Brain data."""
        self._tasks.clear()
        for _status, tasks in data.items():
            for task_data in tasks:
                task = Task(**task_data)
                self._tasks[task.id] = task

        logger.info("task_board_loaded", total=len(self._tasks))
