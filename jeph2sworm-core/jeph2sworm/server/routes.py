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
    return {"decisions": manager.brain.data.get("decisions_log", [])}


@router.get("/brain/errors")
async def brain_errors():
    manager = _get_manager()
    return {"errors": manager.brain.data.get("errors_log", [])}


@router.get("/brain/test-results")
async def brain_test_results():
    manager = _get_manager()
    return {"test_results": manager.brain.data.get("test_results", [])}
