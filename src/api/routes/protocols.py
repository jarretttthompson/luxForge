"""Protocol status and configuration routes."""

from fastapi import APIRouter

from src.api import dependencies as deps
from src.api.schemas import ProtocolStatusListResponse, ProtocolStatusResponse

router = APIRouter(prefix="/api/protocols", tags=["protocols"])


@router.get("/status", response_model=ProtocolStatusListResponse)
async def get_protocol_status():
    state = deps.get_state()
    statuses = [
        ProtocolStatusResponse(
            name=s.name,
            connected=s.connected,
            dry_run=s.dry_run,
            messages_sent=s.messages_sent,
        )
        for s in state.protocol_statuses.values()
    ]
    return ProtocolStatusListResponse(protocols=statuses)
