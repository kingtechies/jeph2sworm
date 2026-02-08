"""Event Logger - Persistent event logging to disk and in-memory ring buffer."""

from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import structlog

from jeph2sworm.events import EventType, SwarmEvent

logger = structlog.get_logger()


class EventLogger:
    """
    Persists SwarmEvents to disk and maintains an in-memory ring buffer
    for fast querying of recent events.

    Used for:
    - Debugging agent behavior
    - Post-session analysis
    - UI event feeds
    - Audit trails
    """

    def __init__(
        self,
        log_dir: str | Path = ".jeph2sworm/events",
        max_in_memory: int = 5000,
    ):
        self.log_dir = Path(log_dir).resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_in_memory = max_in_memory

        self._buffer: Deque[Dict[str, Any]] = deque(maxlen=max_in_memory)
        self._session_id = str(int(time.time()))
        self._log_file = self.log_dir / f"session_{self._session_id}.jsonl"
        self._event_count = 0

    def log(self, event: SwarmEvent) -> None:
        """Log an event to memory and disk."""
        record = {
            "id": self._event_count,
            "type": event.event.value if isinstance(event.event, EventType) else str(event.event),
            "agent": event.source,
            "data": event.data,
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
        }

        # Add to in-memory buffer
        self._buffer.append(record)
        self._event_count += 1

        # Append to disk (JSONL format - one JSON object per line)
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            logger.error("event_log_write_failed", error=str(e))

    def get_recent(
        self,
        count: int = 50,
        event_type: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent events from the in-memory buffer."""
        events = list(self._buffer)

        if event_type:
            events = [e for e in events if e["type"] == event_type]
        if agent:
            events = [e for e in events if e["agent"] == agent]

        return events[-count:]

    def get_by_type(self, event_type: str, count: int = 100) -> List[Dict[str, Any]]:
        """Get events of a specific type."""
        return self.get_recent(count=count, event_type=event_type)

    def get_by_agent(self, agent: str, count: int = 100) -> List[Dict[str, Any]]:
        """Get events from a specific agent."""
        return self.get_recent(count=count, agent=agent)

    def get_errors(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get error events."""
        error_types = {"agent_error", "AGENT_ERROR", "error"}
        return [
            e for e in list(self._buffer)
            if e["type"] in error_types
        ][-count:]

    def search(self, query: str, count: int = 50) -> List[Dict[str, Any]]:
        """Search events by text content."""
        query_lower = query.lower()
        results = []
        for event in reversed(list(self._buffer)):
            data_str = json.dumps(event.get("data", {}), default=str).lower()
            if query_lower in data_str or query_lower in event.get("agent", "").lower():
                results.append(event)
                if len(results) >= count:
                    break
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        type_counts: Dict[str, int] = {}
        agent_counts: Dict[str, int] = {}

        for event in self._buffer:
            t = event["type"]
            a = event["agent"]
            type_counts[t] = type_counts.get(t, 0) + 1
            agent_counts[a] = agent_counts.get(a, 0) + 1

        return {
            "session_id": self._session_id,
            "total_events": self._event_count,
            "in_memory": len(self._buffer),
            "by_type": type_counts,
            "by_agent": agent_counts,
            "log_file": str(self._log_file),
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all event log sessions."""
        sessions = []
        for f in sorted(self.log_dir.glob("session_*.jsonl")):
            sessions.append({
                "session_id": f.stem.replace("session_", ""),
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "created": f.stat().st_mtime,
            })
        return sessions

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Load events from a previous session."""
        session_file = self.log_dir / f"session_{session_id}.jsonl"
        if not session_file.exists():
            return []

        events = []
        with open(session_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events

    def clear(self) -> None:
        """Clear the in-memory buffer."""
        self._buffer.clear()


# Global singleton
event_logger = EventLogger()
