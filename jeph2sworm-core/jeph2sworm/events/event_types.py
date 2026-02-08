"""
Event Types — standalone enum and model definitions for the event system.
Re-exports from events/__init__.py for standalone import convenience.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

import time


class EventType(str, Enum):
    """All event types emitted by the swarm."""

    # Agent lifecycle
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_SPAWNED = "agent_spawned"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    AGENT_HEARTBEAT = "agent_heartbeat"

    # Task events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_FAILED = "task_failed"

    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_BACKUP_CREATED = "file_backup_created"

    # Code events
    API_ENDPOINT_READY = "api_endpoint_ready"
    DESIGN_READY = "design_ready"
    COMPONENT_READY = "component_ready"

    # Testing events
    TEST_RUN_STARTED = "test_run_started"
    TEST_RUN_COMPLETE = "test_run_complete"
    BUG_REPORTED = "bug_reported"
    BUG_FIXED = "bug_fixed"

    # Deployment events
    DEPLOY_STARTED = "deploy_started"
    DEPLOY_STATUS = "deploy_status"
    DEPLOY_COMPLETE = "deploy_complete"

    # Brain events
    BRAIN_UPDATED = "brain_updated"
    DECISION_MADE = "decision_made"

    # User events
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    REQUEST_INPUT = "request_input"

    # Credential events
    CREDENTIAL_CREATED = "credential_created"
    CREDENTIAL_ROTATED = "credential_rotated"

    # System events
    ERROR_OCCURRED = "error_occurred"
    PROGRESS_UPDATE = "progress_update"
    BUILD_COMPLETE = "build_complete"
    SCREENSHOT_CAPTURED = "screenshot_captured"
    RECORDING_READY = "recording_ready"

    # Code events (additional)
    CODE_GENERATED = "code_generated"
    CODE_REVIEWED = "code_reviewed"

    # Testing events (additional)
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"

    # Browser events
    BROWSER_ACTION = "browser_action"
    BROWSER_CONNECTED = "browser_connected"
    BROWSER_DISCONNECTED = "browser_disconnected"

    # System events (additional)
    SYSTEM_READY = "system_ready"
    SESSION_STARTED = "session_started"
    SESSION_STOPPED = "session_stopped"

    # LLM events
    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETE = "llm_call_complete"
    LLM_PROVIDER_SWITCHED = "llm_provider_switched"
    TOKEN_USAGE_UPDATE = "token_usage_update"


class SwarmEvent(BaseModel):
    """A typed event emitted by the swarm system."""

    type: EventType
    agent: str = "system"
    data: Any = None
    timestamp: float = Field(default_factory=time.time)
    event_id: Optional[str] = None


class EventPriority(str, Enum):
    """Priority levels for event processing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Mapping of event types to their default priorities
EVENT_PRIORITIES: dict[EventType, EventPriority] = {
    EventType.ERROR_OCCURRED: EventPriority.CRITICAL,
    EventType.AGENT_ERROR: EventPriority.CRITICAL,
    EventType.BUG_REPORTED: EventPriority.HIGH,
    EventType.TASK_BLOCKED: EventPriority.HIGH,
    EventType.DEPLOY_COMPLETE: EventPriority.HIGH,
    EventType.BUILD_COMPLETE: EventPriority.HIGH,
    EventType.USER_MESSAGE: EventPriority.HIGH,
    EventType.TASK_COMPLETED: EventPriority.NORMAL,
    EventType.FILE_CREATED: EventPriority.NORMAL,
    EventType.FILE_MODIFIED: EventPriority.NORMAL,
    EventType.AGENT_HEARTBEAT: EventPriority.LOW,
    EventType.TOKEN_USAGE_UPDATE: EventPriority.LOW,
    EventType.PROGRESS_UPDATE: EventPriority.LOW,
}
