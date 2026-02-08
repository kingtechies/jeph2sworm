"""Central event bus for agent-to-agent and agent-to-UI communication."""

from __future__ import annotations

import asyncio
import structlog
from collections import defaultdict
from typing import Any, Callable, Coroutine, Optional

from jeph2sworm.events import EventType, SwarmEvent

logger = structlog.get_logger()

# Type alias for event handlers
EventHandler = Callable[[SwarmEvent], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus for the swarm.

    All agents publish events here. All agents and the UI subscribe to events.
    Events are typed, logged, and can be filtered per-subscriber.
    """

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._global_subscribers: list[EventHandler] = []
        self._event_log: list[SwarmEvent] = []
        self._lock = asyncio.Lock()
        self._ws_clients: list[Any] = []  # WebSocket connections for UI

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to ALL events (used by UI feed and logger)."""
        self._global_subscribers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from a specific event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Unsubscribe from global events."""
        if handler in self._global_subscribers:
            self._global_subscribers.remove(handler)

    def register_ws_client(self, ws: Any) -> None:
        """Register a WebSocket client to receive all events."""
        self._ws_clients.append(ws)

    def remove_ws_client(self, ws: Any) -> None:
        """Remove a WebSocket client."""
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    async def publish(self, event: SwarmEvent) -> None:
        """Publish an event to all relevant subscribers."""
        async with self._lock:
            self._event_log.append(event)

        await logger.ainfo(
            "event_published",
            event=event.event.value,
            source=event.source,
            target=event.target,
        )

        # Notify specific subscribers
        handlers = self._subscribers.get(event.event, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                await logger.aerror(
                    "event_handler_error",
                    event=event.event.value,
                    error=str(e),
                )

        # Notify global subscribers
        for handler in self._global_subscribers:
            try:
                await handler(event)
            except Exception as e:
                await logger.aerror(
                    "global_handler_error",
                    event=event.event.value,
                    error=str(e),
                )

        # Forward to WebSocket clients (VS Code extension, Chrome extension)
        message = event.to_ws_message()
        dead_clients = []
        for ws in self._ws_clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead_clients.append(ws)
        for ws in dead_clients:
            self._ws_clients.remove(ws)

    async def emit(
        self,
        event_type: EventType,
        source: str,
        data: dict[str, Any] | None = None,
        target: str | None = None,
    ) -> SwarmEvent:
        """Convenience method to create and publish an event."""
        event = SwarmEvent(
            event=event_type,
            source=source,
            data=data or {},
            target=target,
        )
        await self.publish(event)
        return event

    def get_event_log(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> list[SwarmEvent]:
        """Get recent events, optionally filtered."""
        events = self._event_log
        if event_type:
            events = [e for e in events if e.event == event_type]
        if source:
            events = [e for e in events if e.source == source]
        return events[-limit:]

    def clear_log(self) -> None:
        """Clear the event log."""
        self._event_log.clear()


# Global singleton
event_bus = EventBus()
