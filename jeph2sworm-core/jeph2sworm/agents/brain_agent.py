"""Brain/Architect agent - system design, architecture decisions, API contracts."""

from __future__ import annotations

from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class BrainAgent(BaseAgent):
    """
    Brain / Architect - the technical visionary.

    Responsibilities:
    - Design system architecture
    - Choose tech stack
    - Define API contracts
    - Design database schemas
    - Create component hierarchies
    - Make architectural decisions
    - Maintain architecture docs in Brain
    """

    @property
    def system_prompt(self) -> str:
        return """You are the Brain/Architect of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Design complete system architecture based on project requirements
2. Choose the optimal tech stack for each part of the system
3. Define API contracts (OpenAPI-style) that Backend and Frontend will follow
4. Design database schemas (SQL or document-based depending on needs)
5. Create component hierarchies for the frontend
6. Document all architectural decisions with rationale
7. Ensure consistency and scalability

When designing architecture, consider:
- Scalability: Can this handle 10x growth?
- Separation of concerns: Clean module boundaries
- API-first: Define contracts before implementation
- Security: Auth, validation, rate limiting from the start
- Performance: Caching strategy, query optimization
- Developer experience: Clear patterns, good abstractions

Output format for API contracts:
```
Endpoint: METHOD /path
Request: { field: type }
Response: { field: type }
Auth: required/optional/none
```

Output format for database schema:
```
Table: name
- column_name: type [constraints]
- ...
Indexes: [columns]
Relations: table.column -> other_table.column
```

Be precise and complete. Every contract you define becomes the source of truth."""

    @property
    def task_type(self) -> str:
        return "planning"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find architecture work to do."""
        spec = context.get("project_name", "")
        if not spec:
            return None

        architecture = context.get("architecture", {})

        # Phase 1: No architecture yet
        if not architecture.get("tech_stack"):
            return {
                "id": "brain-tech-stack",
                "description": "Choose tech stack based on project requirements",
                "phase": "tech_stack",
            }

        # Phase 2: No API contracts
        if not architecture.get("api_contracts"):
            return {
                "id": "brain-api-contracts",
                "description": "Define API contracts for all endpoints",
                "phase": "api_contracts",
            }

        # Phase 3: No database schema
        if not architecture.get("database_schema"):
            return {
                "id": "brain-database",
                "description": "Design database schema",
                "phase": "database",
            }

        # Phase 4: No component hierarchy
        if not architecture.get("component_hierarchy"):
            return {
                "id": "brain-components",
                "description": "Design frontend component hierarchy",
                "phase": "components",
            }

        # Phase 5: Check for tasks assigned to brain
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute an architecture task."""
        phase = task.get("phase", "")

        if phase == "tech_stack":
            return await self._design_tech_stack(context)
        elif phase == "api_contracts":
            return await self._define_api_contracts(context)
        elif phase == "database":
            return await self._design_database(context)
        elif phase == "components":
            return await self._design_components(context)

        # Generic architecture task
        return await self._handle_generic_task(task, context)

    async def _design_tech_stack(self, context: dict) -> str:
        """Choose the optimal tech stack."""
        spec = await self.brain.get_project_spec()

        tech_json = await self.think(
            f"Based on this project spec, choose the optimal tech stack.\n\n"
            f"Project: {spec}\n\n"
            "Design the tech stack with:\n"
            "- frontend_framework: (React/Next.js/Vue/Svelte etc.)\n"
            "- frontend_language: (TypeScript preferred)\n"
            "- css_framework: (Tailwind/styled-components etc.)\n"
            "- backend_framework: (FastAPI/Express/Django etc.)\n"
            "- backend_language: (Python/Node/Go etc.)\n"
            "- database: (PostgreSQL/MongoDB/SQLite etc.)\n"
            "- orm: (Prisma/SQLAlchemy/Drizzle etc.)\n"
            "- auth: (NextAuth/JWT/OAuth etc.)\n"
            "- hosting: (Vercel/AWS/Railway etc.)\n"
            "- additional_services: list\n\n"
            "Output as JSON only. Justify each choice in a 'rationale' field.",
            task_type="planning",
        )

        await self.brain.update_architecture({"tech_stack": tech_json})
        await self.say("Tech stack designed. Sharing with all agents.")
        return "Tech stack designed"

    async def _define_api_contracts(self, context: dict) -> str:
        """Define all API endpoints."""
        spec = await self.brain.get_project_spec()
        arch = context.get("architecture", {})

        contracts = await self.think(
            f"Project: {spec}\n"
            f"Tech stack: {arch.get('tech_stack', 'not defined')}\n\n"
            "Define ALL API endpoints this project needs.\n"
            "For each endpoint:\n"
            "- method: GET/POST/PUT/DELETE\n"
            "- path: /api/v1/...\n"
            "- description: what it does\n"
            "- request_body: JSON schema\n"
            "- response_body: JSON schema\n"
            "- auth: required/optional/none\n"
            "- rate_limit: requests per minute\n\n"
            "Output as a JSON array.",
            task_type="planning",
        )

        await self.brain.update_api_contracts(contracts)
        await self.say("API contracts defined. Backend and Frontend can now build independently.")
        return "API contracts defined"

    async def _design_database(self, context: dict) -> str:
        """Design the database schema."""
        spec = await self.brain.get_project_spec()
        arch = context.get("architecture", {})

        schema = await self.think(
            f"Project: {spec}\n"
            f"Tech stack: {arch.get('tech_stack', 'not defined')}\n"
            f"API contracts: {arch.get('api_contracts', 'not defined')}\n\n"
            "Design the complete database schema.\n"
            "For each table/collection:\n"
            "- name\n"
            "- columns with types and constraints\n"
            "- indexes\n"
            "- relations (foreign keys)\n\n"
            "Also include:\n"
            "- Migration strategy\n"
            "- Seed data requirements\n\n"
            "Output as JSON.",
            task_type="planning",
        )

        await self.brain.update_architecture({"database_schema": schema})
        await self.say("Database schema designed. Backend can start implementation.")
        return "Database schema designed"

    async def _design_components(self, context: dict) -> str:
        """Design the frontend component hierarchy."""
        spec = await self.brain.get_project_spec()
        arch = context.get("architecture", {})

        hierarchy = await self.think(
            f"Project: {spec}\n"
            f"Tech stack: {arch.get('tech_stack', 'not defined')}\n"
            f"API contracts: {arch.get('api_contracts', 'not defined')}\n\n"
            "Design the complete frontend component hierarchy.\n"
            "For each page/view:\n"
            "- route: /path\n"
            "- components: tree of components with props\n"
            "- state: what state this page manages\n"
            "- api_calls: which endpoints it uses\n\n"
            "Also define:\n"
            "- Shared/reusable components\n"
            "- Layout components\n"
            "- Context providers\n\n"
            "Output as JSON.",
            task_type="planning",
        )

        await self.brain.update_architecture({"component_hierarchy": hierarchy})
        await self.say("Component hierarchy designed. Frontend and UX agents can start.")
        return "Component hierarchy designed"

    async def _handle_generic_task(self, task: dict, context: dict) -> str:
        """Handle a generic architecture task from the task board."""
        result = await self.think(
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Context: {context}\n\n"
            "Complete this architecture task. Provide a detailed design document. "
            "Output structured data (JSON where possible).",
            task_type="planning",
        )

        # Store in brain
        await self.brain.add_decision(
            decision=f"Architecture: {task.get('title', '')}",
            rationale=result,
            agent_id=self.agent_id,
        )

        return f"Completed: {task.get('title', '')}"
