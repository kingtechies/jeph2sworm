"""Backend Developer agent - APIs, database, business logic, auth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class BackendAgent(BaseAgent):
    """
    Backend Developer - the server-side builder.

    Responsibilities:
    - Implement API endpoints per contracts
    - Set up database models and migrations
    - Implement authentication and authorization
    - Write business logic
    - Create middleware (CORS, rate limiting, logging)
    - Set up WebSocket handlers if needed
    """

    @property
    def system_prompt(self) -> str:
        return """You are the Backend Developer of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Implement API endpoints exactly matching the API contracts defined by the Brain
2. Set up database models, migrations, and seed data
3. Implement authentication (JWT, OAuth, sessions as specified)
4. Write clean, well-structured business logic
5. Create middleware for CORS, rate limiting, error handling, logging
6. Implement WebSocket handlers if needed
7. Write input validation for all endpoints

Coding standards:
- Follow the language's best practices and idioms
- Type everything (TypeScript strict mode, Python type hints)
- Use dependency injection where appropriate
- Handle errors gracefully with proper HTTP status codes
- Log important operations with structured logging
- Never hardcode secrets - always use environment variables
- Write docstrings/comments for complex logic
- Keep functions small and focused (< 50 lines)

When writing code, output the complete file content. Include:
- All imports at the top
- Type definitions
- The implementation
- Export statements

Always follow the API contracts exactly. If a contract seems wrong, flag it but implement it anyway."""

    @property
    def task_type(self) -> str:
        return "coding"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find backend work to do."""
        # Need architecture before we can build
        architecture = context.get("architecture", {})
        if not architecture.get("tech_stack"):
            return None

        # Check for assigned tasks
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        # Auto-detect work: set up project structure
        if not architecture.get("_backend_initialized"):
            return {
                "id": "be-init",
                "description": "Initialize backend project structure",
                "phase": "init",
            }

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a backend development task."""
        phase = task.get("phase", "")

        if phase == "init":
            return await self._initialize_project(context)

        # Generic dev task
        return await self._implement_task(task, context)

    async def _initialize_project(self, context: dict) -> str:
        """Set up the backend project structure."""
        architecture = context.get("architecture", {})
        tech_stack = architecture.get("tech_stack", "{}")

        plan = await self.think(
            f"Tech stack: {tech_stack}\n\n"
            "Generate the initial backend project structure. List every file to create:\n"
            "- Package config (package.json / pyproject.toml)\n"
            "- Entry point (main.ts / main.py)\n"
            "- Router setup\n"
            "- Database connection\n"
            "- Auth middleware\n"
            "- Error handler\n"
            "- Environment config\n"
            "- .env.example\n\n"
            "For each file, include the full path relative to the project root "
            "and the complete file content.\n"
            "Output as JSON array: [{\"path\": \"...\", \"content\": \"...\"}]",
            task_type="coding",
        )

        try:
            # Parse and create files
            if "```" in plan:
                json_str = plan.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                files = json.loads(json_str.strip())
            else:
                files = json.loads(plan.strip())

            workspace = self.brain.data.get("workspace_path", "")
            for f in files:
                filepath = str(Path(workspace) / "output" / f["path"])
                await self.write_code(filepath, f["content"])

            await self.brain.update_architecture({"_backend_initialized": True})
            return f"Backend initialized with {len(files)} files"

        except (json.JSONDecodeError, KeyError):
            return "Backend structure planned (needs manual file creation)"

    async def _implement_task(self, task: dict, context: dict) -> str:
        """Implement a backend development task."""
        architecture = context.get("architecture", {})

        prompt = (
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Tech stack: {architecture.get('tech_stack', 'not specified')}\n"
            f"API contracts: {architecture.get('api_contracts', 'not specified')}\n"
            f"Database schema: {architecture.get('database_schema', 'not specified')}\n\n"
            "Implement this task. Output the complete file(s) needed.\n"
            "For each file, format as:\n"
            "FILE: relative/path/to/file.ext\n"
            "```\n"
            "complete file content\n"
            "```\n\n"
            "Make sure to follow the API contracts exactly."
        )

        implementation = await self.think(prompt, task_type="coding")

        # Parse and write files
        files_written = await self._parse_and_write_files(implementation, context)

        await self.brain.complete_task(
            task.get("id", ""), self.agent_id, f"Implemented: {task.get('title', '')}"
        )

        return f"Implemented {task.get('title', '')} ({files_written} files)"

    async def _parse_and_write_files(self, response: str, context: dict) -> int:
        """Parse LLM response and write code files."""
        files_written = 0
        workspace = self.brain.data.get("workspace_path", "")

        # Parse FILE: path format
        parts = response.split("FILE: ")
        for part in parts[1:]:
            lines = part.split("\n")
            filepath = lines[0].strip()

            # Find code block
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
