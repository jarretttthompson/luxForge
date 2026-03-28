"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import dependencies as deps
from src.api.routes import audio, mapping, scenes, fixtures, protocols, system
from src.api.websocket import broadcast_loop, router as ws_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the WebSocket broadcast loop during app lifetime."""
    broadcast_task = asyncio.create_task(broadcast_loop())
    logger.info("ws_broadcast_started")
    yield
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    logger.info("ws_broadcast_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="LuxForge",
        description="Audio-reactive lighting control system",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    app.include_router(audio.router)
    app.include_router(mapping.router)
    app.include_router(scenes.router)
    app.include_router(fixtures.router)
    app.include_router(protocols.router)
    app.include_router(system.router)
    app.include_router(ws_router)

    return app
