"""Validators - Input validation utilities for the swarm."""

from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse


def validate_project_name(name: str) -> Tuple[bool, str]:
    """
    Validate a project name.

    Rules:
    - 2-64 characters
    - Alphanumeric, hyphens, underscores only
    - Must start with a letter
    """
    if not name:
        return False, "Project name cannot be empty"

    if len(name) < 2:
        return False, "Project name must be at least 2 characters"

    if len(name) > 64:
        return False, "Project name must be 64 characters or less"

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        return False, "Project name must start with a letter and contain only letters, numbers, hyphens, underscores"

    return True, ""


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate a URL."""
    if not url:
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"URL scheme must be http or https, got: {parsed.scheme}"
        if not parsed.netloc:
            return False, "URL must have a valid hostname"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def validate_filepath(
    filepath: str,
    workspace_dir: Optional[str] = None,
    must_exist: bool = False,
) -> Tuple[bool, str]:
    """
    Validate a file path.

    Rules:
    - Must be within workspace_dir if specified
    - No path traversal (../)
    - No null bytes
    - Optionally check existence
    """
    if not filepath:
        return False, "File path cannot be empty"

    if "\x00" in filepath:
        return False, "File path contains null bytes"

    # Normalize
    normalized = os.path.normpath(filepath)

    # Check for path traversal
    if ".." in normalized.split(os.sep):
        return False, "Path traversal (..) not allowed"

    # Check workspace bounds
    if workspace_dir:
        abs_path = os.path.abspath(normalized)
        abs_workspace = os.path.abspath(workspace_dir)
        if not abs_path.startswith(abs_workspace):
            return False, "File path outside workspace directory"

    # Check existence
    if must_exist and not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    return True, ""


def validate_port(port: int) -> Tuple[bool, str]:
    """Validate a port number."""
    if not isinstance(port, int):
        return False, "Port must be an integer"
    if port < 1 or port > 65535:
        return False, "Port must be between 1 and 65535"
    if port < 1024:
        return False, "Ports below 1024 require elevated privileges"
    return True, ""


def validate_agent_role(role: str) -> Tuple[bool, str]:
    """Validate an agent role name."""
    valid_roles = {"pm", "brain", "backend", "frontend", "ux", "tester", "devops"}
    if role not in valid_roles:
        return False, f"Invalid agent role: {role}. Must be one of: {', '.join(sorted(valid_roles))}"
    return True, ""


def validate_task_priority(priority: str) -> Tuple[bool, str]:
    """Validate a task priority value."""
    valid = {"critical", "high", "medium", "low"}
    if priority not in valid:
        return False, f"Invalid priority: {priority}. Must be one of: {', '.join(sorted(valid))}"
    return True, ""


def validate_llm_provider(provider: str) -> Tuple[bool, str]:
    """Validate an LLM provider name."""
    valid = {
        "openai", "anthropic", "xai", "gemini", "google",
        "deepseek", "mistral", "together_ai", "cohere",
    }
    if provider not in valid:
        return False, f"Invalid LLM provider: {provider}. Must be one of: {', '.join(sorted(valid))}"
    return True, ""


def validate_password_strength(password: str, min_length: int = 32) -> Tuple[bool, str]:
    """
    Validate password strength per the swarm's 128-bit entropy requirement.

    Rules:
    - At least min_length characters (default 32)
    - Must contain uppercase, lowercase, digits, special chars
    - No more than 2 consecutive repeated characters
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"

    checks = {
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password)),
    }

    missing = [k for k, v in checks.items() if not v]
    if missing:
        return False, f"Password missing: {', '.join(missing)}"

    # Check for repeated characters
    if re.search(r"(.)\1{2,}", password):
        return False, "Password has too many consecutive repeated characters"

    return True, ""


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    sanitized = re.sub(r"\s+", "_", sanitized)
    sanitized = sanitized.strip("._")
    return sanitized[:255]  # Max filename length
