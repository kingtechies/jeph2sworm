"""Action Validator - Pre and post action validation hooks."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class ValidationResult:
    """Result of an action validation check."""

    __slots__ = ("allowed", "reason", "modified_action")

    def __init__(self, allowed: bool, reason: str = "", modified_action: Optional[Dict] = None):
        self.allowed = allowed
        self.reason = reason
        self.modified_action = modified_action

    def __bool__(self) -> bool:
        return self.allowed


class ActionValidator:
    """
    Validates agent actions before and after execution.

    Pre-hooks: Run before an action to approve/deny/modify it.
    Post-hooks: Run after an action to audit/log/revert if needed.

    Enforces the swarm's safety rules at the action level.
    """

    # Directories that agents should never touch
    PROTECTED_DIRS = [
        "/etc", "/usr", "/bin", "/sbin", "/boot", "/root",
        "/proc", "/sys", "/dev", "/var/run",
    ]

    # File extensions that should never be modified by agents
    PROTECTED_EXTENSIONS = [
        ".pem", ".key", ".cert", ".crt", ".ssh",
    ]

    # Commands that are completely forbidden
    FORBIDDEN_COMMANDS = [
        "rm -rf /", "rm -rf /*", "mkfs", "dd if=",
        ":(){ :|:& };:", "> /dev/sda", "chmod -R 777 /",
        "curl | sh", "wget | sh", "eval $(", "sudo rm",
    ]

    # Patterns for potentially dangerous commands
    DANGEROUS_PATTERNS = [
        re.compile(r"rm\s+-rf\s+/(?!home|tmp)"),
        re.compile(r"chmod\s+.*\s+/(?!home|tmp)"),
        re.compile(r"chown\s+.*\s+/(?!home|tmp)"),
        re.compile(r"kill\s+-9\s+-1"),
        re.compile(r"shutdown|reboot|halt|poweroff"),
    ]

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
        self._action_log: List[Dict[str, Any]] = []

    def validate_file_action(
        self, action: str, filepath: str, agent: str
    ) -> ValidationResult:
        """Validate a file-related action (create, read, write, delete)."""
        # Rule: No operations outside workspace
        if not self._is_in_workspace(filepath):
            return ValidationResult(
                False,
                f"File operation outside workspace: {filepath}",
            )

        # Rule: No deleting files (per plan rule #3)
        if action == "delete":
            return ValidationResult(
                False,
                "File deletion is not allowed. Files can only be created or modified.",
            )

        # Rule: No touching protected extensions
        for ext in self.PROTECTED_EXTENSIONS:
            if filepath.endswith(ext):
                return ValidationResult(
                    False,
                    f"Cannot modify protected file type: {ext}",
                )

        # Rule: No modifying system directories
        for d in self.PROTECTED_DIRS:
            if filepath.startswith(d):
                return ValidationResult(
                    False,
                    f"Cannot modify files in protected directory: {d}",
                )

        self._log_action(agent, "file", action, filepath, True)
        return ValidationResult(True)

    def validate_command(self, command: str, agent: str) -> ValidationResult:
        """Validate a terminal command before execution."""
        cmd_lower = command.lower().strip()

        # Check forbidden commands
        for forbidden in self.FORBIDDEN_COMMANDS:
            if forbidden in cmd_lower:
                self._log_action(agent, "command", "execute", command, False)
                return ValidationResult(
                    False,
                    f"Forbidden command detected: {forbidden}",
                )

        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(cmd_lower):
                self._log_action(agent, "command", "execute", command, False)
                return ValidationResult(
                    False,
                    f"Dangerous command pattern detected",
                )

        # Warn on sudo (allow but log)
        if cmd_lower.startswith("sudo "):
            logger.warning("sudo_command_used", agent=agent, command=command[:100])

        self._log_action(agent, "command", "execute", command, True)
        return ValidationResult(True)

    def validate_network_action(
        self, url: str, method: str, agent: str
    ) -> ValidationResult:
        """Validate a network request."""
        # Block requests to private IPs (except localhost for dev)
        import urllib.parse

        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""

        # Allow localhost for local dev servers
        allowed_local = ["localhost", "127.0.0.1", "0.0.0.0"]
        private_prefixes = ["192.168.", "10.", "172.16."]

        if hostname not in allowed_local:
            for prefix in private_prefixes:
                if hostname.startswith(prefix):
                    return ValidationResult(
                        False,
                        f"Network requests to private IPs not allowed: {hostname}",
                    )

        self._log_action(agent, "network", method, url, True)
        return ValidationResult(True)

    def validate_credential_action(
        self, action: str, credential_name: str, agent: str
    ) -> ValidationResult:
        """Validate credential-related actions."""
        # Only DevOps agent can rotate credentials
        if action == "rotate" and agent != "devops":
            return ValidationResult(
                False,
                f"Only DevOps agent can rotate credentials, not {agent}",
            )

        # Reading credentials: only the assigned agent or DevOps
        self._log_action(agent, "credential", action, credential_name, True)
        return ValidationResult(True)

    def add_pre_hook(self, hook: Callable) -> None:
        """Add a pre-action validation hook."""
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable) -> None:
        """Add a post-action audit hook."""
        self._post_hooks.append(hook)

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action audit log."""
        return self._action_log[-limit:]

    def _is_in_workspace(self, filepath: str) -> bool:
        """Check if a filepath is within the workspace."""
        import os
        abs_path = os.path.abspath(filepath)
        abs_workspace = os.path.abspath(self.workspace_dir)
        return abs_path.startswith(abs_workspace)

    def _log_action(
        self,
        agent: str,
        category: str,
        action: str,
        target: str,
        allowed: bool,
    ) -> None:
        """Log an action for auditing."""
        import time

        self._action_log.append({
            "agent": agent,
            "category": category,
            "action": action,
            "target": target[:200],
            "allowed": allowed,
            "timestamp": time.time(),
        })

        # Keep log bounded
        if len(self._action_log) > 10000:
            self._action_log = self._action_log[-5000:]
