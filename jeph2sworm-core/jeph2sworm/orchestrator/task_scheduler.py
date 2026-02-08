"""Task Scheduler - prioritizes and distributes tasks across agents."""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import structlog

from jeph2sworm.agents.base_agent import AgentRole
from jeph2sworm.brain.memory import Brain
from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class TaskScheduler:
    """
    Manages task prioritization and distribution.

    Tasks flow: backlog -> assigned -> in_progress -> review -> done
    The scheduler watches the task board and assigns work to idle agents.
    """

    ROLE_PRIORITY = {
        AgentRole.BRAIN: 1,      # Architecture first
        AgentRole.UX: 2,         # Design second
        AgentRole.BACKEND: 3,    # Backend third
        AgentRole.FRONTEND: 4,   # Frontend fourth
        AgentRole.TESTER: 5,     # Testing concurrent
        AgentRole.DEVOPS: 6,     # DevOps concurrent
        AgentRole.PM: 0,         # PM always active
    }

    PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

    def __init__(self, brain: Brain):
        self.brain = brain
        self._running = False

        event_bus.subscribe(EventType.TASK_CREATED, self._on_task_created)
        event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)

    async def start(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        logger.info("Task scheduler started")

        while self._running:
            await self._schedule_cycle()
            await asyncio.sleep(2)  # Check every 2 seconds

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False

    async def _schedule_cycle(self) -> None:
        """One scheduling cycle - assign backlog tasks to available agents."""
        task_board = self.brain.data.get("task_board", {})
        backlog = task_board.get("backlog", [])

        if not backlog:
            return

        # Sort by priority
        sorted_tasks = sorted(
            backlog,
            key=lambda t: self.PRIORITY_WEIGHT.get(t.get("priority", "low"), 0),
            reverse=True,
        )

        # Check dependencies
        done_ids = {t.get("id") for t in task_board.get("done", [])}

        for task in sorted_tasks:
            deps = task.get("dependencies", [])
            if all(d in done_ids for d in deps):
                # Dependencies met - check if agent is available
                assigned_to = task.get("assigned_to", "")
                agent_states = self.brain.data.get("agent_states", {})
                agent_id = f"{assigned_to}-agent"
                agent_state = agent_states.get(agent_id, {})

                if agent_state.get("status") in ("idle", None):
                    await self._assign_task(task, agent_id)

    async def _assign_task(self, task: dict, agent_id: str) -> None:
        """Move a task from backlog to assigned."""
        task_id = task.get("id", "")
        await self.brain.assign_task(task_id, agent_id)

        await event_bus.emit(
            EventType.TASK_ASSIGNED,
            source="task-scheduler",
            data={"task_id": task_id, "agent_id": agent_id},
        )

        logger.info(f"Assigned task {task_id} to {agent_id}")

    async def _on_task_created(self, event: dict) -> None:
        """React to new task creation."""
        logger.info(f"New task created: {event.get('data', {})}")
        # Will be picked up in next schedule cycle

    async def _on_task_completed(self, event: dict) -> None:
        """React to task completion - may unblock dependent tasks."""
        data = event.get("data", {})
        task_id = data.get("task_id", "")
        logger.info(f"Task completed: {task_id}")

        # Trigger immediate reschedule to unblock dependents
        await self._schedule_cycle()

    def get_queue_status(self) -> dict:
        """Get the current queue status."""
        board = self.brain.data.get("task_board", {})
        return {
            "backlog": len(board.get("backlog", [])),
            "assigned": len(board.get("assigned", [])),
            "in_progress": len(board.get("in_progress", [])),
            "review": len(board.get("review", [])),
            "done": len(board.get("done", [])),
        }
