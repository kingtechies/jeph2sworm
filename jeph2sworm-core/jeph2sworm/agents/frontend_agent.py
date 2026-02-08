"""Frontend Developer agent - UI components, pages, state management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class FrontendAgent(BaseAgent):
    """
    Frontend Developer - the UI builder.

    Responsibilities:
    - Implement UI components per design specs from UX
    - Build pages and routing
    - Implement state management
    - Connect to backend APIs per contracts
    - Handle client-side validation
    - Implement responsive design
    - Animations and transitions
    """

    @property
    def system_prompt(self) -> str:
        return """You are the Frontend Developer of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Build UI components exactly matching the UX agent's designs
2. Implement pages with proper routing (file-based or config-based)
3. Set up state management (React Context, Zustand, Redux, etc.)
4. Connect to backend APIs following the Brain's API contracts
5. Handle loading states, error states, and empty states
6. Implement responsive design (mobile-first)
7. Add smooth animations and transitions
8. Ensure accessibility (ARIA labels, keyboard navigation, focus management)

Coding standards:
- TypeScript strict mode (no 'any' types)
- Functional components with hooks
- Props interface for every component
- CSS-in-JS or Tailwind as specified by tech stack
- Client-side form validation mirroring server-side rules
- Optimistic updates where appropriate
- Lazy loading for routes and heavy components
- Image optimization
- SEO meta tags for public pages

Component structure:
```
ComponentName/
  index.tsx       - main component
  styles.ts       - styled-components (if used)
  types.ts        - TypeScript interfaces
  hooks.ts        - custom hooks
  utils.ts        - helper functions
```

When implementing, focus on:
- Pixel-perfect matching of design specs
- Smooth user experience (transitions, loading states)
- Error boundary implementation
- Dark mode support when specified"""

    @property
    def task_type(self) -> str:
        return "coding"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find frontend work to do."""
        architecture = context.get("architecture", {})
        if not architecture.get("tech_stack"):
            return None

        # Check for assigned tasks
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        # Auto-detect: initialize frontend project
        if not architecture.get("_frontend_initialized"):
            return {
                "id": "fe-init",
                "description": "Initialize frontend project structure",
                "phase": "init",
            }

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a frontend development task."""
        phase = task.get("phase", "")

        if phase == "init":
            return await self._initialize_project(context)

        return await self._implement_task(task, context)

    async def _initialize_project(self, context: dict) -> str:
        """Set up the frontend project structure."""
        architecture = context.get("architecture", {})
        tech_stack = architecture.get("tech_stack", "{}")

        plan = await self.think(
            f"Tech stack: {tech_stack}\n\n"
            "Generate the initial frontend project structure:\n"
            "- Package config (package.json with all dependencies)\n"
            "- TypeScript config (tsconfig.json)\n"
            "- Entry point (main.tsx / _app.tsx)\n"
            "- Layout component\n"
            "- Router setup\n"
            "- API client (axios/fetch wrapper)\n"
            "- Theme/design tokens\n"
            "- Global styles\n"
            "- Example page component\n\n"
            "Output as JSON array: [{\"path\": \"...\", \"content\": \"...\"}]",
            task_type="coding",
        )

        try:
            if "```" in plan:
                json_str = plan.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                files = json.loads(json_str.strip())
            else:
                files = json.loads(plan.strip())

            workspace = self.brain.data.get("workspace_path", "")
            for f in files:
                full_path = str(Path(workspace) / "output" / f["path"])
                await self.write_code(full_path, f["content"])

            await self.brain.update_architecture({"_frontend_initialized": True})
            return f"Frontend initialized with {len(files)} files"

        except (json.JSONDecodeError, KeyError):
            return "Frontend structure planned"

    async def _implement_task(self, task: dict, context: dict) -> str:
        """Implement a frontend component or feature."""
        architecture = context.get("architecture", {})
        ux_specs = architecture.get("design_system", {})

        prompt = (
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Tech stack: {architecture.get('tech_stack', 'not specified')}\n"
            f"API contracts: {architecture.get('api_contracts', 'not specified')}\n"
            f"Component hierarchy: {architecture.get('component_hierarchy', 'not specified')}\n"
            f"Design system: {ux_specs}\n\n"
            "Implement this frontend task. Include:\n"
            "- All TypeScript interfaces\n"
            "- Component implementation with hooks\n"
            "- Styling (Tailwind classes or styled-components)\n"
            "- API integration\n"
            "- Loading/error/empty states\n"
            "- Responsive design\n\n"
            "For each file, format as:\n"
            "FILE: relative/path/to/file.ext\n"
            "```typescript\ncomplete file content\n```"
        )

        implementation = await self.think(prompt, task_type="coding")
        files_written = await self._parse_and_write_files(implementation, context)

        await self.brain.complete_task(
            task.get("id", ""), self.agent_id, f"Implemented: {task.get('title', '')}"
        )

        return f"Implemented {task.get('title', '')} ({files_written} files)"

    async def _parse_and_write_files(self, response: str, context: dict) -> int:
        """Parse LLM response and write code files."""
        files_written = 0
        workspace = self.brain.data.get("workspace_path", "")

        parts = response.split("FILE: ")
        for part in parts[1:]:
            lines = part.split("\n")
            filepath = lines[0].strip()

            code_start = None
            code_end = None
            for i, line in enumerate(lines[1:], 1):
                if line.startswith("```") and code_start is None:
                    code_start = i + 1
                elif line.startswith("```") and code_start is not None:
                    code_end = i
                    break

            if code_start and code_end:
                content = "\n".join(lines[code_start:code_end])
                full_path = str(Path(workspace) / "output" / filepath)
                await self.write_code(full_path, content)
                files_written += 1

        return files_written
