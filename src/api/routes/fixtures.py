"""Fixture profile and patch management routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api import dependencies as deps

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])


class PatchEntryCreate(BaseModel):
    profile_id: str
    mode_index: int = 0
    universe: int = 1
    start_address: int
    label: str


class PatchMoveRequest(BaseModel):
    universe: int
    start_address: int


@router.get("/profiles")
async def list_profiles():
    library = deps.fixture_library
    if library is None:
        return {"profiles": []}
    return {"profiles": [p.to_dict() for p in library.list_all()]}


@router.get("/profiles/search")
async def search_profiles(q: str = ""):
    library = deps.fixture_library
    if library is None:
        return {"profiles": []}
    results = library.search(q) if q else library.list_all()
    return {"profiles": [p.to_dict() for p in results]}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    library = deps.fixture_library
    if library is None:
        raise HTTPException(503, "Fixture library not initialized")
    profile = library.get_profile(profile_id)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile.to_dict()


@router.get("/patch")
async def get_patch():
    pm = deps.patch_manager
    if pm is None:
        return {"entries": [], "errors": []}
    entries = pm.get_entries()
    errors = pm.validate()
    return {
        "entries": [e.to_dict() for e in entries],
        "errors": errors,
    }


@router.post("/patch", status_code=201)
async def add_patch_entry(body: PatchEntryCreate):
    pm = deps.patch_manager
    if pm is None:
        raise HTTPException(503, "Patch manager not initialized")
    try:
        entry = pm.add_fixture(
            profile_id=body.profile_id,
            mode_index=body.mode_index,
            universe=body.universe,
            start_address=body.start_address,
            label=body.label,
        )
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(409, str(e))


@router.delete("/patch/{patch_id}", status_code=204)
async def remove_patch_entry(patch_id: str):
    pm = deps.patch_manager
    if pm is None:
        raise HTTPException(503, "Patch manager not initialized")
    if not pm.remove_fixture(patch_id):
        raise HTTPException(404, "Patch entry not found")


@router.put("/patch/{patch_id}/move")
async def move_patch_entry(patch_id: str, body: PatchMoveRequest):
    pm = deps.patch_manager
    if pm is None:
        raise HTTPException(503, "Patch manager not initialized")
    try:
        entry = pm.move_fixture(patch_id, body.universe, body.start_address)
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(409, str(e))
