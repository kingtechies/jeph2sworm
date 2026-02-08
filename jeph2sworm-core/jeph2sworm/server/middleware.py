"""FastAPI middleware - CORS, logging, error handling."""

from __future__ import annotations

import json
import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI app."""

    # CORS - allow VS Code extension and Chrome extension
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )

        response = await call_next(request)
        elapsed = (time.monotonic() - start) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed, 2),
            request_id=request_id,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed:.2f}ms"
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return clean error responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception(
                "unhandled_error",
                path=request.url.path,
                error=str(exc),
            )
            return Response(
                content=json.dumps({"error": type(exc).__name__, "detail": str(exc)}),
                status_code=500,
                media_type="application/json",
            )
