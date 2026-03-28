"""Scene management routes (placeholder — full implementation in Session 13)."""

from fastapi import APIRouter

from src.api.schemas import SceneListResponse

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


@router.get("", response_model=SceneListResponse)
async def list_scenes():
    # Placeholder until Session 13 adds SceneManager
    return SceneListResponse(scenes=[])


@router.post("", status_code=201)
async def create_scene():
    return {"id": "placeholder", "message": "Scene storage not yet implemented"}


@router.post("/{scene_id}/activate")
async def activate_scene(scene_id: str):
    return {"message": f"Scene activation not yet implemented for {scene_id}"}


@router.post("/{scene_id}/deactivate")
async def deactivate_scene(scene_id: str):
    return {"message": f"Scene deactivation not yet implemented for {scene_id}"}
