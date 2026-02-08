"""Tests for Brain module - memory, context_manager, task_board, decision_log."""

import json
import os
import pytest
import asyncio

from jeph2sworm.brain.memory import Brain
from jeph2sworm.brain.context_manager import ContextManager
from jeph2sworm.brain.task_board import TaskBoard, TaskPriority, TaskStatus
from jeph2sworm.brain.decision_log import DecisionLog


class TestBrainMemory:
    """Tests for Brain memory persistence and data access."""

    @pytest.fixture
    def brain(self, brain_dir):
        return Brain(brain_dir)

    def test_brain_initialization(self, brain):
        assert brain.data is not None
        assert "project_spec" in brain.data
        assert "task_board" in brain.data

    def test_brain_update_section(self, brain):
        brain.data["project_spec"] = {"name": "test", "type": "web"}
        assert brain.data["project_spec"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_brain_save_and_load(self, brain):
        brain.data["project_spec"] = {"name": "persist-test"}
        await brain.save()

        brain2 = Brain(brain.brain_dir)
        await brain2.load()
        assert brain2.data["project_spec"]["name"] == "persist-test"


class TestContextManager:
    """Tests for per-agent context extraction."""

    @pytest.fixture
    def ctx_manager(self, brain_dir):
        brain = Brain(brain_dir)
        brain.data["project_spec"] = {"name": "test-app"}
        brain.data["task_board"] = {
            "backlog": [{"title": "task1", "assigned_to": "backend"}],
            "assigned": [],
            "in_progress": [],
        }
        return ContextManager(brain)

    def test_get_context_for_role(self, ctx_manager):
        ctx = ctx_manager.get_context("backend")
        assert "project_spec" in ctx
        assert "my_tasks" in ctx

    def test_get_tasks_for_role(self, ctx_manager):
        tasks = ctx_manager._get_tasks_for_role("backend")
        assert len(tasks) == 1
        assert tasks[0]["title"] == "task1"


class TestTaskBoard:
    """Tests for task management."""

    @pytest.fixture
    def board(self):
        return TaskBoard()

    def test_create_task(self, board):
        task = board.create_task("Test task", priority=TaskPriority.HIGH)
        assert task.title == "Test task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.BACKLOG

    def test_assign_task(self, board):
        task = board.create_task("Task")
        board.assign_task(task.id, "backend")
        assert task.assigned_to == "backend"
        assert task.status == TaskStatus.ASSIGNED

    def test_complete_task(self, board):
        task = board.create_task("Task", assigned_to="backend")
        board.start_task(task.id)
        board.complete_task(task.id, files_affected=["api.py"])
        assert task.status == TaskStatus.DONE
        assert "api.py" in task.files_affected

    def test_get_pending_tasks(self, board):
        board.create_task("T1", assigned_to="backend", priority=TaskPriority.LOW)
        board.create_task("T2", assigned_to="backend", priority=TaskPriority.CRITICAL)
        pending = board.get_pending_tasks("backend")
        assert len(pending) == 2
        assert pending[0].priority == TaskPriority.CRITICAL

    def test_task_dependencies(self, board):
        t1 = board.create_task("First")
        t2 = board.create_task("Second", dependencies=[t1.id])
        result = board.start_task(t2.id)
        assert result.status == TaskStatus.BLOCKED

    def test_board_summary(self, board):
        board.create_task("T1")
        board.create_task("T2", assigned_to="backend")
        summary = board.get_summary()
        assert summary["total"] == 2


class TestDecisionLog:
    """Tests for decision tracking."""

    @pytest.fixture
    def log(self, tmp_path):
        return DecisionLog(persist_path=str(tmp_path / "decisions.json"))

    def test_record_decision(self, log):
        d = log.record(
            title="Use PostgreSQL",
            description="We chose PostgreSQL as the database",
            rationale="Best for relational data",
            decided_by="brain",
            category="architecture",
        )
        assert d.id == "DEC-0001"
        assert d.status == "active"

    def test_get_active_decisions(self, log):
        log.record("D1", "desc", "reason", "brain")
        log.record("D2", "desc", "reason", "brain")
        active = log.get_active()
        assert len(active) == 2

    def test_supersede_decision(self, log):
        d1 = log.record("Old choice", "desc", "reason", "brain")
        d2 = log.record("New choice", "desc", "better reason", "brain")
        log.supersede(d1.id, d2)
        assert d1.status == "superseded"

    def test_decision_persistence(self, log, tmp_path):
        log.record("Persistent", "desc", "reason", "brain")
        log2 = DecisionLog(persist_path=str(tmp_path / "decisions.json"))
        asyncio.get_event_loop().run_until_complete(log2.initialize())
        assert len(log2.get_active()) == 1
