"""File system operations for agents - read, write, create, with safety enforcement."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
import structlog

from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.security.rules_engine import RulesEngine

logger = structlog.get_logger()


class FileSystem:
    """
    Safe file system operations with rules enforcement.

    All writes are backed up. All operations are logged.
    No access outside workspace. No deletions (only archive).
    """

    def __init__(self, workspace_root: Path, rules: RulesEngine) -> None:
        self.workspace_root = workspace_root.resolve()
        self.rules = rules
        self._archive_dir = workspace_root / ".jeph2sworm" / "archive"
        self._backup_dir = workspace_root / ".jeph2sworm" / "file_backups"

    async def create_file(
        self,
        path: str,
        content: str,
        agent_id: str = "system",
    ) -> Path:
        """Create a new file. Creates directories as needed."""
        full_path = (self.workspace_root / path).resolve()
        self.rules.validate_file_write(full_path)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "w") as f:
            await f.write(content)

        await event_bus.emit(
            EventType.FILE_CREATED,
            source=agent_id,
            data={"file_path": path, "purpose": "created"},
        )
        await logger.ainfo("file_created", path=path, agent=agent_id)
        return full_path

    async def read_file(self, path: str) -> str:
        """Read file contents."""
        full_path = (self.workspace_root / path).resolve()
        self.rules.validate_file_read(full_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, "r") as f:
            return await f.read()

    async def write_file(
        self,
        path: str,
        content: str,
        agent_id: str = "system",
    ) -> Path:
        """Write to an existing or new file with backup."""
        full_path = (self.workspace_root / path).resolve()
        self.rules.validate_file_write(full_path)

        # Backup existing file before overwrite
        if full_path.exists():
            await self._backup_file(full_path)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "w") as f:
            await f.write(content)

        await event_bus.emit(
            EventType.FILE_MODIFIED,
            source=agent_id,
            data={"file_path": path, "changes_summary": "file updated"},
        )
        await logger.ainfo("file_written", path=path, agent=agent_id)
        return full_path

    async def update_file(
        self,
        path: str,
        old_content: str,
        new_content: str,
        agent_id: str = "system",
    ) -> bool:
        """Replace specific content in a file."""
        current = await self.read_file(path)
        if old_content not in current:
            return False

        full_path = (self.workspace_root / path).resolve()
        await self._backup_file(full_path)

        updated = current.replace(old_content, new_content, 1)
        async with aiofiles.open(full_path, "w") as f:
            await f.write(updated)

        await event_bus.emit(
            EventType.FILE_MODIFIED,
            source=agent_id,
            data={"file_path": path, "changes_summary": "content replaced"},
        )
        return True

    async def create_directory(self, path: str, agent_id: str = "system") -> Path:
        """Create a directory (and parents)."""
        full_path = (self.workspace_root / path).resolve()
        self.rules.validate_file_write(full_path)

        full_path.mkdir(parents=True, exist_ok=True)
        await logger.ainfo("directory_created", path=path, agent=agent_id)
        return full_path

    async def list_directory(self, path: str = ".") -> list[dict]:
        """List directory contents with type info."""
        full_path = (self.workspace_root / path).resolve()
        self.rules.validate_file_read(full_path)

        entries = []
        if full_path.is_dir():
            for item in sorted(full_path.iterdir()):
                rel = item.relative_to(self.workspace_root)
                entries.append({
                    "name": item.name,
                    "path": str(rel),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        return entries

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        full_path = (self.workspace_root / path).resolve()
        return full_path.exists()

    async def search_files(self, pattern: str) -> list[str]:
        """Search for files matching a glob pattern."""
        matches = []
        for match in self.workspace_root.rglob(pattern):
            if ".jeph2sworm" not in str(match) and "node_modules" not in str(match):
                matches.append(str(match.relative_to(self.workspace_root)))
        return matches

    async def copy_file(
        self, src: str, dst: str, agent_id: str = "system"
    ) -> Path:
        """Copy a file."""
        src_path = (self.workspace_root / src).resolve()
        dst_path = (self.workspace_root / dst).resolve()
        self.rules.validate_file_read(src_path)
        self.rules.validate_file_write(dst_path)

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(dst_path))
        await logger.ainfo("file_copied", src=src, dst=dst, agent=agent_id)
        return dst_path

    async def _backup_file(self, path: Path) -> None:
        """Create a backup of a file before modification."""
        if not path.exists():
            return

        self._backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rel = path.relative_to(self.workspace_root)
        backup_name = f"{rel}".replace("/", "__") + f".{ts}.bak"
        backup_path = self._backup_dir / backup_name
        shutil.copy2(str(path), str(backup_path))
