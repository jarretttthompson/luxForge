"""System health and configuration routes."""

from fastapi import APIRouter

from src.api import dependencies as deps
from src.api.schemas import SystemHealthResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health", response_model=SystemHealthResponse)
async def health():
    state = deps.get_state()
    return SystemHealthResponse(
        status="ok",
        engine_running=state.engine_running,
        fps=round(state.fps, 1),
        tick_count=state.tick_count,
        active_console=state.active_console,
        active_scene=state.active_scene,
    )
