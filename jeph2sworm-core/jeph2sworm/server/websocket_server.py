"""WebSocket server - real-time communication with VS Code and Chrome extensions."""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

import structlog
from fastapi import WebSocket, WebSocketDisconnect

from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections from extensions."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._groups: Dict[str, Set[str]] = {
            "vscode": set(),
            "browser": set(),
            "all": set(),
        }
        self._lock = asyncio.Lock()

        # Forward all events to connected clients
        event_bus.subscribe(EventType.AGENT_MESSAGE, self._broadcast_event)
        event_bus.subscribe(EventType.TASK_COMPLETED, self._broadcast_event)
        event_bus.subscribe(EventType.TASK_CREATED, self._broadcast_event)
        event_bus.subscribe(EventType.FILE_CREATED, self._broadcast_event)
        event_bus.subscribe(EventType.FILE_MODIFIED, self._broadcast_event)
        event_bus.subscribe(EventType.CODE_GENERATED, self._broadcast_event)
        event_bus.subscribe(EventType.TEST_PASSED, self._broadcast_event)
        event_bus.subscribe(EventType.TEST_FAILED, self._broadcast_event)
        event_bus.subscribe(EventType.AGENT_ERROR, self._broadcast_event)
        event_bus.subscribe(EventType.SYSTEM_READY, self._broadcast_event)

    async def connect(self, websocket: WebSocket, client_id: str, client_type: str = "vscode") -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        async with self._lock:
            self._connections[client_id] = websocket
            self._groups["all"].add(client_id)
            if client_type in self._groups:
                self._groups[client_type].add(client_id)

        logger.info(f"Client connected: {client_id} ({client_type})")

        # Send current state
        await self._send_initial_state(websocket)

    async def disconnect(self, client_id: str) -> None:
        """Handle client disconnection."""
        async with self._lock:
            self._connections.pop(client_id, None)
            for group in self._groups.values():
                group.discard(client_id)

        logger.info(f"Client disconnected: {client_id}")

    async def send_to(self, client_id: str, message: dict) -> None:
        """Send a message to a specific client."""
        ws = self._connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(client_id)

    async def broadcast(self, message: dict, group: str = "all") -> None:
        """Broadcast a message to all clients in a group."""
        client_ids = list(self._groups.get(group, set()))
        disconnected = []

        for client_id in client_ids:
            ws = self._connections.get(client_id)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(client_id)

        for cid in disconnected:
            await self.disconnect(cid)

    async def _broadcast_event(self, event: dict) -> None:
        """Forward an event bus event to all WebSocket clients."""
        ws_message = {
            "type": "event",
            "event_type": event.get("event_type", ""),
            "source": event.get("source", ""),
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp", ""),
        }
        await self.broadcast(ws_message)

    async def _send_initial_state(self, websocket: WebSocket) -> None:
        """Send the current swarm state to a newly connected client."""
        try:
            await websocket.send_json({
                "type": "initial_state",
                "data": {
                    "connected": True,
                    "message": "Connected to Jeph2Sworm backend",
                },
            })
        except Exception:
            pass

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    def get_stats(self) -> dict:
        return {
            "total_connections": len(self._connections),
            "vscode_connections": len(self._groups["vscode"]),
            "browser_connections": len(self._groups["browser"]),
        }


# Global singleton
ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str, client_type: str = "vscode"):
    """WebSocket endpoint handler for FastAPI."""
    await ws_manager.connect(websocket, client_id, client_type)

    try:
        while True:
            data = await websocket.receive_json()
            await _handle_ws_message(data, client_id)
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await ws_manager.disconnect(client_id)


async def _handle_ws_message(data: dict, client_id: str) -> None:
    """Process an incoming WebSocket message."""
    msg_type = data.get("type", "")

    if msg_type == "user_message":
        # Route user chat messages to swarm
        await event_bus.emit(
            EventType.REQUEST_INPUT,
            source=client_id,
            data={"message": data.get("message", ""), "from": client_id},
        )

    elif msg_type == "command":
        # Handle commands from extension
        await event_bus.emit(
            EventType.SYSTEM_READY,
            source=client_id,
            data={"command": data.get("command", ""), "args": data.get("args", {})},
        )

    elif msg_type == "browser_action":
        # Browser extension actions
        await event_bus.emit(
            EventType.BROWSER_ACTION,
            source=client_id,
            data=data.get("action", {}),
        )

    elif msg_type == "ping":
        ws = ws_manager._connections.get(client_id)
        if ws:
            await ws.send_json({"type": "pong"})
