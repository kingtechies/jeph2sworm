"""Tests for Agent module - base_agent, pm_agent, and specialized agents."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from jeph2sworm.agents.base_agent import AgentRole, AgentStatus, BaseAgent
from jeph2sworm.agents.pm_agent import PMAgent
from jeph2sworm.agents.backend_agent import BackendAgent
from jeph2sworm.agents.frontend_agent import FrontendAgent
from jeph2sworm.agents.ux_agent import UXAgent
from jeph2sworm.agents.tester_agent import TesterAgent
from jeph2sworm.agents.devops_agent import DevOpsAgent
from jeph2sworm.events import EventType
from jeph2sworm.events.event_bus import event_bus


# ---- Mock Helpers ----

def make_mock_brain(brain_dir: str = "/tmp/test-brain"):
    """Create a mock Brain with all required async methods."""
    brain = MagicMock()
    brain.brain_dir = brain_dir
    brain.data = {"project_spec": {}, "task_board": {}}
    brain.set_agent_state = AsyncMock()
    brain.get_context_for_agent = AsyncMock(return_value={
        "project_name": "test-app",
        "task_board_summary": {"backlog": 0, "in_progress": 0, "done": 0},
        "conversation_history": [],
        "agent_states": {},
    })
    brain.get_project_spec = AsyncMock(return_value={
        "name": "test-app",
        "framework": "nextjs",
        "features": ["auth", "dashboard"],
    })
    brain.add_task = AsyncMock()
    brain.move_task = AsyncMock()
    brain.log_error = AsyncMock()
    brain.add_message = AsyncMock()
    brain.save = AsyncMock()
    brain.load = AsyncMock()
    return brain


def make_mock_llm():
    """Create a mock LLMRouter."""
    llm = MagicMock()
    llm.complete = AsyncMock(return_value={
        "content": "Test LLM response",
        "model": "test-model",
        "tokens": {"prompt": 10, "completion": 20},
    })
    return llm


def make_mock_fs():
    """Create a mock FileSystem."""
    fs = MagicMock()
    fs.write_file = AsyncMock()
    fs.read_file = AsyncMock(return_value="file content")
    fs.list_dir = AsyncMock(return_value=[])
    return fs


def make_mock_terminal():
    """Create a mock Terminal."""
    terminal = MagicMock()
    terminal.run = AsyncMock(return_value={"stdout": "", "stderr": "", "code": 0})
    return terminal


_AGENT_ROLES = {
    PMAgent: AgentRole.PM,
    BackendAgent: AgentRole.BACKEND,
    FrontendAgent: AgentRole.FRONTEND,
    UXAgent: AgentRole.UX,
    TesterAgent: AgentRole.TESTER,
    DevOpsAgent: AgentRole.DEVOPS,
}


def create_agent(agent_class, agent_id: str = "test-agent", **kwargs):
    """Create an agent instance with mock dependencies."""
    # BrainAgent is handled specially if ever needed
    role = _AGENT_ROLES.get(agent_class, AgentRole.PM)
    return agent_class(
        agent_id=agent_id,
        role=role,
        brain=kwargs.get("brain", make_mock_brain()),
        llm=kwargs.get("llm", make_mock_llm()),
        file_system=kwargs.get("fs", make_mock_fs()),
        terminal=kwargs.get("terminal", make_mock_terminal()),
    )


# ---- Tests: AgentRole & AgentStatus Enums ----

class TestAgentEnums:
    """Validate agent role and status enum values."""

    def test_agent_roles(self):
        assert AgentRole.PM.value == "pm"
        assert AgentRole.BRAIN.value == "brain"
        assert AgentRole.BACKEND.value == "backend"
        assert AgentRole.FRONTEND.value == "frontend"
        assert AgentRole.UX.value == "ux"
        assert AgentRole.TESTER.value == "tester"
        assert AgentRole.DEVOPS.value == "devops"

    def test_agent_statuses(self):
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.BLOCKED.value == "blocked"
        assert AgentStatus.PAUSED.value == "paused"
        assert AgentStatus.STOPPED.value == "stopped"

    def test_role_count(self):
        assert len(AgentRole) == 7

    def test_status_count(self):
        assert len(AgentStatus) == 5


# ---- Tests: BaseAgent ----

class TestBaseAgent:
    """Tests for BaseAgent initialization and lifecycle."""

    def test_cannot_instantiate_abstract(self):
        """BaseAgent is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent(
                agent_id="x",
                role=AgentRole.PM,
                brain=make_mock_brain(),
                llm=make_mock_llm(),
                file_system=make_mock_fs(),
                terminal=make_mock_terminal(),
            )

    def test_pm_agent_instantiation(self):
        agent = create_agent(PMAgent, "pm-001")
        assert agent.agent_id == "pm-001"
        assert agent.role == AgentRole.PM
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task is None

    def test_initial_state(self):
        agent = create_agent(PMAgent)
        assert agent._running is False
        assert agent._paused is False
        assert agent._task is None
        assert agent._message_history == []

    @pytest.mark.asyncio
    async def test_start_sets_working(self):
        agent = create_agent(PMAgent, "pm-start")
        await agent.start()
        assert agent.status == AgentStatus.WORKING
        assert agent._running is True
        await agent.stop()

    @pytest.mark.asyncio
    async def test_stop_sets_stopped(self):
        agent = create_agent(PMAgent, "pm-stop")
        await agent.start()
        await agent.stop()
        assert agent.status == AgentStatus.STOPPED
        assert agent._running is False

    @pytest.mark.asyncio
    async def test_pause_and_resume(self):
        agent = create_agent(PMAgent, "pm-pause")
        await agent.start()
        await agent.pause()
        assert agent.status == AgentStatus.PAUSED
        assert agent._paused is True

        await agent.resume()
        assert agent.status == AgentStatus.WORKING
        assert agent._paused is False
        await agent.stop()

    @pytest.mark.asyncio
    async def test_start_emits_agent_spawned(self):
        agent = create_agent(PMAgent, "pm-emit")
        emitted = []

        async def capture(ev):
            emitted.append(ev.event)

        event_bus.subscribe(EventType.AGENT_SPAWNED, capture)
        await agent.start()
        await asyncio.sleep(0.05)
        await agent.stop()
        event_bus.unsubscribe(EventType.AGENT_SPAWNED, capture)

        assert EventType.AGENT_SPAWNED in emitted

    @pytest.mark.asyncio
    async def test_stop_emits_agent_stopped(self):
        agent = create_agent(PMAgent, "pm-emit2")
        emitted = []

        async def capture(ev):
            emitted.append(ev.event)

        event_bus.subscribe(EventType.AGENT_STOPPED, capture)
        await agent.start()
        await agent.stop()
        event_bus.unsubscribe(EventType.AGENT_STOPPED, capture)

        assert EventType.AGENT_STOPPED in emitted

    @pytest.mark.asyncio
    async def test_think_calls_llm(self):
        llm = make_mock_llm()
        agent = create_agent(PMAgent, "pm-think", llm=llm)
        result = await agent.think("What should I do?")
        assert result == "Test LLM response"
        llm.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_say_emits_agent_message(self):
        agent = create_agent(PMAgent, "pm-say")
        emitted_data = []

        async def capture(event):
            emitted_data.append(event.data)

        event_bus.subscribe(EventType.AGENT_MESSAGE, capture)
        await agent.say("Hello from PM")
        event_bus.unsubscribe(EventType.AGENT_MESSAGE, capture)

        assert len(emitted_data) == 1
        assert emitted_data[0]["message"] == "Hello from PM"
        assert emitted_data[0]["role"] == "pm"

    @pytest.mark.asyncio
    async def test_write_code_delegates_to_fs(self):
        fs = make_mock_fs()
        agent = create_agent(PMAgent, "pm-write", fs=fs)
        await agent.write_code("/tmp/test.py", "print('hi')")
        fs.write_file.assert_awaited_once_with("/tmp/test.py", "print('hi')", agent_id="pm-write")

    @pytest.mark.asyncio
    async def test_run_command_delegates_to_terminal(self):
        terminal = make_mock_terminal()
        agent = create_agent(PMAgent, "pm-cmd", terminal=terminal)
        result = await agent.run_command("ls -la")
        assert result["code"] == 0
        terminal.run.assert_awaited_once()

    def test_system_prompt_not_empty(self):
        agent = create_agent(PMAgent)
        assert len(agent.system_prompt) > 50

    def test_task_type(self):
        agent = create_agent(PMAgent)
        assert agent.task_type == "planning"


