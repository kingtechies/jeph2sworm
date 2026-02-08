"""Tests for Tools module - file_system, terminal, git_ops, package_manager, credential_generator."""

import os
import pytest

from jeph2sworm.utils.validators import (
    validate_project_name,
    validate_url,
    validate_filepath,
    validate_password_strength,
    validate_agent_role,
)
from jeph2sworm.utils.helpers import (
    generate_id,
    extract_json_from_text,
    detect_language,
    truncate,
    sanitize_filename,
)


class TestValidators:
    """Tests for input validators."""

    def test_valid_project_name(self):
        ok, _ = validate_project_name("my-app")
        assert ok

    def test_invalid_project_name_empty(self):
        ok, msg = validate_project_name("")
        assert not ok
        assert "empty" in msg.lower()

    def test_invalid_project_name_starts_with_number(self):
        ok, _ = validate_project_name("123app")
        assert not ok

    def test_valid_url(self):
        ok, _ = validate_url("https://example.com")
        assert ok

    def test_invalid_url(self):
        ok, _ = validate_url("not-a-url")
        assert not ok

    def test_valid_filepath(self, workspace_dir):
        filepath = os.path.join(workspace_dir, "test.py")
        ok, _ = validate_filepath(filepath, workspace_dir=workspace_dir)
        assert ok

    def test_filepath_outside_workspace(self, workspace_dir):
        ok, _ = validate_filepath("/etc/passwd", workspace_dir=workspace_dir)
        assert not ok

    def test_strong_password(self):
        # 32+ chars, mixed case, digits, special
        pwd = "Abc123!@#defGHI456$%^jklMNO789&*("
        ok, _ = validate_password_strength(pwd)
        assert ok

    def test_weak_password(self):
        ok, _ = validate_password_strength("short")
        assert not ok

    def test_valid_agent_role(self):
        ok, _ = validate_agent_role("backend")
        assert ok

    def test_invalid_agent_role(self):
        ok, _ = validate_agent_role("invalid")
        assert not ok


class TestHelpers:
    """Tests for utility helpers."""

    def test_generate_id(self):
        id1 = generate_id("task")
        assert id1.startswith("task_")
        assert len(id1) > 5

    def test_generate_id_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_extract_json_direct(self):
        result = extract_json_from_text('{"key": "value"}')
        assert result == {"key": "value"}

    def test_extract_json_from_markdown(self):
        text = 'Here is the result:\n```json\n{"key": "value"}\n```\nDone.'
        result = extract_json_from_text(text)
        assert result == {"key": "value"}

    def test_extract_json_invalid(self):
        result = extract_json_from_text("no json here")
        assert result is None

    def test_detect_language(self):
        assert detect_language("app.py") == "python"
        assert detect_language("index.ts") == "typescript"
        assert detect_language("style.css") == "css"
        assert detect_language("README.md") == "markdown"

    def test_truncate(self):
        assert truncate("short", 100) == "short"
        assert len(truncate("a" * 1000, 100)) == 100

    def test_sanitize_filename(self):
        assert sanitize_filename('file<name>.txt') == "file_name_.txt"
        assert sanitize_filename("normal.py") == "normal.py"
