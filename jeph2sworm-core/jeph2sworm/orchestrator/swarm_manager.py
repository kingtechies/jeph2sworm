"""Swarm Manager - creates, coordinates, and manages all agents."""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import structlog

from jeph2sworm.agents.base_agent import AgentRole, AgentStatus, BaseAgent
from jeph2sworm.agents.pm_agent import PMAgent
from jeph2sworm.agents.brain_agent import BrainAgent
from jeph2sworm.agents.backend_agent import BackendAgent
from jeph2sworm.agents.frontend_agent import FrontendAgent
from jeph2sworm.agents.ux_agent import UXAgent
from jeph2sworm.agents.tester_agent import TesterAgent
from jeph2sworm.agents.devops_agent import DevOpsAgent
from jeph2sworm.brain.memory import Brain
from jeph2sworm.config import Settings
from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.llm.router import LLMRouter
from jeph2sworm.security.rules_engine import RulesEngine

logger = structlog.get_logger()


AGENT_CLASSES = {
    AgentRole.PM: PMAgent,
    AgentRole.BRAIN: BrainAgent,
    AgentRole.BACKEND: BackendAgent,
    AgentRole.FRONTEND: FrontendAgent,
    AgentRole.UX: UXAgent,
    AgentRole.TESTER: TesterAgent,
    AgentRole.DEVOPS: DevOpsAgent,
}


class SwarmManager:
    """
    Central orchestrator for the entire agent swarm.

    Creates all agents, starts/stops them, routes messages,
    and provides status overview. All agents run concurrently.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.brain = Brain(brain_dir=self.settings.brain_dir)
        self.llm_router = LLMRouter()
        self.rules_engine = RulesEngine(workspace_root=self.settings.workspace_dir)
        self.agents: Dict[str, BaseAgent] = {}
        self._agent_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        # Subscribe to events
        event_bus.subscribe(EventType.AGENT_ERROR, self._on_agent_error)
        event_bus.subscribe(EventType.AGENT_BLOCKED, self._on_agent_blocked)

    async def initialize(self) -> None:
        """Initialize the swarm - create all agents."""
        logger.info("Initializing swarm manager")

        # Load brain state
        await self.brain.load()

        # Store workspace path in brain
        self.brain.data["workspace_path"] = str(self.settings.workspace_dir)

        # Create all agents
        for role, agent_cls in AGENT_CLASSES.items():
            agent_id = f"{role.value}-agent"
            agent = agent_cls(
                agent_id=agent_id,
                role=role,
                brain=self.brain,
                llm_router=self.llm_router,
                workspace=self.settings.workspace_dir,
            )
            self.agents[agent_id] = agent
            logger.info(f"Created agent: {agent_id}")

        await event_bus.emit(
            EventType.SYSTEM_READY,
            source="swarm-manager",
            data={"agents": list(self.agents.keys())},
        )

        logger.info(f"Swarm initialized with {len(self.agents)} agents")

    async def start(self) -> None:
        """Start all agents - they begin their autonomous work loops."""
        if self._running:
            return

        self._running = True
        logger.info("Starting swarm")

        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(
                agent.start(),
                name=f"agent-{agent_id}",
            )
            self._agent_tasks[agent_id] = task
            logger.info(f"Started agent: {agent_id}")

        await event_bus.emit(
            EventType.SYSTEM_READY,
            source="swarm-manager",
            data={"status": "all_agents_started"},
        )

    async def stop(self) -> None:
        """Stop all agents gracefully."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping swarm")

        # Stop all agents
        for agent_id, agent in self.agents.items():
            await agent.stop()
            logger.info(f"Stopped agent: {agent_id}")

        # Cancel running tasks
        for agent_id, task in self._agent_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._agent_tasks.clear()

        # Save brain state
        await self.brain.save()

        logger.info("Swarm stopped")

    async def send_user_message(self, message: str) -> str:
        """Route a user message to the PM agent."""
        pm_agent = self.agents.get("pm-agent")
        if not pm_agent:
            return "PM agent not available"

        if isinstance(pm_agent, PMAgent):
            return await pm_agent.handle_user_message(message)
        return "PM agent type mismatch"

    async def set_project_spec(self, spec: dict) -> None:
        """Set the project specification in the Brain."""
        await self.brain.set_project_spec(spec)
        await event_bus.emit(
            EventType.TASK_CREATED,
            source="swarm-manager",
            data={"action": "project_spec_set", "spec": spec},
        )

    def get_status(self) -> dict:
        """Get the current status of all agents."""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = {
                "role": agent.role.value,
                "status": agent.status.value,
                "current_task": agent.current_task,
            }

        return {
            "running": self._running,
            "agent_count": len(self.agents),
            "agents": agent_statuses,
            "brain_stats": self.brain.get_stats(),
        }

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get a specific agent by ID."""
        return self.agents.get(agent_id)

    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """Get all agents with a specific role."""
        return [a for a in self.agents.values() if a.role == role]

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause a specific agent."""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.pause()
            return True
        return False

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent."""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.resume()
            return True
        return False

    async def _on_agent_error(self, event: dict) -> None:
        """Handle agent error events."""
        agent_id = event.get("source", "")
        error = event.get("data", {}).get("error", "Unknown error")
        logger.error(f"Agent error: {agent_id} - {error}")

        # Log to brain
        await self.brain.add_error(
            error=error,
            file_path="",
            agent_id=agent_id,
            details=str(event.get("data", {})),
        )

    async def _on_agent_blocked(self, event: dict) -> None:
        """Handle agent blocked events - try to resolve blockers."""
        agent_id = event.get("source", "")
        reason = event.get("data", {}).get("reason", "Unknown")
        logger.warning(f"Agent blocked: {agent_id} - {reason}")

        # Notify PM about blockers
        await event_bus.emit(
            EventType.AGENT_MESSAGE,
            source="swarm-manager",
            data={
                "target": "pm-agent",
                "message": f"Agent {agent_id} is blocked: {reason}",
            },
        )

    async def configure_llm_provider(
        self, provider: str, api_key: str, **kwargs
    ) -> None:
        """Configure an LLM provider with its API key."""
        self.llm_router.configure_provider(provider, api_key, **kwargs)
        logger.info(f"Configured LLM provider: {provider}")

    async def get_conversation_history(self) -> list:
        """Get the conversation history from the brain."""
        return self.brain.data.get("conversation_history", [])

    async def get_task_board(self) -> dict:
        """Get the current task board state."""
        return self.brain.data.get("task_board", {})