# ---- Tests: PMAgent ----

class TestPMAgent:
    """Tests for PMAgent task logic."""

    @pytest.mark.asyncio
    async def test_get_next_task_requirements_phase(self):
        """When no project spec exists, PM should gather requirements."""
        brain = make_mock_brain()
        brain.get_context_for_agent = AsyncMock(return_value={
            "project_name": "",
            "conversation_history": [],
            "task_board_summary": {},
        })
        agent = create_agent(PMAgent, brain=brain)
        task = await agent.get_next_task({"project_name": ""})
        assert task is not None
        assert task["phase"] == "requirements"

    @pytest.mark.asyncio
    async def test_get_next_task_planning_phase(self):
        """When project exists but no tasks, PM should create plan."""
        agent = create_agent(PMAgent)
        context = {
            "project_name": "my-app",
            "task_board_summary": {"backlog": 0, "in_progress": 0, "done": 0},
        }
        task = await agent.get_next_task(context)
        assert task is not None
        assert task["phase"] == "planning"

    @pytest.mark.asyncio
    async def test_get_next_task_monitoring_phase(self):
        """When tasks exist, PM should monitor."""
        agent = create_agent(PMAgent)
        context = {
            "project_name": "my-app",
            "task_board_summary": {"backlog": 3, "in_progress": 2, "done": 1},
        }
        task = await agent.get_next_task(context)
        assert task is not None
        assert task["phase"] == "monitoring"

    @pytest.mark.asyncio
    async def test_get_next_task_done(self):
        """When all done, returns None."""
        agent = create_agent(PMAgent)
        context = {
            "project_name": "my-app",
            "task_board_summary": {"backlog": 0, "in_progress": 0, "done": 10},
        }
        task = await agent.get_next_task(context)
        assert task is None

    @pytest.mark.asyncio
    async def test_handle_user_message(self):
        brain = make_mock_brain()
        llm = make_mock_llm()
        agent = create_agent(PMAgent, brain=brain, llm=llm)
        result = await agent.handle_user_message("Build me a SaaS app")
        assert isinstance(result, str)
        brain.add_message.assert_any_await("user", "Build me a SaaS app")


