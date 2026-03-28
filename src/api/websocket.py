"""WebSocket endpoint for real-time state broadcasting."""

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api import dependencies as deps

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts state."""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("ws_client_connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("ws_client_disconnected", total=len(self._connections))

    async def broadcast(self, data: dict) -> None:
        """Send data to all connected clients."""
        if not self._connections:
            return
        text = json.dumps(data)
        disconnected = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


async def broadcast_loop() -> None:
    """Sends state snapshots to all WebSocket clients at ~30fps."""
    interval = 1.0 / 30.0
    while True:
        try:
            state = deps.get_state()
            snapshot = state.to_snapshot()
            await manager.broadcast(snapshot)
        except Exception:
            pass
        await asyncio.sleep(interval)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Receive control commands from the client
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                await _handle_command(msg)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "invalid JSON"}))
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


async def _handle_command(msg: dict) -> None:
    """Handle incoming WebSocket control commands."""
    cmd_type = msg.get("type", "")
    mapping_engine = deps.get_mapping_engine()

    if cmd_type == "mapping.enable":
        rule_id = msg.get("id", "")
        mapping_engine.enable_rule(rule_id)
    elif cmd_type == "mapping.disable":
        rule_id = msg.get("id", "")
        mapping_engine.disable_rule(rule_id)
    else:
        logger.debug("ws_unknown_command", command=cmd_type)
