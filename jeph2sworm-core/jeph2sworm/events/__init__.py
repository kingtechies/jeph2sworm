"""Event type definitions for the agent swarm."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All event types in the swarm communication protocol."""

    # Agent lifecycle
    AGENT_STATUS_CHANGED = "AGENT_STATUS_CHANGED"
    AGENT_SPAWNED = "AGENT_SPAWNED"
    AGENT_STOPPED = "AGENT_STOPPED"

    # Task management
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_BLOCKED = "TASK_BLOCKED"
    TASK_FAILED = "TASK_FAILED"

    # File operations
    FILE_CREATED = "FILE_CREATED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_LOCKED = "FILE_LOCKED"
    FILE_UNLOCKED = "FILE_UNLOCKED"

    # API contracts
    API_ENDPOINT_READY = "API_ENDPOINT_READY"

    # Design
    DESIGN_READY = "DESIGN_READY"

    # Testing
    TEST_RUN_COMPLETE = "TEST_RUN_COMPLETE"
    BUG_REPORTED = "BUG_REPORTED"
    BUG_FIXED = "BUG_FIXED"

    # Deployment
    DEPLOY_STATUS = "DEPLOY_STATUS"

    # Errors
    ERROR_OCCURRED = "ERROR_OCCURRED"

    # User communication
    USER_MESSAGE = "USER_MESSAGE"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    REQUEST_INPUT = "REQUEST_INPUT"

    # Brain
    BRAIN_UPDATED = "BRAIN_UPDATED"

    # Credentials
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"

    # Progress
    PROGRESS_UPDATE = "PROGRESS_UPDATE"

    # Browser
    SCREENSHOT = "SCREENSHOT"
    RECORDING_READY = "RECORDING_READY"

    # Session
    BUILD_COMPLETE = "BUILD_COMPLETE"
    DEPLOY_COMPLETE = "DEPLOY_COMPLETE"
    START_PROJECT = "START_PROJECT"
    PAUSE_AGENTS = "PAUSE_AGENTS"
    RESUME_AGENTS = "RESUME_AGENTS"
    APPROVE_PLAN = "APPROVE_PLAN"
    MODIFY_PLAN = "MODIFY_PLAN"
    CONNECT_BROWSER = "CONNECT_BROWSER"


class SwarmEvent(BaseModel):
    """A single event in the swarm communication protocol."""

    event: EventType
    source: str  # agent_id or "user" or "system"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(default_factory=dict)
    target: Optional[str] = None  # specific agent_id or None for broadcast

    def to_ws_message(self) -> dict:
        """Serialize for WebSocket transmission."""
        return {
            "event": self.event.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "target": self.target,
        }
