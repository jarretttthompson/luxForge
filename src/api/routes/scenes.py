"""Scene management routes."""

import uuid

from fastapi import APIRouter, HTTPException

from src.api import dependencies as deps
from src.api.schemas import SceneCreate, SceneListResponse, SceneResponse, SceneUpdate
from src.mapping.types import MappingRule
from src.scenes.models import Scene

router = APIRouter(prefix="/api/scenes", tags=["scenes"])


def _scene_to_response(scene: Scene, active_id: str | None = None) -> SceneResponse:
    return SceneResponse(
        id=scene.id,
        name=scene.name,
        description=scene.description,
        mapping_rule_ids=[r.id for r in scene.mapping_rules],
        transition_time_ms=scene.transition_time_ms,
        active=scene.id == active_id,
    )


@router.get("", response_model=SceneListResponse)
async def list_scenes():
    mgr = deps.scene_manager
    if mgr is None:
        return SceneListResponse(scenes=[])
    scenes = await mgr.list_scenes()
    active_id = mgr.active_scene_id
    return SceneListResponse(scenes=[_scene_to_response(s, active_id) for s in scenes])


@router.post("", response_model=SceneResponse, status_code=201)
async def create_scene(body: SceneCreate):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")

    scene = await mgr.create_scene(
        name=body.name,
        description=body.description,
        transition_time_ms=body.transition_time_ms,
    )

    # If rule IDs were provided, attach copies of those rules to the scene
    if body.mapping_rule_ids:
        engine = deps.get_mapping_engine()
        existing_rules = {r.id: r for r in engine.get_rules()}
        for rid in body.mapping_rule_ids:
            if rid in existing_rules:
                scene.mapping_rules.append(existing_rules[rid])
        await mgr.update_scene(scene)

    return _scene_to_response(scene, mgr.active_scene_id)


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(scene_id: str):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")
    scene = await mgr.get_scene(scene_id)
    if scene is None:
        raise HTTPException(404, "Scene not found")
    return _scene_to_response(scene, mgr.active_scene_id)


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(scene_id: str, body: SceneUpdate):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")
    scene = await mgr.get_scene(scene_id)
    if scene is None:
        raise HTTPException(404, "Scene not found")

    if body.name is not None:
        scene.name = body.name
    if body.description is not None:
        scene.description = body.description
    if body.transition_time_ms is not None:
        scene.transition_time_ms = body.transition_time_ms
    if body.mapping_rule_ids is not None:
        engine = deps.get_mapping_engine()
        existing_rules = {r.id: r for r in engine.get_rules()}
        scene.mapping_rules = [existing_rules[rid] for rid in body.mapping_rule_ids if rid in existing_rules]

    await mgr.update_scene(scene)
    return _scene_to_response(scene, mgr.active_scene_id)


@router.delete("/{scene_id}", status_code=204)
async def delete_scene(scene_id: str):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")
    deleted = await mgr.delete_scene(scene_id)
    if not deleted:
        raise HTTPException(404, "Scene not found")


@router.post("/{scene_id}/activate")
async def activate_scene(scene_id: str):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")
    success = await mgr.activate(scene_id)
    if not success:
        raise HTTPException(404, "Scene not found")
    return {"message": "activated", "scene_id": scene_id}


@router.post("/{scene_id}/deactivate")
async def deactivate_scene(scene_id: str):
    mgr = deps.scene_manager
    if mgr is None:
        raise HTTPException(503, "Scene manager not initialized")
    await mgr.deactivate()
    return {"message": "deactivated"}
