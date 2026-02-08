"""Project Manager agent - user communication, planning, task assignment."""

from __future__ import annotations

from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus


class PMAgent(BaseAgent):
    """
    Project Manager - the user-facing agent.

    Responsibilities:
    - Gather project requirements via structured questions
    - Break the project into milestones and tasks
    - Assign tasks to other agents
    - Monitor progress and communicate status
    - Resolve blockers and make scope decisions
    """

    @property
    def system_prompt(self) -> str:
        return """You are the Project Manager of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Gather complete project requirements from the user through structured questions
2. Break the project into clear milestones with specific tasks
3. Assign tasks to the appropriate agent roles (backend, frontend, ux, tester, devops)
4. Monitor progress and provide status updates
5. Resolve scope questions and blockers

When gathering requirements, ask about:
- Project name and description
- Target audience
- Core features (prioritized list)
- Tech stack preferences (or let the Brain decide)
- Design style and branding
- Authentication needs
- Payment integration needs
- Third-party integrations
- Deployment preferences
- Logo and brand colors

Be thorough but efficient. Group related questions. Don't ask one question at a time.

When creating tasks, output them as a JSON array with:
- id: unique task identifier
- title: short description
- description: detailed requirements
- assigned_to: agent role (backend/frontend/ux/tester/devops)
- priority: high/medium/low
- dependencies: list of task ids this depends on

Always be direct and professional. No fluff. Get the job done."""

    @property
    def task_type(self) -> str:
        return "planning"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Determine what PM needs to do next."""
        spec = context.get("project_name", "")
        conversation = context.get("conversation_history", [])

        # Phase 1: No project yet — gather requirements
        if not spec:
            return {
                "id": "pm-gather-requirements",
                "description": "Gather project requirements from user",
                "phase": "requirements",
            }

        # Phase 2: Project defined but no tasks created
        board = context.get("task_board_summary", {})
        total_tasks = sum(board.values())
        if total_tasks == 0:
            return {
                "id": "pm-create-tasks",
                "description": "Break project into tasks and assign to agents",
                "phase": "planning",
            }

        # Phase 3: Monitor progress
        if board.get("in_progress", 0) > 0 or board.get("backlog", 0) > 0:
            return {
                "id": "pm-monitor",
                "description": "Monitor progress and check for blockers",
                "phase": "monitoring",
            }

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a PM task."""
        phase = task.get("phase", "")

        if phase == "requirements":
            return await self._gather_requirements(context)
        elif phase == "planning":
            return await self._create_project_plan(context)
        elif phase == "monitoring":
            return await self._monitor_progress(context)

        return "No action needed"

    async def _gather_requirements(self, context: dict) -> str:
        """Ask the user structured questions about their project."""
        questions = await self.think(
            "The user wants to start a new project. Generate a set of 10 structured "
            "questions to gather all requirements needed to build the project. "
            "Cover: name, description, features, tech stack, design, auth, payments, "
            "integrations, deployment, and branding. Format as a numbered list."
        )

        await self.say(questions)

        await event_bus.emit(
            EventType.REQUEST_INPUT,
            source=self.agent_id,
            data={"prompt": questions, "phase": "requirements"},
        )

        return "Requirements questions sent to user"

    async def _create_project_plan(self, context: dict) -> str:
        """Create tasks from the project spec and assign to agents."""
        spec = await self.brain.get_project_spec()

        plan_prompt = f"""Based on this project specification, create a detailed task breakdown.

Project: {spec}

Create tasks for these agents:
- brain: Architecture, tech stack, API contracts, database schema
- backend: API endpoints, database, auth, business logic
- frontend: UI components, pages, state management, routing
- ux: Design system, layouts, component specs, branding
- tester: Test plans, unit/integration/e2e tests
- devops: Docker, CI/CD, deployment, environment setup

Output a JSON array of tasks. Each task has:
- "id": string (e.g., "be-001")
- "title": string
- "description": string (detailed requirements)
- "assigned_to": string (agent role)
- "priority": "high" | "medium" | "low"
- "dependencies": list of task IDs

Create at least 20 tasks covering the full project. Prioritize correctly.
Only output the JSON array, nothing else."""

        plan_json = await self.think(plan_prompt, task_type="planning")

        # Parse and add tasks to Brain
        import json
        try:
            # Extract JSON from response
            json_str = plan_json
            if "```" in json_str:
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            tasks = json.loads(json_str.strip())

            for task in tasks:
                await self.brain.add_task(task, status="backlog", agent_id=self.agent_id)

            await self.say(f"Project plan created with {len(tasks)} tasks. Swarm activated.")
            return f"Created {len(tasks)} tasks"

        except (json.JSONDecodeError, IndexError):
            await self.say("Plan created. Assigning tasks to the team.")
            return "Plan created (manual parse needed)"

    async def _monitor_progress(self, context: dict) -> str:
        """Check progress and report to user."""
        board = context.get("task_board_summary", {})
        agents = context.get("agent_states", {})

        status = f"Progress: {board.get('done', 0)} done, {board.get('in_progress', 0)} in progress, {board.get('backlog', 0)} remaining"
        await self.say(status)
        return status

    async def handle_user_message(self, message: str) -> str:
        """Process a direct message from the user."""
        await self.brain.add_message("user", message)

        response = await self.think(
            f"The user said: {message}\n\n"
            "Respond appropriately. If they're answering project questions, "
            "consolidate their answers. If they're asking about progress, "
            "check the task board. Be direct and helpful."
        )

        await self.brain.add_message("assistant", response, self.agent_id)
        await self.say(response)
        return response
