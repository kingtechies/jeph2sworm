"""Terminal command execution for agents."""

from __future__ import annotations

import asyncio
import os
from typing import Optional

import structlog

from jeph2sworm.security.rules_engine import RulesEngine

logger = structlog.get_logger()


class Terminal:
    """
    Execute terminal commands on behalf of agents.

    Commands are validated by the rules engine before execution.
    Output is captured and returned. Background processes are tracked.
    """

    def __init__(self, workspace_root: str, rules: RulesEngine) -> None:
        self.workspace_root = workspace_root
        self.rules = rules
        self._background_processes: dict[str, asyncio.subprocess.Process] = {}

    async def run(
        self,
        command: str,
        agent_id: str = "system",
        cwd: Optional[str] = None,
        timeout: int = 300,
        env: Optional[dict[str, str]] = None,
    ) -> dict[str, str | int]:
        """
        Execute a command and return its output.

        Returns:
            {"stdout": str, "stderr": str, "exit_code": int}
        """
        self.rules.validate_command(command)

        work_dir = cwd or self.workspace_root
        run_env = {**os.environ, **(env or {})}

        await logger.ainfo("terminal_run", command=command, agent=agent_id)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=run_env,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            result = {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode or 0,
            }

            await logger.ainfo(
                "terminal_result",
                command=command,
                exit_code=result["exit_code"],
                agent=agent_id,
            )

            return result

        except asyncio.TimeoutError:
            proc.kill()
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s: {command}",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
            }

    async def run_background(
        self,
        command: str,
        process_id: str,
        agent_id: str = "system",
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> str:
        """Start a background process (e.g., dev server)."""
        self.rules.validate_command(command)

        work_dir = cwd or self.workspace_root
        run_env = {**os.environ, **(env or {})}

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir,
            env=run_env,
        )

        self._background_processes[process_id] = proc
        await logger.ainfo(
            "background_process_started",
            command=command,
            process_id=process_id,
            agent=agent_id,
        )
        return process_id

    async def stop_background(self, process_id: str) -> None:
        """Stop a background process."""
        proc = self._background_processes.pop(process_id, None)
        if proc:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            await logger.ainfo("background_process_stopped", process_id=process_id)

    async def install_package(
        self,
        manager: str,
        package: str,
        agent_id: str = "system",
    ) -> dict[str, str | int]:
        """Install a package using the specified package manager."""
        commands = {
            "npm": f"npm install {package}",
            "pip": f"pip install {package}",
            "pnpm": f"pnpm add {package}",
            "yarn": f"yarn add {package}",
        }
        cmd = commands.get(manager)
        if not cmd:
            return {"stdout": "", "stderr": f"Unknown package manager: {manager}", "exit_code": 1}

        return await self.run(cmd, agent_id=agent_id, timeout=120)

    async def stop_all(self) -> None:
        """Stop all background processes."""
        for pid in list(self._background_processes.keys()):
            await self.stop_background(pid)