# ---- Tests: Specialized Agents have correct roles ----

class TestSpecializedAgents:
    """Verify each agent has the correct role and required properties."""

    def test_backend_agent_role(self):
        agent = create_agent(BackendAgent, "be-001")
        assert agent.role == AgentRole.BACKEND

    def test_frontend_agent_role(self):
        agent = create_agent(FrontendAgent, "fe-001")
        assert agent.role == AgentRole.FRONTEND

    def test_ux_agent_role(self):
        agent = create_agent(UXAgent, "ux-001")
        assert agent.role == AgentRole.UX

    def test_tester_agent_role(self):
        agent = create_agent(TesterAgent, "tst-001")
        assert agent.role == AgentRole.TESTER

    def test_devops_agent_role(self):
        agent = create_agent(DevOpsAgent, "ops-001")
        assert agent.role == AgentRole.DEVOPS

    def test_all_agents_have_system_prompt(self):
        agents = [
            create_agent(PMAgent),
            create_agent(BackendAgent, "be"),
            create_agent(FrontendAgent, "fe"),
            create_agent(UXAgent, "ux"),
            create_agent(TesterAgent, "tst"),
            create_agent(DevOpsAgent, "ops"),
        ]
        for agent in agents:
            assert len(agent.system_prompt) > 20, f"{agent.role} has no system prompt"

    def test_all_agents_have_task_type(self):
        agents = [
            create_agent(PMAgent),
            create_agent(BackendAgent, "be"),
            create_agent(FrontendAgent, "fe"),
            create_agent(UXAgent, "ux"),
            create_agent(TesterAgent, "tst"),
            create_agent(DevOpsAgent, "ops"),
        ]
        for agent in agents:
            assert isinstance(agent.task_type, str)
            assert len(agent.task_type) > 0
