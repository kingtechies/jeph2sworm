"""Agent Lifecycle Manager - Manages agent creation, health, restart, and scaling."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.agents.base_agent import AgentRole, AgentStatus, BaseAgent
from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class AgentHealth:
    """Health status for a single agent."""

    __slots__ = (
        "role", "status", "last_heartbeat", "tasks_completed",
        "errors_count", "restarts", "uptime_start",
    )

    def __init__(self, role: str):
        self.role = role
        self.status = AgentStatus.IDLE
        self.last_heartbeat = time.time()
        self.tasks_completed = 0
        self.errors_count = 0
        self.restarts = 0
        self.uptime_start = time.time()

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.uptime_start

    @property
    def is_healthy(self) -> bool:
        """Agent is healthy if heartbeat within last 30 seconds."""
        return (time.time() - self.last_heartbeat) < 30

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "status": self.status.value if isinstance(self.status, AgentStatus) else str(self.status),
            "healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat,
            "tasks_completed": self.tasks_completed,
            "errors_count": self.errors_count,
            "restarts": self.restarts,
            "uptime_seconds": round(self.uptime_seconds, 1),
        }


class LifecycleManager:
    """
    Manages the full lifecycle of swarm agents:
    - Creation and initialization
    - Health monitoring with heartbeats
    - Automatic restart on failure
    - Graceful shutdown
    - Scaling (pause/resume based on workload)
    """

    HEALTH_CHECK_INTERVAL = 10  # seconds
    MAX_RESTARTS = 5
    HEARTBEAT_TIMEOUT = 30  # seconds

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._health: Dict[str, AgentHealth] = {}
        self._health_task: Optional[asyncio.Task] = None
        self._running = False

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent for lifecycle management."""
        role = agent.role.value if isinstance(agent.role, AgentRole) else str(agent.role)
        self._agents[role] = agent
        self._health[role] = AgentHealth(role)
        logger.info("agent_registered", role=role)

    async def start_all(self) -> None:
        """Start all registered agents and health monitoring."""
        self._running = True

        for role, agent in self._agents.items():
            await self._start_agent(role, agent)

        # Start health check loop
        self._health_task = asyncio.create_task(self._health_check_loop())

        event_bus.emit(SwarmEvent(
            type=EventType.SYSTEM_MESSAGE,
            agent="lifecycle",
            data={"action": "all_started", "agents": list(self._agents.keys())},
        ))

    async def stop_all(self) -> None:
        """Gracefully stop all agents."""
        self._running = False

        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        for role, agent in self._agents.items():
            await self._stop_agent(role, agent)

        logger.info("all_agents_stopped")

    async def restart_agent(self, role: str) -> bool:
        """Restart a specific agent."""
        agent = self._agents.get(role)
        if not agent:
            return False

        health = self._health[role]
        if health.restarts >= self.MAX_RESTARTS:
            logger.error(
                "max_restarts_exceeded",
                role=role,
                restarts=health.restarts,
            )
            return False

        await self._stop_agent(role, agent)
        await asyncio.sleep(1)
        await self._start_agent(role, agent)

        health.restarts += 1
        health.uptime_start = time.time()

        event_bus.emit(SwarmEvent(
            type=EventType.SYSTEM_MESSAGE,
            agent="lifecycle",
            data={"action": "agent_restarted", "role": role, "restarts": health.restarts},
        ))

        return True

    def heartbeat(self, role: str) -> None:
        """Record a heartbeat from an agent."""
        if role in self._health:
            self._health[role].last_heartbeat = time.time()

    def record_task_completed(self, role: str) -> None:
        """Record that an agent completed a task."""
        if role in self._health:
            self._health[role].tasks_completed += 1

    def record_error(self, role: str) -> None:
        """Record an agent error."""
        if role in self._health:
            self._health[role].errors_count += 1

    def get_health(self, role: Optional[str] = None) -> Any:
        """Get health status for one or all agents."""
        if role:
            h = self._health.get(role)
            return h.to_dict() if h else None
        return {r: h.to_dict() for r, h in self._health.items()}

    def get_unhealthy_agents(self) -> List[str]:
        """Get list of agents that have missed heartbeats."""
        return [role for role, h in self._health.items() if not h.is_healthy]

    async def _start_agent(self, role: str, agent: BaseAgent) -> None:
        """Start a single agent."""
        try:
            await agent.start()
            self._health[role].status = AgentStatus.IDLE
            self._health[role].last_heartbeat = time.time()
            logger.info("agent_started", role=role)
        except Exception as e:
            self._health[role].status = AgentStatus.STOPPED
            logger.error("agent_start_failed", role=role, error=str(e))

    async def _stop_agent(self, role: str, agent: BaseAgent) -> None:
        """Stop a single agent gracefully."""
        try:
            await agent.stop()
            self._health[role].status = AgentStatus.STOPPED
            logger.info("agent_stopped", role=role)
        except Exception as e:
            logger.error("agent_stop_failed", role=role, error=str(e))

    async def _health_check_loop(self) -> None:
        """Periodically check agent health and restart if needed."""
        while self._running:
            try:
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)

                for role, health in self._health.items():
                    if not health.is_healthy and self._running:
                        logger.warning(
                            "agent_unhealthy",
                            role=role,
                            seconds_since_heartbeat=round(
                                time.time() - health.last_heartbeat, 1
                            ),
                        )

                        if health.restarts < self.MAX_RESTARTS:
                            logger.info("auto_restarting_agent", role=role)
                            await self.restart_agent(role)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("health_check_error", error=str(e))
