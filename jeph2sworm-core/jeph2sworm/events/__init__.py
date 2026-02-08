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
    AGENT_ERROR = "AGENT_ERROR"
    AGENT_BLOCKED = "AGENT_BLOCKED"
    AGENT_HEARTBEAT = "AGENT_HEARTBEAT"

    # Task management
    TASK_CREATED = "TASK_CREATED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_STARTED = "TASK_STARTED"
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

    # Code
    CODE_GENERATED = "CODE_GENERATED"

    # Testing
    TEST_RUN_COMPLETE = "TEST_RUN_COMPLETE"
    TEST_PASSED = "TEST_PASSED"
    TEST_FAILED = "TEST_FAILED"
    BUG_REPORTED = "BUG_REPORTED"
    BUG_FIXED = "BUG_FIXED"

    # Deployment
    DEPLOY_STATUS = "DEPLOY_STATUS"
    DEPLOY_COMPLETE = "DEPLOY_COMPLETE"

    # Errors
    ERROR_OCCURRED = "ERROR_OCCURRED"

    # User communication
    USER_MESSAGE = "USER_MESSAGE"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    REQUEST_INPUT = "REQUEST_INPUT"

    # Brain
    BRAIN_UPDATED = "BRAIN_UPDATED"
    DECISION_MADE = "DECISION_MADE"

    # Credentials
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"

    # Progress
    PROGRESS_UPDATE = "PROGRESS_UPDATE"

    # Browser
    SCREENSHOT = "SCREENSHOT"
    SCREENSHOT_CAPTURED = "SCREENSHOT_CAPTURED"
    RECORDING_READY = "RECORDING_READY"
    BROWSER_ACTION = "BROWSER_ACTION"
    BROWSER_CONNECTED = "BROWSER_CONNECTED"
    BROWSER_READY = "BROWSER_READY"

    # System
    SYSTEM_READY = "SYSTEM_READY"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    SESSION_STARTED = "SESSION_STARTED"

    # Session control
    BUILD_COMPLETE = "BUILD_COMPLETE"
    START_PROJECT = "START_PROJECT"
    PAUSE_AGENTS = "PAUSE_AGENTS"
    RESUME_AGENTS = "RESUME_AGENTS"
    APPROVE_PLAN = "APPROVE_PLAN"
    MODIFY_PLAN = "MODIFY_PLAN"
    CONNECT_BROWSER = "CONNECT_BROWSER"

    # Conflicts
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"

    # LLM / Tokens
    TOKEN_USAGE_UPDATE = "TOKEN_USAGE_UPDATE"


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
