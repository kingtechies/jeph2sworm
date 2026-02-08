"""Brain - the central memory and state management system for the swarm."""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiofiles
import structlog

from jeph2sworm.events import EventType, SwarmEvent
from jeph2sworm.events.event_bus import event_bus

logger = structlog.get_logger()


class Brain:
    """
    Central shared memory for all agents.

    Stores project spec, architecture, task board, API contracts,
    agent states, decision log, error log, test results, credentials
    reference, and conversation history.

    All agents read from and write to the Brain. It is the single
    source of truth for the entire project.
    """

    DEFAULT_SECTIONS = {
        "project_spec": {},
        "architecture": {},
        "task_board": {"backlog": [], "assigned": [], "in_progress": [], "in_review": [], "done": [], "blocked": []},
        "api_contracts": [],
        "agent_states": {},
        "decisions_log": [],
        "errors_log": [],
        "test_results": [],
        "credentials": [],
        "conversation_history": {"messages": []},
    }

    def __init__(self, brain_dir: Path | str) -> None:
        self.brain_dir = Path(brain_dir) if isinstance(brain_dir, str) else brain_dir
        self._lock = asyncio.Lock()
        # Start with default structure so all sections are immediately accessible
        self._cache: dict[str, Any] = {k: self._deep_copy(v) for k, v in self.DEFAULT_SECTIONS.items()}

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """Simple deep copy for JSON-serializable objects."""
        import copy
        return copy.deepcopy(obj)

    # ---- data property for backward compat ----

    @property
    def data(self) -> dict[str, Any]:
        """Public accessor for cached brain data (sync, backward-compat)."""
        return self._cache

    # ---- load / save aliases ----

    async def load(self) -> None:
        """Load brain state from disk (alias for initialize)."""
        await self.initialize()

    async def save(self) -> None:
        """Persist all cached brain data to disk (alias for backup)."""
        for section, content in self._cache.items():
            if section.startswith("_"):
                continue
            path = self.brain_dir / f"{section}.json"
            await self._write_json(path, content)
        await logger.ainfo("brain_saved", path=str(self.brain_dir))

    # ---- Stats ----

    def get_stats(self) -> dict:
        """Return summary statistics about the brain state."""
        board = self._cache.get("task_board", {})
        return {
            "sections": list(self._cache.keys()),
            "tasks_backlog": len(board.get("backlog", [])),
            "tasks_in_progress": len(board.get("in_progress", [])),
            "tasks_done": len(board.get("done", [])),
            "tasks_blocked": len(board.get("blocked", [])),
            "agents": len(self._cache.get("agent_states", {})),
            "errors": len(self._cache.get("errors_log", [])),
            "decisions": len(self._cache.get("decisions_log", [])),
            "test_runs": len(self._cache.get("test_results", [])),
        }

    # ---- Error shortcut ----

    async def add_error(
        self,
        error: str,
        file_path: str = "",
        agent_id: str = "system",
        details: str = "",
        **kwargs,
    ) -> None:
        """Convenience method that delegates to log_error."""
        await self.log_error(
            error=error,
            context=f"file={file_path} {details}".strip(),
            fixed_by=agent_id,
        )

    # ---- Initialization ----

    async def initialize(self) -> None:
        """Create Brain directory and default data files."""
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        (self.brain_dir / "backups").mkdir(exist_ok=True)
        (self.brain_dir / "test_evidence").mkdir(exist_ok=True)

        defaults = {
            "project_spec": {
                "name": "",
                "description": "",
                "features": [],
                "tech_stack": {},
                "architecture": {},
                "constraints": [],
                "logo": None,
                "branding": {},
            },
            "architecture": {
                "frontend_framework": None,
                "backend_framework": None,
                "database": None,
                "api_design": "REST",
                "folder_structure": {},
                "deployment_target": None,
                "diagrams": [],
            },
            "task_board": {
                "backlog": [],
                "assigned": [],
                "in_progress": [],
                "in_review": [],
                "done": [],
                "blocked": [],
            },
            "api_contracts": {
                "endpoints": [],
                "shared_types": {},
            },
            "agent_states": {},
            "decisions_log": [],
            "errors_log": [],
            "test_results": [],
            "credentials": [],
            "conversation_history": {
                "messages": [],
                "clarifications": [],
            },
        }

        for name, data in defaults.items():
            path = self.brain_dir / f"{name}.json"
            if path.exists():
                # Load persisted data from disk
                self._cache[name] = await self._read_json(path)
            else:
                # Write default and cache it
                await self._write_json(path, data)
                self._cache[name] = self._deep_copy(data)

        await logger.ainfo("brain_initialized", path=str(self.brain_dir))

    # ---- Core Read/Write ----

    async def read(self, section: str) -> Any:
        """Read a Brain section. Returns cached data if available."""
        if section in self._cache:
            return self._cache[section]

        path = self.brain_dir / f"{section}.json"
        if not path.exists():
            return None

        data = await self._read_json(path)
        self._cache[section] = data
        return data

    async def write(self, section: str, data: Any, agent_id: str = "system") -> None:
        """Write to a Brain section. Updates cache and persists to disk."""
        async with self._lock:
            path = self.brain_dir / f"{section}.json"
            await self._write_json(path, data)
            self._cache[section] = data

        await event_bus.emit(
            EventType.BRAIN_UPDATED,
            source=agent_id,
            data={"section": section},
        )

    async def update(
        self, section: str, key: str, value: Any, agent_id: str = "system"
    ) -> None:
        """Update a specific key within a Brain section."""
        data = await self.read(section) or {}
        if isinstance(data, dict):
            data[key] = value
            await self.write(section, data, agent_id)

    async def append(self, section: str, item: Any, agent_id: str = "system") -> None:
        """Append an item to a list-type Brain section or a list within a dict."""
        data = await self.read(section)
        if isinstance(data, list):
            data.append(item)
            await self.write(section, data, agent_id)
        elif isinstance(data, dict):
            # For sections like decisions_log that are stored as a list at root
            # This is handled by the caller specifying the key
            pass

    # ---- Project Spec ----

    async def set_project_spec(self, spec: dict, agent_id: str = "system") -> None:
        """Set the full project specification."""
        await self.write("project_spec", spec, agent_id)

    async def get_project_spec(self) -> dict:
        return await self.read("project_spec") or {}

    # ---- Architecture ----

    async def set_architecture(self, arch: dict, agent_id: str = "system") -> None:
        await self.write("architecture", arch, agent_id)

    async def get_architecture(self) -> dict:
        return await self.read("architecture") or {}

    # ---- Task Board ----

    BOARD_COLUMNS = ("backlog", "assigned", "in_progress", "in_review", "done", "blocked")

    def _empty_board(self) -> dict:
        return {col: [] for col in self.BOARD_COLUMNS}

    async def add_task(
        self,
        task: dict,
        status: str = "backlog",
        agent_id: str = "system",
    ) -> None:
        """Add a task to the task board."""
        board = await self.read("task_board") or self._empty_board()
        # Ensure all columns exist (migration from older brain files)
        for col in self.BOARD_COLUMNS:
            board.setdefault(col, [])
        task.setdefault("id", f"task-{len(board['backlog']) + len(board['assigned']) + len(board['in_progress']) + len(board['done']) + 1:03d}")
        task.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        board[status].append(task)
        await self.write("task_board", board, agent_id)

    async def assign_task(
        self, task_id: str, agent_id: str
    ) -> None:
        """Move a task from backlog to assigned for a specific agent."""
        board = await self.read("task_board") or self._empty_board()
        for col in self.BOARD_COLUMNS:
            board.setdefault(col, [])
        task = None
        for t in board.get("backlog", []):
            if t.get("id") == task_id:
                task = t
                board["backlog"].remove(t)
                break
        if task:
            task["assigned_to"] = agent_id
            task["assigned_at"] = datetime.now(timezone.utc).isoformat()
            board["assigned"].append(task)
            await self.write("task_board", board, "task-scheduler")

    async def move_task(
        self, task_id: str, to_status: str, agent_id: str = "system"
    ) -> None:
        """Move a task between board columns."""
        board = await self.read("task_board") or self._empty_board()
        for col in self.BOARD_COLUMNS:
            board.setdefault(col, [])
        task = None
        for status in self.BOARD_COLUMNS:
            for t in board.get(status, []):
                if t.get("id") == task_id:
                    task = t
                    board[status].remove(t)
                    break
            if task:
                break
        if task:
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            board[to_status].append(task)
            await self.write("task_board", board, agent_id)

    async def get_task_board(self) -> dict:
        return await self.read("task_board") or {}

    # ---- API Contracts ----

    async def add_api_endpoint(self, endpoint: dict, agent_id: str = "system") -> None:
        """Register an API endpoint contract."""
        contracts = await self.read("api_contracts") or {"endpoints": [], "shared_types": {}}
        contracts["endpoints"].append(endpoint)
        await self.write("api_contracts", contracts, agent_id)

        await event_bus.emit(
            EventType.API_ENDPOINT_READY,
            source=agent_id,
            data=endpoint,
        )

    async def get_api_contracts(self) -> dict:
        return await self.read("api_contracts") or {"endpoints": [], "shared_types": {}}

    # ---- Agent States ----

    async def set_agent_state(
        self,
        agent_id: str,
        role: str,
        status: str,
        current_task: Optional[str] = None,
        files_modified: Optional[list[str]] = None,
    ) -> None:
        """Update an agent's state in the Brain."""
        states = await self.read("agent_states") or {}
        states[agent_id] = {
            "agent_id": agent_id,
            "role": role,
            "status": status,
            "current_task": current_task,
            "last_update": datetime.now(timezone.utc).isoformat(),
            "files_modified": files_modified or [],
        }
        await self.write("agent_states", states, agent_id)

    async def get_agent_states(self) -> dict:
        return await self.read("agent_states") or {}

    # ---- Decision Log ----

    async def log_decision(
        self, decision: str, reasoning: str, decided_by: str
    ) -> None:
        """Log an architectural or project decision."""
        log = await self.read("decisions_log") or []
        log.append({
            "decision": decision,
            "reasoning": reasoning,
            "decided_by": decided_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.write("decisions_log", log, decided_by)

    # ---- Error Log ----

    async def log_error(
        self,
        error: str,
        context: str,
        fix_applied: Optional[str] = None,
        fixed_by: Optional[str] = None,
    ) -> None:
        """Log an error and its resolution."""
        log = await self.read("errors_log") or []
        log.append({
            "error": error,
            "context": context,
            "fix_applied": fix_applied,
            "fixed_by": fixed_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.write("errors_log", log, fixed_by or "system")

    # ---- Test Results ----

    async def add_test_result(self, result: dict, agent_id: str = "tester") -> None:
        """Store a test run result."""
        results = await self.read("test_results") or []
        result.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        results.append(result)
        await self.write("test_results", results, agent_id)

    async def get_test_results(self) -> list[dict]:
        return await self.read("test_results") or []

    # ---- Credentials ----

    async def register_credential(
        self,
        key_name: str,
        purpose: str,
        created_by: str,
        used_in_files: Optional[list[str]] = None,
    ) -> None:
        """Register a credential reference (actual value in ai.env)."""
        creds = await self.read("credentials") or []
        creds.append({
            "key_name": key_name,
            "purpose": purpose,
            "created_by": created_by,
            "used_in_files": used_in_files or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await self.write("credentials", creds, created_by)

        await event_bus.emit(
            EventType.CREDENTIAL_CREATED,
            source=created_by,
            data={"key_name": key_name, "purpose": purpose},
        )

    # ---- Conversation ----

    async def add_message(
        self, role: str, content: str, agent_id: Optional[str] = None
    ) -> None:
        """Add a message to conversation history."""
        history = await self.read("conversation_history") or {
            "messages": [], "clarifications": []
        }
        history["messages"].append({
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.write("conversation_history", history, agent_id or "system")

    async def get_conversation(self) -> dict:
        return await self.read("conversation_history") or {"messages": [], "clarifications": []}

    # ---- Context for Agents ----

    async def get_context_for_agent(self, role: str) -> dict:
        """Get role-specific context summary for an agent."""
        spec = await self.get_project_spec()
        arch = await self.get_architecture()
        board = await self.get_task_board()
        contracts = await self.get_api_contracts()
        states = await self.get_agent_states()

        base = {
            "project_name": spec.get("name", ""),
            "project_description": spec.get("description", ""),
            "tech_stack": spec.get("tech_stack", {}),
            "task_board_summary": {
                "backlog": len(board.get("backlog", [])),
                "in_progress": len(board.get("in_progress", [])),
                "done": len(board.get("done", [])),
                "blocked": len(board.get("blocked", [])),
            },
            "agent_states": states,
        }

        # Role-specific context enrichment
        if role in ("backend", "frontend"):
            base["api_contracts"] = contracts
            base["architecture"] = arch
        elif role == "brain":
            base["full_spec"] = spec
            base["full_architecture"] = arch
            base["api_contracts"] = contracts
        elif role == "pm":
            conversation = await self.get_conversation()
            base["conversation_history"] = conversation["messages"][-20:]
        elif role == "ux":
            base["branding"] = spec.get("branding", {})
            base["features"] = spec.get("features", [])
        elif role == "tester":
            base["api_contracts"] = contracts
            base["test_results"] = (await self.get_test_results())[-10:]
        elif role == "devops":
            base["architecture"] = arch
            creds = await self.read("credentials") or []
            base["credentials"] = [c["key_name"] for c in creds]

        return base

    # ---- Backup ----

    async def backup(self, label: str = "auto") -> Path:
        """Create a timestamped backup of all Brain data."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = self.brain_dir / "backups" / f"{label}_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for json_file in self.brain_dir.glob("*.json"):
            data = await self._read_json(json_file)
            await self._write_json(backup_dir / json_file.name, data)

        await logger.ainfo("brain_backup_created", path=str(backup_dir))
        return backup_dir

    # ---- Helpers ----

    async def _read_json(self, path: Path) -> Any:
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))
