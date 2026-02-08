"""Jeph2Sworm entry point - starts the FastAPI server and swarm."""

from __future__ import annotations

import asyncio
import signal
import sys

import structlog
import uvicorn
from fastapi import FastAPI, WebSocket

from jeph2sworm.config import Settings
from jeph2sworm.orchestrator.swarm_manager import SwarmManager
from jeph2sworm.server.middleware import setup_middleware
from jeph2sworm.server.routes import router, set_swarm_manager
from jeph2sworm.server.websocket_server import websocket_endpoint, ws_manager

# ── Structured logging setup ──────────────────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or Settings()

    app = FastAPI(
        title="Jeph2Sworm",
        description="Autonomous AI Development Swarm",
        version="0.1.0",
    )

    # Middleware
    setup_middleware(app)

    # REST routes
    app.include_router(router)

    # WebSocket endpoint
    @app.websocket("/ws/{client_id}")
    async def ws_route(websocket: WebSocket, client_id: str, client_type: str = "vscode"):
        await websocket_endpoint(websocket, client_id, client_type)

    # Swarm lifecycle
    swarm = SwarmManager(settings)

    @app.on_event("startup")
    async def on_startup():
        logger.info("Starting Jeph2Sworm server", host=settings.host, port=settings.port)
        await swarm.initialize()
        set_swarm_manager(swarm)
        # Don't start agents automatically - wait for user to connect and set project
        logger.info("Server ready. Waiting for connections.")

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Shutting down Jeph2Sworm server")
        await swarm.stop()

    # Store references
    app.state.swarm = swarm
    app.state.settings = settings

    return app


def main():
    """CLI entry point."""
    settings = Settings()

    logger.info(
        "Jeph2Sworm starting",
        host=settings.host,
        port=settings.port,
        workspace=str(settings.workspace_dir),
    )

    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        ws="websockets",
    )


if __name__ == "__main__":
    main()
