"""File Guard - File system protection and access control."""

from __future__ import annotations

import asyncio
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import structlog

logger = structlog.get_logger()


class FileGuard:
    """
    Protects the file system from destructive or unauthorized operations.

    Features:
    - Auto-backup before modifications
    - File locking (prevent concurrent writes)
    - Write-ahead logging
    - Protected path enforcement
    - Undo/restore capability
    """

    def __init__(
        self,
        workspace_dir: str,
        backup_dir: str = ".jeph2sworm/backups",
        max_backups: int = 50,
    ):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.backup_dir = Path(workspace_dir) / backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups

        self._locks: Dict[str, asyncio.Lock] = {}
        self._locked_by: Dict[str, str] = {}  # filepath -> agent
        self._write_log: List[Dict] = []

    async def acquire_lock(self, filepath: str, agent: str, timeout: float = 10.0) -> bool:
        """
        Acquire a write lock on a file.

        Returns True if lock acquired, False if timed out.
        """
        abs_path = os.path.abspath(filepath)

        if abs_path not in self._locks:
            self._locks[abs_path] = asyncio.Lock()

        try:
            acquired = await asyncio.wait_for(
                self._locks[abs_path].acquire(), timeout=timeout
            )
            if acquired:
                self._locked_by[abs_path] = agent
                logger.debug("file_lock_acquired", filepath=filepath, agent=agent)
            return acquired
        except asyncio.TimeoutError:
            holder = self._locked_by.get(abs_path, "unknown")
            logger.warning(
                "file_lock_timeout",
                filepath=filepath,
                agent=agent,
                held_by=holder,
            )
            return False

    def release_lock(self, filepath: str, agent: str) -> bool:
        """Release a write lock on a file."""
        abs_path = os.path.abspath(filepath)

        if abs_path not in self._locks:
            return False

        holder = self._locked_by.get(abs_path)
        if holder and holder != agent:
            logger.warning(
                "file_lock_release_denied",
                filepath=filepath,
                agent=agent,
                held_by=holder,
            )
            return False

        if self._locks[abs_path].locked():
            self._locks[abs_path].release()
            self._locked_by.pop(abs_path, None)
            logger.debug("file_lock_released", filepath=filepath, agent=agent)
            return True

        return False

    def backup_file(self, filepath: str) -> Optional[str]:
        """Create a backup of a file before modification."""
        if not os.path.exists(filepath):
            return None

        rel_path = os.path.relpath(filepath, self.workspace_dir)
        timestamp = int(time.time() * 1000)
        backup_name = f"{rel_path.replace('/', '_')}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(filepath, str(backup_path))
            self._write_log.append({
                "action": "backup",
                "original": filepath,
                "backup": str(backup_path),
                "timestamp": time.time(),
            })

            # Prune old backups
            self._prune_backups()

            return str(backup_path)

        except Exception as e:
            logger.error("backup_failed", filepath=filepath, error=str(e))
            return None

    def restore_file(self, filepath: str) -> bool:
        """Restore a file from its most recent backup."""
        rel_path = os.path.relpath(filepath, self.workspace_dir)
        prefix = rel_path.replace("/", "_")

        # Find the most recent backup
        backups = sorted(
            self.backup_dir.glob(f"{prefix}_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            logger.warning("no_backup_found", filepath=filepath)
            return False

        try:
            shutil.copy2(str(backups[0]), filepath)
            self._write_log.append({
                "action": "restore",
                "filepath": filepath,
                "from_backup": str(backups[0]),
                "timestamp": time.time(),
            })
            logger.info("file_restored", filepath=filepath, from_backup=str(backups[0]))
            return True

        except Exception as e:
            logger.error("restore_failed", filepath=filepath, error=str(e))
            return False

    def is_locked(self, filepath: str) -> bool:
        """Check if a file is currently locked."""
        abs_path = os.path.abspath(filepath)
        return abs_path in self._locks and self._locks[abs_path].locked()

    def get_lock_holder(self, filepath: str) -> Optional[str]:
        """Get the agent holding the lock on a file."""
        abs_path = os.path.abspath(filepath)
        return self._locked_by.get(abs_path)

    def is_safe_path(self, filepath: str) -> bool:
        """Check if a filepath is safe to operate on."""
        abs_path = os.path.abspath(filepath)
        return abs_path.startswith(self.workspace_dir)

    def get_write_log(self, limit: int = 50) -> List[Dict]:
        """Get recent write operations log."""
        return self._write_log[-limit:]

    def list_backups(self, filepath: Optional[str] = None) -> List[Dict]:
        """List available backups, optionally for a specific file."""
        backups = []
        pattern = "*"
        if filepath:
            rel_path = os.path.relpath(filepath, self.workspace_dir)
            pattern = f"{rel_path.replace('/', '_')}_*"

        for f in sorted(self.backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
            backups.append({
                "backup_path": str(f),
                "size_bytes": f.stat().st_size,
                "created": f.stat().st_mtime,
            })

        return backups

    def _prune_backups(self) -> None:
        """Remove oldest backups if we exceed max_backups."""
        all_backups = sorted(
            self.backup_dir.iterdir(),
            key=lambda p: p.stat().st_mtime,
        )
        while len(all_backups) > self.max_backups:
            oldest = all_backups.pop(0)
            oldest.unlink()
