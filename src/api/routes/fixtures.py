"""Fixture profile and patch routes (placeholder — full implementation in Session 14)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])


@router.get("/profiles")
async def list_profiles():
    return {"profiles": []}


@router.get("/patch")
async def get_patch():
    return {"entries": []}


@router.post("/patch", status_code=201)
async def add_patch_entry():
    return {"message": "Fixture patching not yet implemented"}
