"""Tester agent - test plans, unit/integration/e2e tests, 120-cycle testing."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from jeph2sworm.agents.base_agent import AgentRole, BaseAgent
from jeph2sworm.events import EventType

if TYPE_CHECKING:
    from jeph2sworm.browser.browser_use_bridge import BrowserUseBridge


@dataclass
class CycleTestResult:
    """Result of a single test cycle."""
    
    cycle: int
    passed: bool
    duration_ms: float
    output: str
    timestamp: float = field(default_factory=time.time)


@dataclass 
class CycleTestReport:
    """Aggregate report for 120-cycle test run."""
    
    total_cycles: int
    passed_cycles: int
    failed_cycles: int
    pass_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    failures: list[CycleTestResult]
    start_time: float
    end_time: float
    test_command: str


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
        elif phase == "run_120_cycles":
            test_cmd = task.get("test_command")
            cycles = task.get("cycles", 120)
            stop_on_failure = task.get("stop_on_failure", False)
            report = await self.run_120_cycles(
                context, 
                test_command=test_cmd,
                cycles=cycles,
                stop_on_failure=stop_on_failure
            )
            return f"120-cycle test: {report.pass_rate:.1f}% pass rate ({report.passed_cycles}/{report.total_cycles})"

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

    async def run_120_cycles(
        self, 
        context: dict, 
        test_command: str | None = None,
        cycles: int = 120,
        stop_on_failure: bool = False,
        parallel_workers: int = 1
    ) -> CycleTestReport:
        """
        Run tests for 120 cycles (or custom count) to catch flaky tests and race conditions.
        
        The 120-cycle philosophy: Run tests enough times to catch intermittent failures.
        This helps identify:
        - Flaky tests due to timing issues
        - Race conditions in async code
        - Memory leaks that accumulate over runs
        - External service timeouts
        
        Args:
            context: Project context with architecture info
            test_command: Custom test command (auto-detected if not provided)
            cycles: Number of test cycles to run (default: 120)
            stop_on_failure: Stop immediately on first failure
            parallel_workers: Number of parallel test processes (default: 1)
            
        Returns:
            CycleTestReport with aggregate statistics
        """
        architecture = context.get("architecture", {})
        
        # Determine test command
        if not test_command:
            tech = architecture.get("tech_stack", "{}")
            test_command = await self.think(
                f"Tech stack: {tech}\n\n"
                "What is the single command to run all tests for this project? "
                "Just output the command, nothing else.",
                task_type="testing",
            )
            test_command = test_command.strip().strip("`")
        
        await self.say(f"Starting 120-cycle test run with command: {test_command}")
        
        start_time = time.time()
        results: list[CycleTestResult] = []
        
        async def run_single_cycle(cycle_num: int) -> CycleTestResult:
            """Run a single test cycle."""
            cycle_start = time.time()
            try:
                output = await self.run_command(test_command)
                passed = "fail" not in output.lower() and "error" not in output.lower()
                duration_ms = (time.time() - cycle_start) * 1000
                return CycleTestResult(
                    cycle=cycle_num,
                    passed=passed,
                    duration_ms=duration_ms,
                    output=output[:2000],  # Truncate for memory
                )
            except Exception as e:
                duration_ms = (time.time() - cycle_start) * 1000
                return CycleTestResult(
                    cycle=cycle_num,
                    passed=False,
                    duration_ms=duration_ms,
                    output=str(e),
                )
        
        # Run cycles
        if parallel_workers > 1:
            # Parallel execution
            for batch_start in range(0, cycles, parallel_workers):
                batch_end = min(batch_start + parallel_workers, cycles)
                tasks = [
                    run_single_cycle(i + 1) 
                    for i in range(batch_start, batch_end)
                ]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                
                # Check for early termination
                if stop_on_failure and any(not r.passed for r in batch_results):
                    break
                
                # Progress update every 10 cycles
                if len(results) % 10 == 0:
                    passed = sum(1 for r in results if r.passed)
                    await self.say(f"Cycle {len(results)}/{cycles}: {passed} passed")
        else:
            # Sequential execution
            for i in range(cycles):
                result = await run_single_cycle(i + 1)
                results.append(result)
                
                if stop_on_failure and not result.passed:
                    await self.say(f"Stopping at cycle {i + 1} due to failure")
                    break
                
                # Progress update every 10 cycles
                if (i + 1) % 10 == 0:
                    passed = sum(1 for r in results if r.passed)
                    await self.say(f"Cycle {i + 1}/{cycles}: {passed} passed")
        
        end_time = time.time()
        
        # Calculate statistics
        passed_results = [r for r in results if r.passed]
        failed_results = [r for r in results if not r.passed]
        durations = [r.duration_ms for r in results]
        
        report = CycleTestReport(
            total_cycles=len(results),
            passed_cycles=len(passed_results),
            failed_cycles=len(failed_results),
            pass_rate=len(passed_results) / len(results) * 100 if results else 0,
            avg_duration_ms=sum(durations) / len(durations) if durations else 0,
            min_duration_ms=min(durations) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            failures=failed_results,
            start_time=start_time,
            end_time=end_time,
            test_command=test_command,
        )
        
        # Store results in brain
        await self.brain.add_test_result(
            test_name="120_cycle_run",
            status="passed" if report.pass_rate == 100 else "flaky" if report.pass_rate > 95 else "failed",
            details=json.dumps({
                "total_cycles": report.total_cycles,
                "passed": report.passed_cycles,
                "failed": report.failed_cycles,
                "pass_rate": f"{report.pass_rate:.1f}%",
                "avg_duration_ms": f"{report.avg_duration_ms:.0f}",
                "failure_cycles": [r.cycle for r in report.failures],
            }),
            agent_id=self.agent_id,
        )
        
        # Report findings
        if report.pass_rate == 100:
            await self.say(f"✅ 120-cycle test complete: All {report.total_cycles} cycles passed!")
        elif report.pass_rate > 95:
            await self.say(
                f"⚠️ 120-cycle test complete: {report.passed_cycles}/{report.total_cycles} passed "
                f"({report.pass_rate:.1f}%). Some flaky tests detected."
            )
            # Report flaky tests as bugs
            await self._report_flaky_tests(report, context)
        else:
            await self.say(
                f"❌ 120-cycle test complete: {report.passed_cycles}/{report.total_cycles} passed "
                f"({report.pass_rate:.1f}%). Significant failures detected."
            )
            # Report failures
            for failure in report.failures[:5]:  # Report first 5 failures
                await self._report_failures(failure.output, context)
        
        return report

    async def _report_flaky_tests(self, report: CycleTestReport, context: dict) -> None:
        """Report flaky tests as bugs."""
        failure_outputs = "\n---\n".join(f.output for f in report.failures[:3])
        
        analysis = await self.think(
            f"Test command: {report.test_command}\n"
            f"Pass rate: {report.pass_rate:.1f}% over {report.total_cycles} cycles\n"
            f"Failed cycles: {[f.cycle for f in report.failures]}\n\n"
            f"Sample failure outputs:\n{failure_outputs}\n\n"
            "Analyze these intermittent failures:\n"
            "1. What tests are flaky?\n"
            "2. What are the likely causes (timing, race conditions, external deps)?\n"
            "3. How to fix each flaky test?\n\n"
            "Output as JSON with: test_name, cause, fix_suggestion",
            task_type="testing",
        )
        
        await self.brain.add_error(
            error=f"Flaky tests detected ({report.pass_rate:.1f}% pass rate)",
            file_path="test_suite",
            agent_id=self.agent_id,
            details=analysis,
        )

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

    # ---- Browser E2E Testing ----
    
    _browser_bridge: Optional["BrowserUseBridge"] = None
    
    def set_browser_bridge(self, bridge: "BrowserUseBridge") -> None:
        """Set the browser bridge for E2E testing."""
        self._browser_bridge = bridge
    
    async def run_browser_e2e_tests(
        self,
        url: str,
        context: dict,
        test_scenarios: list[dict] | None = None
    ) -> list[dict]:
        """
        Run end-to-end browser tests using the browser-use bridge.
        
        Uses the browser to:
        - Navigate to pages
        - Fill forms, click buttons
        - Verify page content
        - Take screenshots for visual regression
        
        Args:
            url: Base URL of the application to test
            context: Project context with architecture/spec info
            test_scenarios: Optional list of test scenarios. If not provided,
                          generates from the test plan.
        
        Returns:
            List of test results with pass/fail status
        """
        if self._browser_bridge is None:
            await self.say("No browser bridge configured. Cannot run E2E tests.")
            return []
        
        # Generate test scenarios if not provided
        if not test_scenarios:
            architecture = context.get("architecture", {})
            test_plan = architecture.get("test_plan", "")
            
            scenarios_json = await self.think(
                f"Base URL: {url}\n"
                f"Test plan: {test_plan}\n"
                f"Architecture: {json.dumps(architecture, indent=2)[:2000]}\n\n"
                "Generate E2E browser test scenarios. For each scenario:\n"
                "- name: descriptive name\n" 
                "- steps: what to do (click, fill, navigate)\n"
                "- expected: what should happen\n\n"
                "Output as JSON array. Generate 5-10 critical path scenarios.",
                task_type="testing",
            )
            
            try:
                if "```" in scenarios_json:
                    json_str = scenarios_json.split("```")[1]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                    test_scenarios = json.loads(json_str.strip())
                else:
                    test_scenarios = json.loads(scenarios_json.strip())
            except (json.JSONDecodeError, IndexError):
                await self.say("Failed to generate test scenarios")
                return []
        
        await self.say(f"Running {len(test_scenarios)} E2E browser tests on {url}")
        
        # Execute tests through the browser bridge
        results = await self._browser_bridge.test_webapp(url, test_scenarios)
        
        # Record results
        passed = sum(1 for r in results if r.get("passed"))
        failed = len(results) - passed
        
        await self.brain.add_test_result(
            test_name=f"e2e_{url}",
            status="passed" if failed == 0 else "failed",
            details=json.dumps({
                "url": url,
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "scenarios": [r["scenario"] for r in results if not r.get("passed")],
            }),
            agent_id=self.agent_id,
        )
        
        if failed > 0:
            await self.say(f"E2E tests: {passed} passed, {failed} failed")
            # Report failures as bugs
            for result in results:
                if not result.get("passed"):
                    await self.brain.add_error(
                        error=f"E2E test failed: {result.get('scenario')}",
                        file_path=url,
                        agent_id=self.agent_id,
                        details=result.get("details", ""),
                    )
        else:
            await self.say(f"All {passed} E2E tests passed!")
        
        return results
    
    async def visual_regression_test(
        self,
        url: str,
        baseline_screenshot: str | None = None,
        design_spec: str | None = None
    ) -> dict:
        """
        Run visual regression testing on a page.
        
        Args:
            url: URL to test
            baseline_screenshot: Path to baseline screenshot for comparison
            design_spec: Design specification to compare against
            
        Returns:
            Dict with comparison results
        """
        if self._browser_bridge is None:
            return {"error": "No browser bridge configured"}
        
        workspace = self.brain.data.get("workspace_path", "")
        screenshot_dir = Path(workspace) / "output" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        current_screenshot = str(screenshot_dir / f"visual_test_{int(time.time())}.png")
        
        # Take screenshot
        success = await self._browser_bridge.take_visual_snapshot(url, current_screenshot)
        if not success:
            return {"error": "Failed to capture screenshot"}
        
        result = {
            "url": url,
            "screenshot": current_screenshot,
            "matches": True,
            "issues": [],
        }
        
        # Compare against design spec if provided
        if design_spec:
            comparison = await self._browser_bridge.compare_visual(url, design_spec)
            result["design_comparison"] = comparison
            
            try:
                comp_data = json.loads(comparison.get("comparison", "{}"))
                result["matches"] = comp_data.get("matches", True)
                result["issues"] = comp_data.get("issues", [])
            except json.JSONDecodeError:
                pass
        
        # Store result
        await self.brain.add_test_result(
            test_name=f"visual_{url}",
            status="passed" if result["matches"] else "failed",
            details=json.dumps(result),
            agent_id=self.agent_id,
        )
        
        return result
