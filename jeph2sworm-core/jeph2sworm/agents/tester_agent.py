"""Tester agent - test plans, unit/integration/e2e tests, 120-cycle testing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType


class TesterAgent(BaseAgent):
    """
    Tester - the quality assurance agent.

    Responsibilities:
    - Create test plans for every feature
    - Write unit tests for all modules
    - Write integration tests for API endpoints
    - Write E2E tests (browser and mobile)
    - Run tests and report results
    - 120-cycle test philosophy: keep testing until 120 passes
    - Report bugs back to the relevant dev agent
    """

    @property
    def system_prompt(self) -> str:
        return """You are the Tester of Jeph2Sworm, an autonomous AI development swarm.

Your role:
1. Write comprehensive test suites for all code
2. Create test plans before implementation begins
3. Run tests continuously as code is written
4. Report bugs with full reproduction steps
5. Follow the 120-cycle philosophy: test 120 times, catch every bug
6. Write unit, integration, and end-to-end tests

Testing standards:
- Unit tests: Test every function in isolation. Mock dependencies. Edge cases matter.
- Integration tests: Test API endpoints with real database. Test auth flows.
- E2E tests: Use Playwright for browser tests, Maestro for mobile.
- Coverage target: 90%+ line coverage, 80%+ branch coverage.
- Test naming: test_<feature>_<scenario>_<expected_result>

For each test file:
- Arrange: Set up test data and mocks
- Act: Execute the function/endpoint
- Assert: Verify results, side effects, error cases

Bug report format:
```
Bug: [title]
Severity: critical/high/medium/low
Component: [backend/frontend/api]
Steps to reproduce:
1. ...
2. ...
Expected: ...
Actual: ...
Test: [test file and function name]
```

