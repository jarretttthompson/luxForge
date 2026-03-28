"""Application configuration using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class AudioConfig(BaseSettings):
    device_index: int | None = Field(default=None, description="Audio device index (None = use simulator)")
    sample_rate: int = Field(default=48000, description="Audio sample rate in Hz")
    buffer_size: int = Field(default=1024, description="Audio buffer size in samples")


class SimulatorConfig(BaseSettings):
    enabled: bool = Field(default=True, description="Use audio simulator instead of real hardware")
    bpm: int = Field(default=120, description="Simulator BPM for kick pattern mode")
    mode: str = Field(default="kick_pattern", description="Simulator mode: kick_pattern, sine, noise, sweep, silent")
    frequency: float = Field(default=440.0, description="Frequency for sine mode")


class OSCConfig(BaseSettings):
    host: str = Field(default="127.0.0.1", description="OSC target host")
    port: int = Field(default=8000, description="OSC target port")
    dry_run: bool = Field(default=True, description="Log messages instead of sending")


class ArtNetConfig(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Art-Net target host")
    port: int = Field(default=6454, description="Art-Net port")
    universe: int = Field(default=0, description="Art-Net universe")
    dry_run: bool = Field(default=True, description="Log messages instead of sending")


class SACNConfig(BaseSettings):
    universe: int = Field(default=1, description="sACN universe")
    multicast: bool = Field(default=True, description="Use multicast")
    unicast_dest: str | None = Field(default=None, description="Unicast destination")
    dry_run: bool = Field(default=True, description="Log messages instead of sending")


class MIDIConfig(BaseSettings):
    port_name: str | None = Field(default=None, description="MIDI output port name")
    dry_run: bool = Field(default=True, description="Log messages instead of sending")


class APIConfig(BaseSettings):
    port: int = Field(default=8765, description="API server port")
    host: str = Field(default="0.0.0.0", description="API server host")


class AppConfig(BaseSettings):
    """Root configuration loaded from environment variables and .env file."""

    model_config = {"env_prefix": "", "env_file": ".env", "env_nested_delimiter": "__"}

    audio: AudioConfig = Field(default_factory=AudioConfig)
    simulator: SimulatorConfig = Field(default_factory=SimulatorConfig)
    osc: OSCConfig = Field(default_factory=OSCConfig)
    artnet: ArtNetConfig = Field(default_factory=ArtNetConfig)
    sacn: SACNConfig = Field(default_factory=SACNConfig)
    midi: MIDIConfig = Field(default_factory=MIDIConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    log_level: str = Field(default="INFO", description="Logging level")
