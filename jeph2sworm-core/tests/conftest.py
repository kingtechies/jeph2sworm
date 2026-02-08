"""Shared test fixtures for jeph2sworm test suite."""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio


@pytest.fixture
def workspace_dir(tmp_path) -> str:
    """Create a temporary workspace directory."""
    ws = tmp_path / "test_workspace"
    ws.mkdir()
    return str(ws)


@pytest.fixture
def brain_dir(tmp_path) -> str:
    """Create a temporary brain storage directory."""
    bd = tmp_path / ".jeph2sworm"
    bd.mkdir()
    return str(bd)


@pytest.fixture
def sample_project_spec() -> dict:
    """Sample project specification for testing."""
    return {
        "name": "test-app",
        "description": "A test application",
        "type": "web",
        "framework": "nextjs",
        "features": ["auth", "dashboard", "api"],
        "database": "postgresql",
    }


@pytest.fixture
def sample_task() -> dict:
    """Sample task data for testing."""
    return {
        "title": "Create user authentication",
        "description": "Implement JWT-based auth with login/register",
        "priority": "high",
        "assigned_to": "backend",
    }


@pytest.fixture
def sample_messages() -> list:
    """Sample LLM conversation messages."""
    return [
        {"role": "system", "content": "You are a backend developer."},
        {"role": "user", "content": "Create a REST API for users."},
    ]


@pytest.fixture
def env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("JEPH2SWORM_HOST", "localhost")
    monkeypatch.setenv("JEPH2SWORM_PORT", "8765")
    monkeypatch.setenv("DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini")


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
