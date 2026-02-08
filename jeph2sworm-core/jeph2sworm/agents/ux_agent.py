"""UX Designer agent - design system, layouts, component specs, branding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class UXAgent(BaseAgent):
    """
    UX Designer - the visual and interaction designer.

    Responsibilities:
    - Create design system (colors, typography, spacing)
    - Design page layouts and wireframes
    - Define component visual specs
    - Create branding assets spec
    - Ensure UI consistency
    - Motion/animation design
    - Accessibility compliance
    """

    @property
    def system_prompt(self) -> str:
        return """You are the UX Designer of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Create a complete design system with colors, typography, spacing, and shadows
2. Design page layouts with exact measurements and responsive breakpoints
3. Define component visual specifications (states, variants, sizing)
4. Establish branding guidelines (logo specs, color palette, tone)
5. Design micro-interactions and animations
6. Ensure WCAG 2.1 AA accessibility compliance
7. Create dark mode variants

Design system output format:
```json
{
  "colors": {
    "primary": {"50": "#...", "100": "#...", ..., "900": "#..."},
    "secondary": {...},
    "neutral": {...},
    "success": "#...",
    "warning": "#...",
    "error": "#...",
    "background": {"light": "#...", "dark": "#..."},
    "text": {"primary": "#...", "secondary": "#...", "disabled": "#..."}
  },
  "typography": {
    "fontFamily": {"heading": "...", "body": "...", "mono": "..."},
    "fontSize": {"xs": "...", "sm": "...", "base": "...", "lg": "...", "xl": "...", "2xl": "...", "3xl": "..."},
    "fontWeight": {"normal": 400, "medium": 500, "semibold": 600, "bold": 700},
    "lineHeight": {"tight": 1.25, "normal": 1.5, "relaxed": 1.75}
  },
  "spacing": {"1": "4px", "2": "8px", "3": "12px", "4": "16px", ...},
  "borderRadius": {"sm": "4px", "md": "8px", "lg": "12px", "full": "9999px"},
  "shadows": {"sm": "...", "md": "...", "lg": "..."},
  "breakpoints": {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"}
}
```

Be opinionated about design. Choose modern, clean aesthetics. Make it beautiful.
Prioritize usability and clarity over decoration."""

    @property
    def task_type(self) -> str:
        return "design"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find design work to do."""
        architecture = context.get("architecture", {})
        spec = context.get("project_name", "")
        if not spec:
            return None

        # Phase 1: Design system
        if not architecture.get("design_system"):
            return {
                "id": "ux-design-system",
                "description": "Create the complete design system",
                "phase": "design_system",
            }

        # Phase 2: Page layouts
        if not architecture.get("page_layouts"):
            return {
                "id": "ux-layouts",
                "description": "Design page layouts and wireframes",
                "phase": "layouts",
            }

        # Phase 3: Component specs
        if not architecture.get("component_specs"):
            return {
                "id": "ux-component-specs",
                "description": "Define component visual specifications",
                "phase": "component_specs",
            }

        # Check assigned tasks
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a design task."""
        phase = task.get("phase", "")

        if phase == "design_system":
            return await self._create_design_system(context)
        elif phase == "layouts":
            return await self._design_layouts(context)
        elif phase == "component_specs":
            return await self._design_components(context)

        return await self._handle_generic_task(task, context)

    async def _create_design_system(self, context: dict) -> str:
        """Create the complete design system."""
        spec = await self.brain.get_project_spec()

        design = await self.think(
            f"Project: {spec}\n\n"
            "Create a complete design system with:\n"
            "1. Color palette (primary, secondary, neutral, semantic colors, dark mode)\n"
            "2. Typography scale (font families, sizes, weights, line heights)\n"
            "3. Spacing scale (4px base unit)\n"
            "4. Border radius values\n"
            "5. Shadow values\n"
            "6. Breakpoints for responsive design\n"
            "7. Z-index scale\n"
            "8. Transition/animation tokens\n\n"
            "Make it modern, clean, and professional.\n"
            "Output as a single JSON object.",
            task_type="design",
        )

        await self.brain.update_architecture({"design_system": design})
        await self.say("Design system created. Frontend can start building.")
        return "Design system created"

    async def _design_layouts(self, context: dict) -> str:
        """Design page layouts."""
        spec = await self.brain.get_project_spec()
        architecture = context.get("architecture", {})

        layouts = await self.think(
            f"Project: {spec}\n"
            f"Component hierarchy: {architecture.get('component_hierarchy', 'not defined')}\n"
            f"Design system: {architecture.get('design_system', 'not defined')}\n\n"
            "Design the layout for every page in the application:\n"
            "- Header/navigation structure\n"
            "- Sidebar (if needed)\n"
            "- Content areas with grid/flex layout\n"
            "- Footer\n"
            "- Mobile layout variations\n\n"
            "For each page, describe:\n"
            "- Layout grid (columns, gutters)\n"
            "- Component placement\n"
            "- Spacing between elements\n"
            "- Responsive behavior at each breakpoint\n\n"
            "Output as JSON.",
            task_type="design",
        )

        await self.brain.update_architecture({"page_layouts": layouts})
        await self.say("Page layouts designed.")
        return "Page layouts designed"

    async def _design_components(self, context: dict) -> str:
        """Define component visual specifications."""
        architecture = context.get("architecture", {})

        specs = await self.think(
            f"Component hierarchy: {architecture.get('component_hierarchy', 'not defined')}\n"
            f"Design system: {architecture.get('design_system', 'not defined')}\n\n"
            "Define visual specs for shared/reusable components:\n"
            "- Button (primary, secondary, ghost, danger variants + sizes)\n"
            "- Input (text, select, checkbox, radio, textarea)\n"
            "- Card (default, elevated, outlined)\n"
            "- Modal/Dialog\n"
            "- Toast/Notification\n"
            "- Table\n"
            "- Navigation (header, sidebar, breadcrumb, tabs)\n"
            "- Loading indicators (spinner, skeleton, progress)\n"
            "- Avatar\n"
            "- Badge\n\n"
            "For each component include:\n"
            "- All visual states (default, hover, focus, active, disabled)\n"
            "- All variants and sizes\n"
            "- Exact CSS values (colors, padding, font, border, shadow)\n"
            "- Dark mode values\n"
            "- Accessibility requirements\n\n"
            "Output as JSON.",
            task_type="design",
        )

        await self.brain.update_architecture({"component_specs": specs})

        # Also generate a Tailwind config or theme file
        workspace = self.brain.data.get("workspace_path", "")
        theme_content = await self.think(
            f"Design system: {architecture.get('design_system', '')}\n\n"
            "Convert this design system into a tailwind.config.ts (or theme.ts) file. "
            "Include all custom colors, fonts, spacing. Output just the file content.",
            task_type="design",
        )

        theme_path = str(Path(workspace) / "output" / "tailwind.config.ts")
        await self.write_code(theme_path, theme_content)

        await self.say("Component specs and theme file created.")
        return "Component specs created"

    async def _handle_generic_task(self, task: dict, context: dict) -> str:
        """Handle a generic design task."""
        result = await self.think(
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            "Complete this design task. Provide detailed visual specifications. "
            "Output structured JSON.",
            task_type="design",
        )

        await self.brain.add_decision(
            decision=f"Design: {task.get('title', '')}",
            rationale=result,
            agent_id=self.agent_id,
        )

        return f"Completed: {task.get('title', '')}"
