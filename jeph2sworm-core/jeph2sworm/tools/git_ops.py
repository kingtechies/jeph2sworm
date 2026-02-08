"""Git Operations - Git management for project workspaces."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class GitOps:
    """
    Handles all Git operations for the project workspace.

    Used by agents (mostly DevOps) to manage version control:
    - Initialize repos
    - Stage, commit, push
    - Branch management
    - Conflict detection
    """

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    async def _run(self, *args: str, cwd: Optional[str] = None) -> str:
        """Run a git command and return stdout."""
        cmd = ["git"] + list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or self.workspace_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error = stderr.decode().strip()
            logger.error("git_command_failed", cmd=cmd, error=error)
            raise RuntimeError(f"Git error: {error}")

        return stdout.decode().strip()

    async def init(self, initial_branch: str = "main") -> str:
        """Initialize a new git repository."""
        result = await self._run("init", "-b", initial_branch)
        await event_bus.emit(
            EventType.SYSTEM_MESSAGE,
            source="git_ops",
            data={"action": "init", "branch": initial_branch},
        )
        return result

    async def clone(self, url: str, target_dir: Optional[str] = None) -> str:
        """Clone a repository."""
        args = ["clone", url]
        if target_dir:
            args.append(target_dir)
        return await self._run(*args)

    async def add(self, *paths: str) -> str:
        """Stage files."""
        if not paths:
            paths = (".",)
        return await self._run("add", *paths)

    async def commit(self, message: str) -> str:
        """Create a commit."""
        result = await self._run("commit", "-m", message)
        await event_bus.emit(
            EventType.SYSTEM_MESSAGE,
            source="git_ops",
            data={"action": "commit", "message": message},
        )
        return result

    async def push(self, remote: str = "origin", branch: str = "main") -> str:
        """Push to remote."""
        return await self._run("push", remote, branch)

    async def pull(self, remote: str = "origin", branch: str = "main") -> str:
        """Pull from remote."""
        return await self._run("pull", remote, branch)

    async def checkout(self, branch: str, create: bool = False) -> str:
        """Switch branches."""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)
        return await self._run(*args)

    async def create_branch(self, branch: str) -> str:
        """Create and switch to a new branch."""
        return await self.checkout(branch, create=True)

    async def merge(self, branch: str) -> str:
        """Merge a branch into current."""
        return await self._run("merge", branch)

    async def status(self) -> Dict[str, List[str]]:
        """Get repository status as structured data."""
        output = await self._run("status", "--porcelain")
        result: Dict[str, List[str]] = {
            "staged": [],
            "modified": [],
            "untracked": [],
            "deleted": [],
        }

        for line in output.split("\n"):
            if not line.strip():
                continue
            status_code = line[:2]
            filepath = line[3:].strip()

            if status_code[0] in ("A", "M"):
                result["staged"].append(filepath)
            if status_code[1] == "M":
                result["modified"].append(filepath)
            if status_code == "??":
                result["untracked"].append(filepath)
            if "D" in status_code:
                result["deleted"].append(filepath)

        return result

    async def log(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent commit log."""
        output = await self._run(
            "log",
            f"-{count}",
            "--pretty=format:%H|%an|%ae|%s|%ci",
        )

        commits = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "message": parts[3],
                    "date": parts[4],
                })

        return commits

    async def diff(self, staged: bool = False) -> str:
        """Get diff of changes."""
        args = ["diff"]
        if staged:
            args.append("--staged")
        return await self._run(*args)

    async def current_branch(self) -> str:
        """Get current branch name."""
        return await self._run("rev-parse", "--abbrev-ref", "HEAD")

    async def branches(self) -> List[str]:
        """List all branches."""
        output = await self._run("branch", "--list")
        return [b.strip().lstrip("* ") for b in output.split("\n") if b.strip()]

    async def stash(self, message: str = "") -> str:
        """Stash current changes."""
        args = ["stash"]
        if message:
            args.extend(["push", "-m", message])
        return await self._run(*args)

    async def stash_pop(self) -> str:
        """Pop the latest stash."""
        return await self._run("stash", "pop")

    async def set_config(self, key: str, value: str, is_global: bool = False) -> str:
        """Set a git config value."""
        args = ["config"]
        if is_global:
            args.append("--global")
        args.extend([key, value])
        return await self._run(*args)

    async def setup_gitignore(self, patterns: List[str]) -> None:
        """Create or append to .gitignore."""
        import os

        gitignore_path = os.path.join(self.workspace_dir, ".gitignore")
        existing = set()

        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                existing = set(f.read().strip().split("\n"))

        new_patterns = [p for p in patterns if p not in existing]
        if new_patterns:
            with open(gitignore_path, "a") as f:
                f.write("\n" + "\n".join(new_patterns) + "\n")
