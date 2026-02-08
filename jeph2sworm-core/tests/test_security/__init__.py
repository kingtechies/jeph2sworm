"""Tests for Security module - rules_engine, action_validator, file_guard."""

import os
import pytest
import asyncio

from jeph2sworm.security.action_validator import ActionValidator, ValidationResult
from jeph2sworm.security.file_guard import FileGuard


class TestActionValidator:
    """Tests for pre/post action validation."""

    @pytest.fixture
    def validator(self, workspace_dir):
        return ActionValidator(workspace_dir)

    def test_allow_workspace_file(self, validator, workspace_dir):
        filepath = os.path.join(workspace_dir, "test.py")
        result = validator.validate_file_action("create", filepath, "backend")
        assert result.allowed

    def test_deny_file_outside_workspace(self, validator):
        result = validator.validate_file_action("create", "/etc/passwd", "backend")
        assert not result.allowed

    def test_deny_file_deletion(self, validator, workspace_dir):
        filepath = os.path.join(workspace_dir, "test.py")
        result = validator.validate_file_action("delete", filepath, "backend")
        assert not result.allowed

    def test_deny_protected_extension(self, validator, workspace_dir):
        filepath = os.path.join(workspace_dir, "key.pem")
        result = validator.validate_file_action("write", filepath, "backend")
        assert not result.allowed

    def test_allow_safe_command(self, validator):
        result = validator.validate_command("npm install express", "backend")
        assert result.allowed

    def test_deny_destructive_command(self, validator):
        result = validator.validate_command("rm -rf /", "backend")
        assert not result.allowed

    def test_deny_system_command(self, validator):
        result = validator.validate_command("shutdown -h now", "backend")
        assert not result.allowed

    def test_allow_network_request(self, validator):
        result = validator.validate_network_action("https://api.example.com", "GET", "backend")
        assert result.allowed

    def test_audit_log(self, validator, workspace_dir):
        filepath = os.path.join(workspace_dir, "test.py")
        validator.validate_file_action("create", filepath, "backend")
        log = validator.get_audit_log()
        assert len(log) == 1
        assert log[0]["allowed"] is True


class TestFileGuard:
    """Tests for file system protection."""

    @pytest.fixture
    def guard(self, workspace_dir):
        return FileGuard(workspace_dir)

    def test_is_safe_path(self, guard, workspace_dir):
        safe = os.path.join(workspace_dir, "test.py")
        assert guard.is_safe_path(safe)
        assert not guard.is_safe_path("/etc/passwd")

    def test_backup_and_restore(self, guard, workspace_dir):
        filepath = os.path.join(workspace_dir, "test.txt")
        with open(filepath, "w") as f:
            f.write("original content")

        backup = guard.backup_file(filepath)
        assert backup is not None

        with open(filepath, "w") as f:
            f.write("modified content")

        restored = guard.restore_file(filepath)
        assert restored
        with open(filepath) as f:
            assert f.read() == "original content"

    @pytest.mark.asyncio
    async def test_file_locking(self, guard):
        acquired = await guard.acquire_lock("/test/file.py", "backend")
        assert acquired
        assert guard.is_locked("/test/file.py")
        assert guard.get_lock_holder("/test/file.py") == "backend"
        guard.release_lock("/test/file.py", "backend")
        assert not guard.is_locked("/test/file.py")
