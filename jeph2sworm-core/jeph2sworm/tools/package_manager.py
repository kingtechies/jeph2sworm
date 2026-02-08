"""Package Manager - npm, pip, pnpm, yarn, apt operations."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class PackageManager:
    """
    Unified package manager interface for installing dependencies.

    Supports:
    - npm / pnpm / yarn (Node.js)
    - pip / poetry (Python)
    - apt (system packages, when needed)
    """

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    async def _run(self, cmd: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a package manager command."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or self.workspace_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        result = {
            "success": proc.returncode == 0,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
            "returncode": proc.returncode,
        }

        if proc.returncode != 0:
            logger.error("package_cmd_failed", cmd=cmd, error=result["stderr"])
        else:
            logger.info("package_cmd_ok", cmd=cmd[:3])

        return result

    # ── npm / pnpm / yarn ──────────────────────────────────────

    async def npm_install(
        self,
        packages: Optional[List[str]] = None,
        dev: bool = False,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Install npm packages."""
        cmd = ["npm", "install"]
        if packages:
            cmd.extend(packages)
        if dev:
            cmd.append("--save-dev")

        result = await self._run(cmd, cwd=cwd)
        self._emit("npm_install", packages or ["all"], result["success"])
        return result

    async def npm_run(self, script: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run an npm script."""
        return await self._run(["npm", "run", script], cwd=cwd)

    async def npm_init(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a new npm project."""
        return await self._run(["npm", "init", "-y"], cwd=cwd)

    async def pnpm_install(
        self,
        packages: Optional[List[str]] = None,
        dev: bool = False,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Install pnpm packages."""
        cmd = ["pnpm", "add"]
        if packages:
            cmd.extend(packages)
        else:
            cmd = ["pnpm", "install"]
        if dev:
            cmd.append("-D")

        result = await self._run(cmd, cwd=cwd)
        self._emit("pnpm_install", packages or ["all"], result["success"])
        return result

    async def yarn_install(
        self,
        packages: Optional[List[str]] = None,
        dev: bool = False,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Install yarn packages."""
        cmd = ["yarn", "add"]
        if not packages:
            cmd = ["yarn", "install"]
        else:
            cmd.extend(packages)
        if dev:
            cmd.append("--dev")

        result = await self._run(cmd, cwd=cwd)
        self._emit("yarn_install", packages or ["all"], result["success"])
        return result

    # ── pip / poetry ───────────────────────────────────────────

    async def pip_install(
        self,
        packages: List[str],
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Install pip packages."""
        cmd = ["pip", "install"] + packages
        result = await self._run(cmd, cwd=cwd)
        self._emit("pip_install", packages, result["success"])
        return result

    async def pip_install_requirements(
        self, requirements_file: str = "requirements.txt", cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Install from requirements.txt."""
        return await self._run(
            ["pip", "install", "-r", requirements_file], cwd=cwd
        )

    async def pip_install_editable(self, path: str = ".", cwd: Optional[str] = None) -> Dict[str, Any]:
        """Install a package in editable mode."""
        return await self._run(["pip", "install", "-e", path], cwd=cwd)

    async def poetry_install(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Install poetry dependencies."""
        return await self._run(["poetry", "install"], cwd=cwd)

    async def poetry_add(
        self,
        packages: List[str],
        dev: bool = False,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add poetry packages."""
        cmd = ["poetry", "add"] + packages
        if dev:
            cmd.append("--group=dev")
        return await self._run(cmd, cwd=cwd)

    # ── Detect and auto-install ────────────────────────────────

    async def detect_and_install(self, project_dir: str) -> Dict[str, Any]:
        """Auto-detect package manager and install dependencies."""
        import os

        results: Dict[str, Any] = {"manager": None, "success": False}

        # Check for Node.js project
        if os.path.exists(os.path.join(project_dir, "pnpm-lock.yaml")):
            results["manager"] = "pnpm"
            results.update(await self._run(["pnpm", "install"], cwd=project_dir))
        elif os.path.exists(os.path.join(project_dir, "yarn.lock")):
            results["manager"] = "yarn"
            results.update(await self._run(["yarn", "install"], cwd=project_dir))
        elif os.path.exists(os.path.join(project_dir, "package.json")):
            results["manager"] = "npm"
            results.update(await self._run(["npm", "install"], cwd=project_dir))

        # Check for Python project
        if os.path.exists(os.path.join(project_dir, "pyproject.toml")):
            results["manager"] = "pip"
            results.update(
                await self._run(["pip", "install", "-e", "."], cwd=project_dir)
            )
        elif os.path.exists(os.path.join(project_dir, "requirements.txt")):
            results["manager"] = "pip"
            results.update(
                await self._run(
                    ["pip", "install", "-r", "requirements.txt"], cwd=project_dir
                )
            )

        return results

    async def list_installed(self, manager: str = "npm", cwd: Optional[str] = None) -> List[Dict[str, str]]:
        """List installed packages."""
        if manager == "npm":
            result = await self._run(["npm", "list", "--json", "--depth=0"], cwd=cwd)
            if result["success"]:
                try:
                    data = json.loads(result["stdout"])
                    deps = data.get("dependencies", {})
                    return [{"name": k, "version": v.get("version", "?")} for k, v in deps.items()]
                except json.JSONDecodeError:
                    pass
        elif manager == "pip":
            result = await self._run(["pip", "list", "--format=json"], cwd=cwd)
            if result["success"]:
                try:
                    return json.loads(result["stdout"])
                except json.JSONDecodeError:
                    pass

        return []

    def _emit(self, action: str, packages: List[str], success: bool) -> None:
        """Emit an event for package operations."""
        event_bus.emit(SwarmEvent(
            type=EventType.SYSTEM_MESSAGE,
            agent="package_manager",
            data={"action": action, "packages": packages, "success": success},
        ))
