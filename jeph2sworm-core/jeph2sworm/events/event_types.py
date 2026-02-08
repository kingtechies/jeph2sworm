"""
Event Types — re-exports from events/__init__.py for convenience.
Also provides EventPriority enum and EVENT_PRIORITIES mapping.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

import time

# Re-export the canonical EventType and SwarmEvent from the package
from jeph2sworm.events import EventType, SwarmEvent


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
