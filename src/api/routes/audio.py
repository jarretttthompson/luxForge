"""Audio configuration and device routes."""

from fastapi import APIRouter

from src.api import dependencies as deps
from src.api.schemas import AudioConfigResponse, AudioDeviceInfo, AudioDeviceListResponse

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/devices", response_model=AudioDeviceListResponse)
async def list_audio_devices():
    source = deps.audio_source
    if source is None:
        return AudioDeviceListResponse(devices=[])

    raw_devices = source.list_devices()
    devices = [
        AudioDeviceInfo(
            index=d.get("index", -1),
            name=d.get("name", "Unknown"),
            channels=d.get("channels", 0) if isinstance(d.get("channels"), int) else d.get("max_input_channels", 0),
            sample_rate=d.get("sample_rate", 0.0) if "sample_rate" in d else d.get("default_samplerate", 0.0),
        )
        for d in raw_devices
    ]
    return AudioDeviceListResponse(devices=devices)


@router.get("/config", response_model=AudioConfigResponse)
async def get_audio_config():
    cfg = deps.config
    return AudioConfigResponse(
        device_index=cfg.audio.device_index if cfg else None,
        sample_rate=cfg.audio.sample_rate if cfg else 48000,
        buffer_size=cfg.audio.buffer_size if cfg else 1024,
        simulator_enabled=cfg.simulator.enabled if cfg else True,
        simulator_mode=cfg.simulator.mode if cfg else "kick_pattern",
        simulator_bpm=cfg.simulator.bpm if cfg else 120,
    )
