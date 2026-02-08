"""Browser controller - manages browser instances and actions."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class BrowserController:
    """
    High-level browser controller that wraps browser-use.

    Provides:
    - Browser instance lifecycle management
    - Navigation and interaction
    - Screenshot capture
    - DOM inspection
    - Form filling
    - Page content extraction
    """

    def __init__(self, llm: Any = None):
        self._browser = None
        self._agent = None
        self._context = None
        self._page = None
        self._initialized = False
        self._llm = llm  # LLM instance for browser-use agent

    def set_llm(self, llm: Any) -> None:
        """Set or update the LLM instance used for browser tasks."""
        self._llm = llm

    async def initialize(self) -> None:
        """Initialize the browser with browser-use."""
        if self._initialized:
            return

        try:
            from browser_use import Agent, Browser, BrowserConfig

            config = BrowserConfig(
                headless=True,
                disable_security=False,
            )
            self._browser = Browser(config=config)
            self._initialized = True

            await event_bus.emit(
                EventType.BROWSER_READY,
                source="browser-controller",
                data={"status": "initialized"},
            )

            logger.info("Browser controller initialized")

        except ImportError:
            logger.warning(
                "browser-use not installed. Browser features disabled. "
                "Install with: pip install browser-use"
            )

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._initialized = False
            logger.info("Browser closed")

    async def navigate(self, url: str) -> dict:
        """Navigate to a URL and return page info."""
        if not self._initialized:
            await self.initialize()

        try:
            from browser_use import Agent

            agent = Agent(
                task=f"Navigate to {url} and describe what you see",
                llm=self._llm,
                browser=self._browser,
            )

            result = await agent.run()

            await event_bus.emit(
                EventType.BROWSER_ACTION,
                source="browser-controller",
                data={"action": "navigate", "url": url, "success": True},
            )

            return {"url": url, "success": True, "result": str(result)}

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {"url": url, "success": False, "error": str(e)}

    async def execute_task(self, task: str, llm: Any = None) -> dict:
        """Execute a browser task using browser-use agent."""
        if not self._initialized:
            await self.initialize()

        # Use provided LLM or fall back to the controller's default LLM
        task_llm = llm or self._llm

        try:
            from browser_use import Agent

            agent = Agent(
                task=task,
                llm=task_llm,
                browser=self._browser,
            )

            result = await agent.run()

            await event_bus.emit(
                EventType.BROWSER_ACTION,
                source="browser-controller",
                data={"action": "task", "task": task, "success": True},
            )

            return {"task": task, "success": True, "result": str(result)}

        except Exception as e:
            logger.error(f"Browser task failed: {e}")
            return {"task": task, "success": False, "error": str(e)}

    async def screenshot(self, save_path: Optional[str] = None) -> Optional[bytes]:
        """Take a screenshot of the current page."""
        if not self._initialized or not self._page:
            return None

        try:
            screenshot_bytes = await self._page.screenshot()

            if save_path:
                import aiofiles
                async with aiofiles.open(save_path, "wb") as f:
                    await f.write(screenshot_bytes)

            await event_bus.emit(
                EventType.BROWSER_ACTION,
                source="browser-controller",
                data={"action": "screenshot", "path": save_path},
            )

            return screenshot_bytes

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def get_page_content(self) -> str:
        """Get the text content of the current page."""
        if not self._page:
            return ""

        try:
            return await self._page.content()
        except Exception:
            return ""

    async def fill_form(self, fields: Dict[str, str]) -> bool:
        """Fill a form with the given field values."""
        if not self._initialized:
            return False

        try:
            task = "Fill in the form with these values: " + ", ".join(
                f"{k}: {v}" for k, v in fields.items()
            )

            from browser_use import Agent

            agent = Agent(
                task=task,
                llm=self._llm,
                browser=self._browser,
            )

            await agent.run()
            return True

        except Exception as e:
            logger.error(f"Form fill failed: {e}")
            return False

    async def click_element(self, selector: str) -> bool:
        """Click an element by CSS selector."""
        if not self._page:
            return False

        try:
            await self._page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    async def wait_for(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for an element to appear."""
        if not self._page:
            return False

        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    @property
    def is_initialized(self) -> bool:
        return self._initialized