Never mark a feature as complete until all tests pass.
If a test fails, create a bug report and assign it to the responsible agent."""

    @property
    def task_type(self) -> str:
        return "testing"

    async def get_next_task(self, context: dict) -> Optional[dict]:
        """Find testing work to do."""
        architecture = context.get("architecture", {})
        if not architecture.get("tech_stack"):
            return None

        # Check for assigned tasks
        tasks = context.get("my_tasks", [])
        for task in tasks:
            if task.get("status") in ("backlog", "assigned"):
                return task

        # Auto-detect: create test plan
        if not architecture.get("_test_plan_created"):
            return {
                "id": "test-plan",
                "description": "Create comprehensive test plan",
                "phase": "test_plan",
            }

        # Auto-detect: run existing tests
        test_results = context.get("test_results", [])
        running_count = sum(1 for r in test_results if r.get("status") == "running")
        if running_count == 0:
            return {
                "id": "test-run",
                "description": "Run test suite",
                "phase": "run_tests",
            }

        return None

    async def execute_task(self, task: dict, context: dict) -> str:
        """Execute a testing task."""
        phase = task.get("phase", "")

        if phase == "test_plan":
            return await self._create_test_plan(context)
        elif phase == "run_tests":
            return await self._run_tests(context)

        return await self._implement_tests(task, context)

    async def _create_test_plan(self, context: dict) -> str:
        """Create a comprehensive test plan."""
        spec = await self.brain.get_project_spec()
        architecture = context.get("architecture", {})

        plan = await self.think(
            f"Project: {spec}\n"
            f"API contracts: {architecture.get('api_contracts', 'not defined')}\n"
            f"Database schema: {architecture.get('database_schema', 'not defined')}\n"
            f"Tech stack: {architecture.get('tech_stack', 'not defined')}\n\n"
            "Create a comprehensive test plan:\n\n"
            "1. Unit tests:\n"
            "   - List every module/function to test\n"
            "   - List edge cases for each\n\n"
            "2. Integration tests:\n"
            "   - List every API endpoint to test\n"
            "   - List auth flow scenarios\n"
            "   - List database operation scenarios\n\n"
            "3. E2E tests:\n"
            "   - List user flow scenarios\n"
            "   - List critical paths\n"
            "   - List error scenarios\n\n"
            "4. Performance tests:\n"
            "   - Load test scenarios\n"
            "   - Response time requirements\n\n"
            "Output as JSON.\n"
            "Include estimated count of tests per category.",
            task_type="testing",
        )

        await self.brain.update_architecture({"_test_plan_created": True, "test_plan": plan})
        await self.say("Test plan created. Will write tests as code is implemented.")
        return "Test plan created"

    async def _implement_tests(self, task: dict, context: dict) -> str:
        """Write test code for a specific feature."""
        architecture = context.get("architecture", {})

        prompt = (
            f"Task: {task.get('title', '')}\n"
            f"Description: {task.get('description', '')}\n\n"
            f"Tech stack: {architecture.get('tech_stack', 'not specified')}\n"
            f"API contracts: {architecture.get('api_contracts', 'not specified')}\n\n"
            "Write comprehensive tests for this feature:\n"
            "- Unit tests for all functions\n"
            "- Integration tests for API endpoints\n"
            "- Edge cases and error scenarios\n"
            "- Use appropriate testing framework (Jest/Pytest/Vitest)\n\n"
            "For each test file, format as:\n"
            "FILE: relative/path/to/__tests__/feature.test.ts\n"
            "```\ncomplete test file\n```\n\n"
            "Include setup/teardown, mocks, and fixtures."
        )

        tests = await self.think(prompt, task_type="testing")
        files_written = await self._parse_and_write_files(tests, context)

        await self.brain.complete_task(
            task.get("id", ""), self.agent_id, f"Tests written for: {task.get('title', '')}"
        )

        return f"Tests written ({files_written} files)"

    async def _run_tests(self, context: dict) -> str:
        """Run the test suite and report results."""
        architecture = context.get("architecture", {})
        tech = architecture.get("tech_stack", "{}")

        # Determine test command from tech stack
        test_cmd = await self.think(
            f"Tech stack: {tech}\n\n"
            "What is the single command to run all tests for this project? "
            "Just output the command, nothing else. "
            "Example: `npm test` or `pytest` or `pnpm test`",
            task_type="testing",
        )

        test_cmd = test_cmd.strip().strip("`")

        try:
            result = await self.run_command(test_cmd)
            pass_count = result.lower().count("pass")
            fail_count = result.lower().count("fail")

            await self.brain.add_test_result(
                test_name="full_suite",
                status="passed" if fail_count == 0 else "failed",
                details=result,
                agent_id=self.agent_id,
            )

            if fail_count > 0:
                # Report failures as bugs
                await self._report_failures(result, context)
                await self.say(f"Tests: {pass_count} passed, {fail_count} failed. Bug reports filed.")
            else:
                await self.say(f"All tests passed ({pass_count} tests).")

            return f"Tests run: {pass_count} passed, {fail_count} failed"

        except Exception as e:
            await self.say(f"Test run failed: {e}")
            return f"Test run error: {e}"

    async def _report_failures(self, test_output: str, context: dict) -> None:
        """Parse test failures and create bug reports."""
        bugs = await self.think(
            f"Test output:\n{test_output}\n\n"
            "Extract each test failure and create a bug report for each.\n"
            "Output as JSON array with:\n"
            "- title: bug title\n"
            "- severity: critical/high/medium/low\n"
            "- component: backend/frontend\n"
            "- test_name: which test failed\n"
            "- details: error message and expected vs actual",
            task_type="testing",
        )

        try:
            if "```" in bugs:
                json_str = bugs.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                bug_list = json.loads(json_str.strip())
            else:
                bug_list = json.loads(bugs.strip())

            for bug in bug_list:
                await self.brain.add_error(
                    error=bug.get("title", "Test failure"),
                    file_path=bug.get("test_name", ""),
                    agent_id=self.agent_id,
                    details=json.dumps(bug),
                )

        except (json.JSONDecodeError, IndexError):
            await self.brain.add_error(
                error="Test failures detected",
                file_path="test_suite",
                agent_id=self.agent_id,
                details=test_output[:1000],
            )

    async def _parse_and_write_files(self, response: str, context: dict) -> int:
        """Parse LLM response and write test files."""
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
