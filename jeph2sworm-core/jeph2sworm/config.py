"""Configuration management for Jeph2Sworm."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False

    # LLM defaults
    default_provider: str = "openai"
    default_model: str = "gpt-4o"

    # Agent config
    max_concurrent_agents: int = 7
    test_cycles: int = 120

    # Paths
    workspace_dir: Optional[str] = None
    brain_dir: str = ".jeph2sworm"

    # Browser extension
    browser_extension_port: int = 9222

    # Security
    machine_password: Optional[str] = Field(default=None, exclude=True)

    model_config = {"env_prefix": "J2S_", "env_file": ".env", "extra": "ignore"}

    def get_workspace(self) -> Path:
        return Path(self.workspace_dir) if self.workspace_dir else Path.cwd()

    def get_brain_path(self) -> Path:
        return self.get_workspace() / self.brain_dir


settings = Settings()
