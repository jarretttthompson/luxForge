"""Pydantic models for API request/response bodies."""

from pydantic import BaseModel, Field


# --- Audio ---

class AudioDeviceInfo(BaseModel):
    index: int
    name: str
    channels: int
    sample_rate: float


class AudioDeviceListResponse(BaseModel):
    devices: list[AudioDeviceInfo]


class AudioConfigResponse(BaseModel):
    device_index: int | None
    sample_rate: int
    buffer_size: int
    simulator_enabled: bool
    simulator_mode: str
    simulator_bpm: int


class AudioConfigUpdate(BaseModel):
    device_index: int | None = None
    sample_rate: int | None = None
    buffer_size: int | None = None
    simulator_enabled: bool | None = None
    simulator_mode: str | None = None
    simulator_bpm: int | None = None


# --- Mapping ---

class TransformDict(BaseModel):
    type: str
    model_config = {"extra": "allow"}


class MappingRuleCreate(BaseModel):
    name: str
    input_param: str
    output_param: str
    transform_chain: list[dict] = Field(default_factory=list)
    condition: str | None = None
    enabled: bool = True


class MappingRuleUpdate(BaseModel):
    name: str | None = None
    input_param: str | None = None
    output_param: str | None = None
    transform_chain: list[dict] | None = None
    condition: str | None = None
    enabled: bool | None = None


class MappingRuleResponse(BaseModel):
    id: str
    name: str
    input_param: str
    output_param: str
    transform_chain: list[dict]
    condition: str | None
    enabled: bool


class MappingRuleListResponse(BaseModel):
    rules: list[MappingRuleResponse]


# --- Scenes ---

class SceneCreate(BaseModel):
    name: str
    description: str = ""
    mapping_rule_ids: list[str] = Field(default_factory=list)
    transition_time_ms: int = 0


class SceneUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mapping_rule_ids: list[str] | None = None
    transition_time_ms: int | None = None


class SceneResponse(BaseModel):
    id: str
    name: str
    description: str
    mapping_rule_ids: list[str]
    transition_time_ms: int
    active: bool = False


class SceneListResponse(BaseModel):
    scenes: list[SceneResponse]


# --- Protocols ---

class ProtocolStatusResponse(BaseModel):
    name: str
    connected: bool
    dry_run: bool
    messages_sent: int = 0


class ProtocolStatusListResponse(BaseModel):
    protocols: list[ProtocolStatusResponse]


class ProtocolConfigUpdate(BaseModel):
    host: str | None = None
    port: int | None = None
    dry_run: bool | None = None
    universe: int | None = None


# --- Parameters ---

class ParameterInfo(BaseModel):
    name: str
    display_name: str = ""


class ParameterListResponse(BaseModel):
    inputs: list[ParameterInfo]
    outputs: list[ParameterInfo]


# --- System ---

class SystemHealthResponse(BaseModel):
    status: str = "ok"
    engine_running: bool
    fps: float
    tick_count: int
    active_console: str
    active_scene: str | None


class WebSocketMessage(BaseModel):
    """Schema for the 30fps WebSocket broadcast message."""
    audio: dict
    outputs: list[dict]
    engine: dict
    console: str
    scene: str | None
    protocols: dict
