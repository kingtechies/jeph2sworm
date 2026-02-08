"""Screenshot - Capture and manage browser screenshots."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()


class Screenshot:
    """
    Captures, stores, and manages browser screenshots.

    Used for:
    - Visual regression testing
    - Progress documentation
    - UX review by the UX agent
    - Bug reproduction evidence
    """

    def __init__(self, output_dir: str = ".jeph2sworm/screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def capture(
        self,
        page: Any,
        name: str = "",
        full_page: bool = True,
        selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Capture a screenshot from a Playwright page.

        Args:
            page: Playwright page object
            name: Screenshot name/label
            full_page: Capture full scrollable page
            selector: CSS selector to capture (element screenshot)

        Returns:
            Dict with path, base64 data, dimensions
        """
        timestamp = int(time.time() * 1000)
        filename = f"{name or 'screenshot'}_{timestamp}.png"
        filepath = self.output_dir / filename

        try:
            if selector:
                element = await page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(filepath))
                else:
                    logger.warning("selector_not_found", selector=selector)
                    await page.screenshot(path=str(filepath), full_page=full_page)
            else:
                await page.screenshot(path=str(filepath), full_page=full_page)

            # Read back as base64 for transmission
            with open(filepath, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode()

            file_size = os.path.getsize(filepath)

            logger.info(
                "screenshot_captured",
                name=name,
                path=str(filepath),
                size_bytes=file_size,
            )

            return {
                "path": str(filepath),
                "filename": filename,
                "base64": b64_data,
                "size_bytes": file_size,
                "timestamp": timestamp,
                "full_page": full_page,
                "selector": selector,
            }

        except Exception as e:
            logger.error("screenshot_failed", name=name, error=str(e))
            return {"error": str(e)}

    async def capture_viewport(self, page: Any, name: str = "") -> Dict[str, Any]:
        """Capture just the visible viewport."""
        return await self.capture(page, name=name, full_page=False)

    async def capture_element(
        self, page: Any, selector: str, name: str = ""
    ) -> Dict[str, Any]:
        """Capture a specific element."""
        return await self.capture(page, name=name, selector=selector)

    def list_screenshots(self) -> list:
        """List all saved screenshots."""
        screenshots = []
        for f in sorted(self.output_dir.glob("*.png")):
            screenshots.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "created": f.stat().st_mtime,
            })
        return screenshots

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Remove screenshots older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for f in self.output_dir.glob("*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        return removed

    def get_latest(self, name_prefix: str = "") -> Optional[Dict[str, Any]]:
        """Get the most recent screenshot, optionally filtered by name prefix."""
        files = sorted(self.output_dir.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files:
            if not name_prefix or f.name.startswith(name_prefix):
                return {
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                }
        return None
