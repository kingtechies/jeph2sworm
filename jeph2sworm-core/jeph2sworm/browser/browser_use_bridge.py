"""Bridge between Jeph2Sworm agents and browser-use library."""

from __future__ import annotations

from typing import Any, Dict, Optional

import structlog

from jeph2sworm.browser.controller import BrowserController
from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.llm.router import LLMRouter

logger = structlog.get_logger()


class BrowserUseBridge:
    """
    Connects the swarm agents to the browser-use library.

    Allows agents to:
    - Research information on the web
    - Test web applications in a real browser
    - Fill forms, click buttons, navigate pages
    - Take screenshots for visual testing
    - Extract data from web pages
    """

    def __init__(self, llm_router: LLMRouter):
        self.controller = BrowserController()
        self.llm_router = llm_router
        self._task_history: list[dict] = []

    async def initialize(self) -> None:
        """Initialize the browser bridge."""
        await self.controller.initialize()

    async def close(self) -> None:
        """Close the browser bridge."""
        await self.controller.close()

    async def research(self, query: str, urls: Optional[list[str]] = None) -> str:
        """Research a topic by browsing the web."""
        task = f"Search for '{query}' and summarize the key findings"
        if urls:
            task = f"Visit {', '.join(urls)} and find information about: {query}"

        result = await self.controller.execute_task(task)
        self._task_history.append({"type": "research", "query": query, "result": result})

        return result.get("result", "No results found")

    async def test_webapp(
        self,
        url: str,
        test_scenarios: list[dict],
    ) -> list[dict]:
        """Run browser-based tests on a web application."""
        results = []

        for scenario in test_scenarios:
            task = (
                f"Go to {url}. "
                f"Test scenario: {scenario.get('name', '')}. "
                f"Steps: {scenario.get('steps', '')}. "
                f"Expected result: {scenario.get('expected', '')}."
            )

            result = await self.controller.execute_task(task)
            results.append({
                "scenario": scenario.get("name", ""),
                "passed": result.get("success", False),
                "details": result.get("result", ""),
            })

            await event_bus.emit(
                EventType.TEST_PASSED if result.get("success") else EventType.TEST_FAILED,
                source="browser-bridge",
                data={
                    "test_name": scenario.get("name", ""),
                    "type": "e2e",
                    "details": result,
                },
            )

        return results

    async def extract_data(self, url: str, what: str) -> str:
        """Extract specific data from a web page."""
        task = f"Go to {url} and extract: {what}. Return the raw data."
        result = await self.controller.execute_task(task)
        return result.get("result", "")

    async def take_visual_snapshot(self, url: str, save_path: str) -> bool:
        """Navigate to a URL and take a screenshot."""
        await self.controller.navigate(url)
        screenshot = await self.controller.screenshot(save_path)
        return screenshot is not None

    async def compare_visual(
        self,
        url: str,
        design_spec: str,
    ) -> dict:
        """Compare a live page against a design specification."""
        # Navigate to the page
        await self.controller.navigate(url)

        # Get page content for comparison
        content = await self.controller.get_page_content()

        # Use LLM to compare
        comparison = await self.llm_router.complete(
            prompt=(
                f"Compare this web page with the design specification.\n\n"
                f"Page HTML (truncated):\n{content[:3000]}\n\n"
                f"Design spec:\n{design_spec}\n\n"
                "List any discrepancies:\n"
                "- Layout differences\n"
                "- Color mismatches\n"
                "- Typography issues\n"
                "- Missing elements\n"
                "- Extra elements\n\n"
                'Output as JSON: {{"matches": true/false, "issues": [...]}}'
            ),
            provider="anthropic",
            model="claude-sonnet-4-20250514",
        )

        return {"url": url, "comparison": comparison}

    def get_history(self) -> list[dict]:
        """Get the browser task history."""
        return self._task_history
