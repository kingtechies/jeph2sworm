"""REST API routes for the Jeph2Sworm server."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")


# ── Request / Response Models ──────────────────────────────────────

class ProjectSpecRequest(BaseModel):
    name: str
    description: str
    features: list[str] = []
    tech_preferences: dict = {}
    design_style: str = ""
    auth_type: str = ""
    deployment: str = ""


class UserMessageRequest(BaseModel):
    message: str


class LLMProviderRequest(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None


class AgentActionRequest(BaseModel):
    agent_id: str


# ── Placeholder for swarm manager injection ───────────────────────

_swarm_manager = None


def set_swarm_manager(manager) -> None:
    """Inject the swarm manager instance."""
    global _swarm_manager
    _swarm_manager = manager


def _get_manager():
    if _swarm_manager is None:
        raise HTTPException(status_code=503, detail="Swarm not initialized")
    return _swarm_manager


# ── Health ─────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "jeph2sworm"}


# ── Swarm Status ───────────────────────────────────────────────────

@router.get("/status")
async def get_status():
    manager = _get_manager()
    return manager.get_status()


# ── Project ────────────────────────────────────────────────────────

@router.post("/project")
async def set_project(spec: ProjectSpecRequest):
    manager = _get_manager()
    await manager.set_project_spec(spec.model_dump())
    return {"status": "ok", "message": "Project spec set"}


# ── Chat ───────────────────────────────────────────────────────────

@router.post("/chat")
async def send_message(req: UserMessageRequest):
    manager = _get_manager()
    response = await manager.send_user_message(req.message)
    return {"status": "ok", "response": response}


@router.get("/chat/history")
async def get_history():
    manager = _get_manager()
    history = await manager.get_conversation_history()
    return {"history": history}


# ── Tasks ──────────────────────────────────────────────────────────

@router.get("/tasks")
async def get_tasks():
    manager = _get_manager()
    board = await manager.get_task_board()
    return {"task_board": board}


# ── Agents ─────────────────────────────────────────────────────────

@router.get("/agents")
async def get_agents():
    manager = _get_manager()
    status = manager.get_status()
    return {"agents": status.get("agents", {})}


@router.post("/agents/pause")
async def pause_agent(req: AgentActionRequest):
    manager = _get_manager()
    ok = await manager.pause_agent(req.agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "paused", "agent_id": req.agent_id}


@router.post("/agents/resume")
async def resume_agent(req: AgentActionRequest):
    manager = _get_manager()
    ok = await manager.resume_agent(req.agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "resumed", "agent_id": req.agent_id}


# ── LLM Providers ─────────────────────────────────────────────────

@router.post("/llm/provider")
async def configure_provider(req: LLMProviderRequest):
    manager = _get_manager()
    await manager.configure_llm_provider(
        req.provider, req.api_key, base_url=req.base_url
    )
    return {"status": "ok", "provider": req.provider}


# ── Brain ──────────────────────────────────────────────────────────

@router.get("/brain/stats")
async def brain_stats():
    manager = _get_manager()
    return manager.brain.get_stats()


@router.get("/brain/decisions")
async def brain_decisions():
    manager = _get_manager()
    decisions = await manager.brain.read("decisions_log")
    return {"decisions": decisions or []}


@router.get("/brain/errors")
async def brain_errors():
    manager = _get_manager()
    errors = await manager.brain.read("errors_log")
    return {"errors": errors or []}


@router.get("/brain/test-results")
async def brain_test_results():
    manager = _get_manager()
    results = await manager.brain.read("test_results")
    return {"test_results": results or []}


# ── Config — Providers ─────────────────────────────────────────────

@router.get("/config/providers")
async def list_providers():
    """List all available LLM providers and their status."""
    manager = _get_manager()
    providers = await manager.list_llm_providers()
    return {"providers": providers}


@router.post("/config/api-key")
async def store_api_key(req: LLMProviderRequest):
    """Store an API key for a provider."""
    manager = _get_manager()
    await manager.configure_llm_provider(
        req.provider, req.api_key, base_url=req.base_url
    )
    return {"status": "ok", "provider": req.provider, "message": "API key stored"}


# ── Session ────────────────────────────────────────────────────────

@router.get("/session/status")
async def session_status():
    """Get current session status including phase and progress."""
    manager = _get_manager()
    status = manager.get_status()
    return {
        "active": status.get("active", False),
        "phase": status.get("phase", "idle"),
        "progress": status.get("progress", 0),
        "agents_working": sum(
            1 for a in status.get("agents", {}).values()
            if isinstance(a, dict) and a.get("status") == "working"
        ),
        "uptime": status.get("uptime", 0),
    }


@router.post("/session/start")
async def session_start(spec: ProjectSpecRequest):
    """Start a new project session — spawns the swarm."""
    manager = _get_manager()
    await manager.set_project_spec(spec.model_dump())
    await manager.start()
    return {"status": "ok", "message": "Swarm started"}


@router.post("/session/stop")
async def session_stop():
    """Stop all agents and the current session."""
    manager = _get_manager()
    await manager.stop()
    return {"status": "ok", "message": "Swarm stopped"}


# ── Agent Logs ─────────────────────────────────────────────────────

@router.get("/agents/{agent_id}/logs")
async def agent_logs(agent_id: str, limit: int = 100):
    """Get recent logs for a specific agent."""
    manager = _get_manager()
    agents = manager.get_status().get("agents", {})
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    logs = await manager.get_agent_logs(agent_id, limit=limit)
    return {"agent_id": agent_id, "logs": logs}


# ── Test Evidence ──────────────────────────────────────────────────

@router.get("/tests/results")
async def test_results():
    """Get all test results across all runs."""
    manager = _get_manager()
    results = await manager.brain.read("test_results") or []
    return {
        "total_runs": len(results),
        "results": results,
    }


@router.get("/tests/evidence/{run_number}")
async def test_evidence(run_number: int):
    """Get evidence (screenshots, logs) for a specific test run."""
    manager = _get_manager()
    results = await manager.brain.read("test_results") or []
    run = next((r for r in results if r.get("run_number") == run_number), None)
    if not run:
        raise HTTPException(status_code=404, detail=f"Test run {run_number} not found")
    return {"run_number": run_number, "evidence": run}


# ── Credentials ────────────────────────────────────────────────────

class RevealCredentialRequest(BaseModel):
    key_name: str


@router.get("/credentials")
async def list_credentials():
    """List all credential keys (values masked)."""
    manager = _get_manager()
    creds = await manager.brain.read("credentials") or []
    masked = [
        {
            "key_name": c.get("key_name", ""),
            "purpose": c.get("purpose", ""),
            "created_by": c.get("created_by", ""),
            "value": "••••••••",
        }
        for c in creds
    ]
    return {"credentials": masked}


@router.post("/credentials/reveal")
async def reveal_credential(req: RevealCredentialRequest):
    """Reveal the actual value of a credential."""
    manager = _get_manager()
    creds = await manager.brain.read("credentials") or []
    cred = next((c for c in creds if c.get("key_name") == req.key_name), None)
    if not cred:
        raise HTTPException(status_code=404, detail=f"Credential '{req.key_name}' not found")
    return {"key_name": req.key_name, "value": cred.get("value", "")}


# ── Token Usage ────────────────────────────────────────────────────

@router.get("/tokens/usage")
async def token_usage():
    """Get token usage statistics per agent and per provider."""
    manager = _get_manager()
    usage = manager.llm_router.get_usage_summary()
    return usage
