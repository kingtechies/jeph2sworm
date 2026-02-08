"""DevOps agent - Docker, CI/CD, deployment, environment setup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class DevOpsAgent(BaseAgent):
    """
    DevOps - the infrastructure and deployment agent.

    Responsibilities:
    - Create Dockerfiles and docker-compose
    - Set up CI/CD pipelines (GitHub Actions)
    - Configure deployment targets
    - Manage environment variables
    - Set up monitoring and logging
    - Database provisioning
    - SSL/domain configuration
    """

    @property
    def system_prompt(self) -> str:
        return """You are the DevOps Engineer of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Create Docker configurations for development and production
2. Set up CI/CD pipelines with GitHub Actions
3. Configure deployment to the specified hosting platform
4. Manage environment variables and secrets
5. Set up database provisioning and migrations
6. Configure SSL, domains, and CDN
7. Implement monitoring, logging, and alerting
8. Security hardening (CSP, CORS, rate limiting)

Standards:
- Multi-stage Docker builds for smaller images
- Docker Compose for local development with hot reload
- GitHub Actions with proper caching and parallel jobs
- Environment-specific configs (dev, staging, prod)
- Secrets managed via GitHub Secrets or vault
- Health check endpoints
- Log aggregation setup
- Auto-scaling configuration where applicable

Docker best practices:
- Use official base images with specific version tags
- Run as non-root user
- Multi-stage builds
- .dockerignore for small build context
- Health checks in Dockerfile
- Proper signal handling (exec form CMD)

CI/CD pipeline stages:
1. Lint and type check
2. Unit tests (parallel)
3. Build
4. Integration tests
5. Security scan
6. Deploy to staging
7. E2E tests on staging
8. Deploy to production (manual approval)

Never hardcode secrets. Use environment variables with sensible defaults for development."""

    @property
    def task_type(self) -> str:
        return "coding"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find DevOps work to do."""
        architecture = context.get("architecture", {})
        if not architecture.get("tech_stack"):
            return None

        # Check assigned tasks
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        # Auto-detect work
        if not architecture.get("_devops_initialized"):
            return {
                "id": "devops-init",
                "description": "Set up Docker, CI/CD, and deployment configs",
                "phase": "init",
            }

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a DevOps task."""
        phase = task.get("phase", "")

        if phase == "init":
            return await self._initialize_infrastructure(context)

        return await self._implement_task(task, context)

    async def _initialize_infrastructure(self, context: dict) -> str:
        """Set up all DevOps infrastructure."""
        architecture = context.get("architecture", {})
        tech_stack = architecture.get("tech_stack", "{}")

        infra = await self.think(
            f"Tech stack: {tech_stack}\n\n"
            "Create all DevOps configuration files:\n\n"
            "1. Dockerfile (multi-stage, production-ready)\n"
            "2. Dockerfile.dev (development with hot reload)\n"
            "3. docker-compose.yml (full local dev environment)\n"
            "4. docker-compose.prod.yml (production overrides)\n"
            "5. .dockerignore\n"
            "6. .github/workflows/ci.yml (lint, test, build)\n"
            "7. .github/workflows/deploy.yml (staging + production)\n"
            "8. .env.example (all required env vars with descriptions)\n"
            "9. nginx.conf (if applicable)\n"
            "10. Makefile (common commands)\n\n"
            "Output as JSON array: [{\"path\": \"...\", \"content\": \"...\"}]\n"
            "Include all file contents. Be thorough.",
            task_type="coding",
        )

        try:
            if "```" in infra:
                json_str = infra.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                files = json.loads(json_str.strip())
            else:
                files = json.loads(infra.strip())

            workspace = self.brain.data.get("workspace_path", "")
            for f in files:
                full_path = str(Path(workspace) / "output" / f["path"])
                await self.write_code(full_path, f["content"])

            await self.brain.update_architecture({"_devops_initialized": True})
            await self.say(f"Infrastructure configured with {len(files)} files.")
            return f"DevOps initialized with {len(files)} files"

        except (json.JSONDecodeError, KeyError):
            return "Infrastructure planned"

    async def _implement_task(self, task: dict, context: dict) -> str:
        """Implement a specific DevOps task."""
        architecture = context.get("architecture", {})

        prompt = (
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Tech stack: {architecture.get('tech_stack', 'not specified')}\n\n"
            "Implement this DevOps task. Include:\n"
            "- All configuration files needed\n"
            "- Shell scripts if required\n"
            "- Documentation for manual steps\n\n"
            "For each file, format as:\n"
            "FILE: relative/path/to/file\n"
            "```\ncomplete file content\n```"
        )

        implementation = await self.think(prompt, task_type="coding")
        files_written = await self._parse_and_write_files(implementation, context)

        await self.brain.complete_task(
            task.get("id", ""), self.agent_id, f"Implemented: {task.get('title', '')}"
        )

        return f"Implemented {task.get('title', '')} ({files_written} files)"

    async def _setup_credentials(self, context: dict) -> str:
        """Set up secure credential management."""
        from jeph2sworm.tools.credential_generator import AiEnvManager

        workspace = self.brain.data.get("workspace_path", "")
        env_manager = AiEnvManager(workspace)

        await env_manager.initialize()

        # Generate standard credentials
        spec = await self.brain.get_project_spec()
        creds_needed = await self.think(
            f"Project: {spec}\n\n"
            "List all credentials/secrets this project needs as a JSON array:\n"
            "[{\"name\": \"ENV_VAR_NAME\", \"description\": \"what it's for\", \"auto_generate\": true/false}]\n"
            "Include: database passwords, JWT secrets, API keys placeholders, etc.\n"
            "Set auto_generate=true for passwords/secrets, false for API keys users must provide.",
            task_type="coding",
        )

        try:
            if "```" in creds_needed:
                json_str = creds_needed.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                creds = json.loads(json_str.strip())
            else:
                creds = json.loads(creds_needed.strip())

            for cred in creds:
                await env_manager.set_credential(
                    key=cred["name"],
                    description=cred.get("description", ""),
                    auto_generate=cred.get("auto_generate", False),
                )

            return f"Credentials configured ({len(creds)} entries)"

        except (json.JSONDecodeError, KeyError):
            return "Credential setup needs manual configuration"

    async def _parse_and_write_files(self, response: str, context: dict) -> int:
        """Parse LLM response and write files."""
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
