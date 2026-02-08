"""Base agent class - abstract foundation for all specialized agents."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import structlog

from jeph2sworm.brain.memory import Brain
from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.llm.router import LLMRouter
from jeph2sworm.tools.file_system import FileSystem
from jeph2sworm.tools.terminal import Terminal

logger = structlog.get_logger()


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    PAUSED = "paused"
    STOPPED = "stopped"


class AgentRole(str, Enum):
    PM = "pm"
    BRAIN = "brain"
    BACKEND = "backend"
    FRONTEND = "frontend"
    UX = "ux"
    TESTER = "tester"
    DEVOPS = "devops"


class BaseAgent(ABC):
    """
    Abstract base class for all swarm agents.

    Each agent has:
    - A role (PM, backend, frontend, etc.)
    - Access to the Brain (shared memory)
    - Access to the LLM router
    - Access to file system and terminal tools
    - An event loop that processes tasks autonomously
    - The ability to communicate with other agents via the event bus
    """

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        brain: Brain,
        llm: LLMRouter,
        file_system: FileSystem,
        terminal: Terminal,
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.brain = brain
        self.llm = llm
        self.fs = file_system
        self.terminal = terminal

        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None
        self._message_history: list[dict[str, str]] = []

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt that defines this agent's personality and capabilities."""
        ...

    @property
    def task_type(self) -> str:
        """The default LLM task type for this agent's work."""
        return "general"

    # ---- Lifecycle ----

    async def start(self) -> None:
        """Start the agent's autonomous work loop."""
        self._running = True
        self._paused = False
        self.status = AgentStatus.WORKING

        await self.brain.set_agent_state(
            self.agent_id, self.role.value, "working"
        )
        await event_bus.emit(
            EventType.AGENT_SPAWNED,
            source=self.agent_id,
            data={"role": self.role.value},
        )

        self._task = asyncio.create_task(self._work_loop())
        await logger.ainfo("agent_started", agent=self.agent_id, role=self.role.value)

    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        self.status = AgentStatus.STOPPED

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.brain.set_agent_state(
            self.agent_id, self.role.value, "stopped"
        )
        await event_bus.emit(
            EventType.AGENT_STOPPED,
            source=self.agent_id,
        )
        await logger.ainfo("agent_stopped", agent=self.agent_id)

    async def pause(self) -> None:
        """Pause the agent."""
        self._paused = True
        self.status = AgentStatus.PAUSED
        await self.brain.set_agent_state(
            self.agent_id, self.role.value, "paused"
        )

    async def resume(self) -> None:
        """Resume a paused agent."""
        self._paused = False
        self.status = AgentStatus.WORKING
        await self.brain.set_agent_state(
            self.agent_id, self.role.value, "working"
        )

    # ---- Work Loop ----

    async def _work_loop(self) -> None:
        """Main autonomous work loop. Agent keeps working until stopped."""
        try:
            while self._running:
                if self._paused:
                    await asyncio.sleep(1)
                    continue

                # Get context from Brain
                context = await self.brain.get_context_for_agent(self.role.value)

                # Get next task
                task = await self.get_next_task(context)
                if not task:
                    self.status = AgentStatus.IDLE
                    await asyncio.sleep(2)  # No tasks, wait and check again
                    continue

                self.status = AgentStatus.WORKING
                self.current_task = task.get("description", "working")
                await self.brain.set_agent_state(
                    self.agent_id, self.role.value, "working", self.current_task
                )

                # Execute the task
                try:
                    result = await self.execute_task(task, context)

                    # Report completion
                    await event_bus.emit(
                        EventType.TASK_COMPLETED,
                        source=self.agent_id,
                        data={
                            "task_id": task.get("id", "unknown"),
                            "result": result,
                        },
                    )

                    # Move task on the board
                    if task.get("id"):
                        await self.brain.move_task(
                            task["id"], "done", self.agent_id
                        )

                except Exception as e:
                    await logger.aerror(
                        "task_execution_failed",
                        agent=self.agent_id,
                        task=task,
                        error=str(e),
                    )
                    await self.brain.log_error(
                        error=str(e),
                        context=f"Agent {self.agent_id} executing task: {task}",
                        fixed_by=None,
                    )
                    await event_bus.emit(
                        EventType.ERROR_OCCURRED,
                        source=self.agent_id,
                        data={"error_type": type(e).__name__, "message": str(e)},
                    )

                # Brief pause between tasks to avoid flooding
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            await logger.aerror("agent_loop_error", agent=self.agent_id, error=str(e))

    # ---- Abstract Methods (each agent implements these) ----

    @abstractmethod
    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Determine the next task to work on based on Brain context."""
        ...

    @abstractmethod
    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a specific task. Returns a result description."""
        ...

    # ---- LLM Helpers ----

    async def think(self, prompt: str, task_type: Optional[str] = None) -> str:
        """Ask the LLM to think/reason about something."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self._message_history[-20:],  # Keep last 20 messages for context
            {"role": "user", "content": prompt},
        ]

        result = await self.llm.complete(
            messages=messages,
            agent_id=self.agent_id,
            task_type=task_type or self.task_type,
        )

        # Track conversation
        self._message_history.append({"role": "user", "content": prompt})
        self._message_history.append({"role": "assistant", "content": result["content"]})

        return result["content"]

    async def say(self, message: str) -> None:
        """Send a message visible to the user in the UI."""
        await event_bus.emit(
            EventType.AGENT_MESSAGE,
            source=self.agent_id,
            data={
                "role": self.role.value,
                "message": message,
            },
        )

    # ---- Tool Helpers ----

    async def write_code(self, path: str, content: str) -> None:
        """Write code to a file."""
        await self.fs.write_file(path, content, agent_id=self.agent_id)
        await self.say(f"Created {path}")

    async def run_command(self, command: str, **kwargs: Any) -> dict:
        """Run a terminal command."""
        return await self.terminal.run(command, agent_id=self.agent_id, **kwargs)
