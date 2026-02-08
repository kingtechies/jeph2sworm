"""DevTools Client - Chrome DevTools Protocol integration."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class DevToolsClient:
    """
    Chrome DevTools Protocol (CDP) client for advanced browser inspection.

    Provides access to:
    - Network monitoring (requests, responses, timing)
    - Console log capture
    - Performance metrics
    - DOM inspection
    - JavaScript evaluation
    - Coverage analysis

    Works alongside browser-use for deeper browser interaction.
    """

    def __init__(self):
        self._cdp_session: Any = None
        self._network_logs: List[Dict[str, Any]] = []
        self._console_logs: List[Dict[str, Any]] = []
        self._performance_entries: List[Dict[str, Any]] = []
        self._listeners: Dict[str, List[Callable]] = {}

    async def connect(self, page: Any) -> None:
        """Connect to a Playwright page's CDP session."""
        try:
            self._cdp_session = await page.context.new_cdp_session(page)
            logger.info("cdp_session_connected")
        except Exception as e:
            logger.error("cdp_connect_failed", error=str(e))

    async def enable_network_monitoring(self) -> None:
        """Enable network request/response logging."""
        if not self._cdp_session:
            return

        await self._cdp_session.send("Network.enable")

        self._cdp_session.on("Network.requestWillBeSent", self._on_request)
        self._cdp_session.on("Network.responseReceived", self._on_response)
        self._cdp_session.on("Network.loadingFailed", self._on_loading_failed)

        logger.info("network_monitoring_enabled")

    async def enable_console_capture(self) -> None:
        """Enable console log capture."""
        if not self._cdp_session:
            return

        await self._cdp_session.send("Runtime.enable")
        self._cdp_session.on("Runtime.consoleAPICalled", self._on_console)

        logger.info("console_capture_enabled")

    async def enable_performance(self) -> None:
        """Enable performance monitoring."""
        if not self._cdp_session:
            return

        await self._cdp_session.send("Performance.enable")
        logger.info("performance_monitoring_enabled")

    async def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        if not self._cdp_session:
            return {}

        try:
            result = await self._cdp_session.send("Performance.getMetrics")
            return {m["name"]: m["value"] for m in result.get("metrics", [])}
        except Exception as e:
            logger.error("performance_metrics_failed", error=str(e))
            return {}

    async def evaluate_js(self, expression: str) -> Any:
        """Evaluate JavaScript in the page context."""
        if not self._cdp_session:
            return None

        try:
            result = await self._cdp_session.send(
                "Runtime.evaluate",
                {"expression": expression, "returnByValue": True},
            )
            return result.get("result", {}).get("value")
        except Exception as e:
            logger.error("js_eval_failed", error=str(e))
            return None

    async def get_dom_snapshot(self) -> Dict[str, Any]:
        """Get a DOM snapshot."""
        if not self._cdp_session:
            return {}

        try:
            result = await self._cdp_session.send(
                "DOMSnapshot.captureSnapshot",
                {"computedStyles": ["display", "visibility", "opacity"]},
            )
            return result
        except Exception as e:
            logger.error("dom_snapshot_failed", error=str(e))
            return {}

    async def get_coverage(self) -> Dict[str, Any]:
        """Get JS and CSS coverage data."""
        if not self._cdp_session:
            return {}

        try:
            await self._cdp_session.send("Profiler.enable")
            await self._cdp_session.send("Profiler.startPreciseCoverage", {
                "callCount": True,
                "detailed": True,
            })

            # Give time for coverage to accumulate
            await asyncio.sleep(1)

            result = await self._cdp_session.send("Profiler.takePreciseCoverage")
            await self._cdp_session.send("Profiler.stopPreciseCoverage")

            return result
        except Exception as e:
            logger.error("coverage_failed", error=str(e))
            return {}

    def get_network_logs(self, status_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get captured network logs, optionally filtered by status code."""
        if status_filter:
            return [
                log for log in self._network_logs
                if log.get("status") == status_filter
            ]
        return list(self._network_logs)

    def get_console_logs(self, level_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get captured console logs, optionally filtered by level."""
        if level_filter:
            return [
                log for log in self._console_logs
                if log.get("type") == level_filter
            ]
        return list(self._console_logs)

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all errors (network failures + console errors)."""
        errors = []
        errors.extend([
            log for log in self._network_logs
            if log.get("status", 200) >= 400 or log.get("failed")
        ])
        errors.extend([
            log for log in self._console_logs
            if log.get("type") == "error"
        ])
        return errors

    def clear_logs(self) -> None:
        """Clear all captured logs."""
        self._network_logs.clear()
        self._console_logs.clear()

    async def disconnect(self) -> None:
        """Disconnect the CDP session."""
        if self._cdp_session:
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None

    # ── CDP Event Handlers ─────────────────────────────────

    def _on_request(self, params: Dict[str, Any]) -> None:
        """Handle network request event."""
        request = params.get("request", {})
        self._network_logs.append({
            "request_id": params.get("requestId"),
            "url": request.get("url"),
            "method": request.get("method"),
            "type": params.get("type"),
            "timestamp": params.get("timestamp"),
        })

    def _on_response(self, params: Dict[str, Any]) -> None:
        """Handle network response event."""
        response = params.get("response", {})
        request_id = params.get("requestId")

        # Update the matching request entry
        for log in reversed(self._network_logs):
            if log.get("request_id") == request_id:
                log["status"] = response.get("status")
                log["headers"] = response.get("headers", {})
                log["mime_type"] = response.get("mimeType")
                break

    def _on_loading_failed(self, params: Dict[str, Any]) -> None:
        """Handle network loading failure."""
        request_id = params.get("requestId")
        for log in reversed(self._network_logs):
            if log.get("request_id") == request_id:
                log["failed"] = True
                log["error_text"] = params.get("errorText")
                break

    def _on_console(self, params: Dict[str, Any]) -> None:
        """Handle console API call."""
        args = params.get("args", [])
        text_parts = []
        for arg in args:
            if arg.get("type") == "string":
                text_parts.append(arg.get("value", ""))
            elif arg.get("description"):
                text_parts.append(arg["description"])

        self._console_logs.append({
            "type": params.get("type", "log"),
            "text": " ".join(text_parts),
            "timestamp": params.get("timestamp"),
        })
