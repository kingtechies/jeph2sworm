"""Rules Engine - hard-coded safety rules that cannot be overridden."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


class RuleViolation(Exception):
    """Raised when an agent action violates a safety rule."""

    def __init__(self, rule: str, action: str, detail: str) -> None:
        self.rule = rule
        self.action = action
        self.detail = detail
        super().__init__(f"Rule violation [{rule}]: {detail} (action: {action})")


class RulesEngine:
    """
    Enforces 8 hard-coded safety rules before and after every agent action.

    Rules:
    1. Never delete user data or system files
    2. Never corrupt the project (backup before writes)
    3. No hallucination in critical paths
    4. Stay in scope (workspace only)
    5. Transparent operations (all actions logged)
    6. Credential security (strong passwords only)
    7. No external data exfiltration
    8. Graceful failure
    """

    DANGEROUS_COMMANDS = [
        r"\brm\s+-rf\s+/",
        r"\brm\s+-rf\s+~",
        r"\brm\s+-rf\s+\*",
        r"\bmkfs\b",
        r"\bdd\s+if=",
        r"\bformat\b.*\b[A-Z]:",
        r">\s*/dev/sd",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bsystemctl\s+(stop|disable)\s+(ssh|sshd|network)",
        r"\biptables\s+-F",
        r"\bchmod\s+777\s+/",
        r"\bchown\s+.*\s+/",
        r"\bcurl\b.*\|\s*(bash|sh)",
        r"\bwget\b.*\|\s*(bash|sh)",
    ]

    BLOCKED_DOMAINS = [
        "pastebin.com",
        "hastebin.com",
        "requestbin.com",
    ]

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._violations: list[dict] = []

    # ---- Pre-execution Checks ----

    def validate_file_write(self, file_path: str | Path) -> None:
        """RULE 1 & 4: Ensure file is within workspace."""
        resolved = Path(file_path).resolve()
        if not str(resolved).startswith(str(self.workspace_root)):
            raise RuleViolation(
                rule="STAY_IN_SCOPE",
                action="file_write",
                detail=f"Cannot write outside workspace: {file_path}",
            )

    def validate_file_read(self, file_path: str | Path) -> None:
        """RULE 4: Ensure reads are within workspace."""
        resolved = Path(file_path).resolve()
        if not str(resolved).startswith(str(self.workspace_root)):
            raise RuleViolation(
                rule="STAY_IN_SCOPE",
                action="file_read",
                detail=f"Cannot read outside workspace: {file_path}",
            )

    def validate_file_delete(self, file_path: str | Path) -> None:
        """RULE 1: Block all file deletions (archive instead)."""
        raise RuleViolation(
            rule="NEVER_DELETE",
            action="file_delete",
            detail=f"Deletion prohibited. Archive the file instead: {file_path}",
        )

    def validate_command(self, command: str) -> None:
        """RULE 1 & 4: Block dangerous terminal commands."""
        for pattern in self.DANGEROUS_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                raise RuleViolation(
                    rule="NEVER_DELETE",
                    action="terminal_command",
                    detail=f"Dangerous command blocked: {command}",
                )

    def validate_url(self, url: str) -> None:
        """RULE 7: Block requests to unauthorized domains."""
        for domain in self.BLOCKED_DOMAINS:
            if domain in url:
                raise RuleViolation(
                    rule="NO_EXFILTRATION",
                    action="network_request",
                    detail=f"Blocked domain: {domain}",
                )

    def validate_password_strength(self, password: str) -> None:
        """RULE 6: Ensure generated passwords meet security requirements."""
        if len(password) < 32:
            raise RuleViolation(
                rule="CREDENTIAL_SECURITY",
                action="password_generation",
                detail=f"Password too short: {len(password)} chars (minimum 32)",
            )

        checks = {
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "digit": any(c.isdigit() for c in password),
            "symbol": any(not c.isalnum() for c in password),
        }
        missing = [k for k, v in checks.items() if not v]
        if missing:
            raise RuleViolation(
                rule="CREDENTIAL_SECURITY",
                action="password_generation",
                detail=f"Password missing: {', '.join(missing)}",
            )

    def validate_env_not_hardcoded(self, file_content: str, file_path: str) -> list[str]:
        """RULE 6: Check that secrets aren't hardcoded in source files."""
        warnings = []
        # Skip ai.env and .env files themselves
        if file_path.endswith(".env") or file_path.endswith("ai.env"):
            return warnings

        # Look for common hardcoded secret patterns
        patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Possible hardcoded password"),
            (r'secret\s*=\s*["\'][^"\']{8,}["\']', "Possible hardcoded secret"),
            (r'api_key\s*=\s*["\'][^"\']{8,}["\']', "Possible hardcoded API key"),
            (r'token\s*=\s*["\'][^"\']{8,}["\']', "Possible hardcoded token"),
        ]
        for pattern, msg in patterns:
            if re.search(pattern, file_content, re.IGNORECASE):
                warnings.append(f"{msg} in {file_path}")

        return warnings

    # ---- Violation Tracking ----

    def record_violation(self, violation: RuleViolation) -> None:
        self._violations.append({
            "rule": violation.rule,
            "action": violation.action,
            "detail": violation.detail,
        })

    def get_violations(self) -> list[dict]:
        return list(self._violations)

    def clear_violations(self) -> None:
        self._violations.clear()
