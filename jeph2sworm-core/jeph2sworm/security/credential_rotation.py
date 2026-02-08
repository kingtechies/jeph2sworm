"""Credential Rotation Service - Automated credential lifecycle management."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import structlog

from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus
from jeph2sworm.security.credential_vault import CredentialVault
from jeph2sworm.tools.credential_generator import AiEnvManager, CredentialGenerator

logger = structlog.get_logger()


@dataclass
class RotationPolicy:
    """Defines rotation policy for credentials."""
    
    # Rotation interval in days
    rotation_interval_days: int = 30
    
    # Maximum age before mandatory rotation (days)
    max_age_days: int = 90
    
    # Minimum password length
    min_password_length: int = 32
    
    # Categories to rotate (None = all)
    categories: Optional[list[str]] = None
    
    # Keys to exclude from rotation
    exclude_keys: Optional[list[str]] = None


@dataclass
class RotationResult:
    """Result of a rotation operation."""
    
    key: str
    success: bool
    old_rotated_at: float
    new_rotated_at: float
    error: Optional[str] = None


class CredentialRotationService:
    """
    Automated credential rotation service.
    
    Features:
    - Scheduled rotation based on policy
    - Rotation tracking and audit log
    - Backup before rotation
    - Notification on rotation events
    - Support for both CredentialVault and AiEnvManager
    """
    
    def __init__(
        self,
        vault: Optional[CredentialVault] = None,
        ai_env_manager: Optional[AiEnvManager] = None,
        backup_dir: str = ".jeph2sworm/credential_backups",
        rotation_log_path: str = ".jeph2sworm/rotation_log.json",
    ):
        self.vault = vault
        self.ai_env_manager = ai_env_manager
        self.backup_dir = Path(backup_dir)
        self.rotation_log_path = Path(rotation_log_path)
        self._rotation_log: list[dict] = []
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._hooks: list[Callable] = []
        
        self._load_rotation_log()
    
    def _load_rotation_log(self) -> None:
        """Load rotation history from disk."""
        if self.rotation_log_path.exists():
            try:
                self._rotation_log = json.loads(self.rotation_log_path.read_text())
            except (json.JSONDecodeError, IOError):
                self._rotation_log = []
    
    def _save_rotation_log(self) -> None:
        """Save rotation history to disk."""
        self.rotation_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.rotation_log_path.write_text(json.dumps(self._rotation_log, indent=2, default=str))
    
    def add_rotation_hook(self, callback: Callable) -> None:
        """Add a callback to be called after rotation."""
        self._hooks.append(callback)
    
    async def start_scheduler(
        self,
        policy: Optional[RotationPolicy] = None,
        check_interval_hours: int = 24
    ) -> None:
        """Start the rotation scheduler."""
        if self._running:
            return
        
        self._running = True
        policy = policy or RotationPolicy()
        
        async def scheduler_loop():
            while self._running:
                try:
                    await self.check_and_rotate(policy)
                except Exception as e:
                    logger.error("rotation_scheduler_error", error=str(e))
                
                await asyncio.sleep(check_interval_hours * 3600)
        
        self._scheduler_task = asyncio.create_task(scheduler_loop())
        logger.info("rotation_scheduler_started", interval_hours=check_interval_hours)
    
    async def stop_scheduler(self) -> None:
        """Stop the rotation scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("rotation_scheduler_stopped")
    
    async def check_and_rotate(self, policy: RotationPolicy) -> list[RotationResult]:
        """Check all credentials and rotate those that need it."""
        results: list[RotationResult] = []
        now = time.time()
        rotation_threshold = now - (policy.rotation_interval_days * 86400)
        max_age_threshold = now - (policy.max_age_days * 86400)
        
        # Check vault credentials
        if self.vault:
            for cred_info in self.vault.list_credentials():
                key = cred_info["name"]
                
                # Check exclusions
                if policy.exclude_keys and key in policy.exclude_keys:
                    continue
                
                # Check categories
                if policy.categories and cred_info.get("category") not in policy.categories:
                    continue
                
                rotated_at = cred_info.get("rotated_at", 0)
                
                # Rotate if past rotation interval or max age
                if rotated_at < rotation_threshold:
                    result = await self._rotate_vault_credential(key, rotated_at, policy)
                    results.append(result)
                elif rotated_at < max_age_threshold:
                    # Force rotation if past max age
                    logger.warning("credential_max_age_exceeded", key=key)
                    result = await self._rotate_vault_credential(key, rotated_at, policy)
                    results.append(result)
        
        # Check ai.env credentials
        if self.ai_env_manager:
            creds = await self.ai_env_manager.list_credentials(masked=False)
            for cred in creds:
                key = cred["key"]
                
                # Skip non-password keys
                password_keys = ["PASSWORD", "SECRET", "TOKEN", "KEY"]
                if not any(pk in key.upper() for pk in password_keys):
                    continue
                
                # Check exclusions
                if policy.exclude_keys and key in policy.exclude_keys:
                    continue
                
                # Check rotation log for last rotation time
                last_rotation = self._get_last_rotation_time(key)
                
                if last_rotation < rotation_threshold:
                    result = await self._rotate_ai_env_credential(key, last_rotation, policy)
                    results.append(result)
        
        # Log results
        rotated_count = sum(1 for r in results if r.success)
        if rotated_count > 0:
            logger.info("credentials_rotated", count=rotated_count, total=len(results))
            
            # Emit event
            await event_bus.emit(
                EventType.TASK_COMPLETED,
                source="credential-rotation",
                data={
                    "action": "credentials_rotated",
                    "count": rotated_count,
                    "keys": [r.key for r in results if r.success],
                },
            )
        
        return results
    
    def _get_last_rotation_time(self, key: str) -> float:
        """Get the last rotation time for a key from the log."""
        for entry in reversed(self._rotation_log):
            if entry.get("key") == key and entry.get("success"):
                return entry.get("timestamp", 0)
        return 0
    
    async def _rotate_vault_credential(
        self,
        key: str,
        old_rotated_at: float,
        policy: RotationPolicy
    ) -> RotationResult:
        """Rotate a vault credential."""
        try:
            # Backup first
            await self._backup_credential("vault", key)
            
            # Generate new value
            new_value = CredentialGenerator.generate_password(policy.min_password_length)
            
            # Rotate
            success = self.vault.rotate(key, new_value)
            
            result = RotationResult(
                key=key,
                success=success,
                old_rotated_at=old_rotated_at,
                new_rotated_at=time.time(),
            )
            
            # Log rotation
            self._rotation_log.append({
                "key": key,
                "source": "vault",
                "success": success,
                "timestamp": time.time(),
            })
            self._save_rotation_log()
            
            # Call hooks
            for hook in self._hooks:
                try:
                    await hook(result) if asyncio.iscoroutinefunction(hook) else hook(result)
                except Exception as e:
                    logger.error("rotation_hook_error", error=str(e))
            
            return result
            
        except Exception as e:
            logger.error("vault_rotation_failed", key=key, error=str(e))
            return RotationResult(
                key=key,
                success=False,
                old_rotated_at=old_rotated_at,
                new_rotated_at=time.time(),
                error=str(e),
            )
    
    async def _rotate_ai_env_credential(
        self,
        key: str,
        old_rotated_at: float,
        policy: RotationPolicy
    ) -> RotationResult:
        """Rotate an ai.env credential."""
        try:
            # Backup first
            await self._backup_credential("ai_env", key)
            
            # Rotate (auto-generate new value)
            await self.ai_env_manager.set_credential(
                key,
                auto_generate=True,
                agent_id="rotation-service"
            )
            
            result = RotationResult(
                key=key,
                success=True,
                old_rotated_at=old_rotated_at,
                new_rotated_at=time.time(),
            )
            
            # Log rotation
            self._rotation_log.append({
                "key": key,
                "source": "ai_env",
                "success": True,
                "timestamp": time.time(),
            })
            self._save_rotation_log()
            
            # Call hooks
            for hook in self._hooks:
                try:
                    await hook(result) if asyncio.iscoroutinefunction(hook) else hook(result)
                except Exception as e:
                    logger.error("rotation_hook_error", error=str(e))
            
            return result
            
        except Exception as e:
            logger.error("ai_env_rotation_failed", key=key, error=str(e))
            return RotationResult(
                key=key,
                success=False,
                old_rotated_at=old_rotated_at,
                new_rotated_at=time.time(),
                error=str(e),
            )
    
    async def _backup_credential(self, source: str, key: str) -> None:
        """Backup a credential before rotation."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = self.backup_dir / f"{source}_{key}_{int(time.time())}.backup"
        
        if source == "vault" and self.vault:
            value = self.vault.retrieve(key, agent="backup")
            if value:
                # Encrypt or obfuscate the backup
                import base64
                encrypted = base64.b64encode(value.encode()).decode()
                backup_file.write_text(encrypted)
        
        elif source == "ai_env" and self.ai_env_manager:
            value = await self.ai_env_manager.get_credential(key)
            if value:
                import base64
                encrypted = base64.b64encode(value.encode()).decode()
                backup_file.write_text(encrypted)
        
        logger.debug("credential_backed_up", source=source, key=key)
    
    async def rotate_single(self, key: str, source: str = "auto") -> RotationResult:
        """Manually rotate a single credential."""
        policy = RotationPolicy()
        
        if source == "auto":
            # Try vault first, then ai_env
            if self.vault and self.vault.has(key):
                source = "vault"
            elif self.ai_env_manager:
                source = "ai_env"
        
        if source == "vault" and self.vault:
            cred_info = next(
                (c for c in self.vault.list_credentials() if c["name"] == key),
                None
            )
            old_rotated_at = cred_info.get("rotated_at", 0) if cred_info else 0
            return await self._rotate_vault_credential(key, old_rotated_at, policy)
        
        elif source == "ai_env" and self.ai_env_manager:
            old_rotated_at = self._get_last_rotation_time(key)
            return await self._rotate_ai_env_credential(key, old_rotated_at, policy)
        
        return RotationResult(
            key=key,
            success=False,
            old_rotated_at=0,
            new_rotated_at=time.time(),
            error="Credential not found",
        )
    
    def get_rotation_schedule(self, policy: Optional[RotationPolicy] = None) -> list[dict]:
        """Get the next scheduled rotation for each credential."""
        policy = policy or RotationPolicy()
        schedule = []
        now = time.time()
        
        if self.vault:
            for cred_info in self.vault.list_credentials():
                rotated_at = cred_info.get("rotated_at", 0)
                next_rotation = rotated_at + (policy.rotation_interval_days * 86400)
                schedule.append({
                    "key": cred_info["name"],
                    "source": "vault",
                    "last_rotated": datetime.fromtimestamp(rotated_at).isoformat() if rotated_at else "never",
                    "next_rotation": datetime.fromtimestamp(next_rotation).isoformat(),
                    "days_until": max(0, int((next_rotation - now) / 86400)),
                    "overdue": next_rotation < now,
                })
        
        if self.ai_env_manager:
            for key in self._rotation_log:
                if key.get("source") == "ai_env":
                    last = key.get("timestamp", 0)
                    next_rotation = last + (policy.rotation_interval_days * 86400)
                    schedule.append({
                        "key": key.get("key"),
                        "source": "ai_env",
                        "last_rotated": datetime.fromtimestamp(last).isoformat() if last else "never",
                        "next_rotation": datetime.fromtimestamp(next_rotation).isoformat(),
                        "days_until": max(0, int((next_rotation - now) / 86400)),
                        "overdue": next_rotation < now,
                    })
        
        return schedule
    
    def get_rotation_history(self, key: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Get rotation history, optionally filtered by key."""
        history = self._rotation_log
        
        if key:
            history = [h for h in history if h.get("key") == key]
        
        return history[-limit:]
