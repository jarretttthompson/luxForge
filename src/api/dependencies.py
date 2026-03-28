"""Shared API dependencies — holds references to application components.

Set during app lifespan startup. Route handlers access these via module-level getters.
"""

from src.engine.events import AsyncEventBus
from src.engine.state import AppState
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry

# These are populated by the app lifespan
state: AppState | None = None
event_bus: AsyncEventBus | None = None
mapping_engine: MappingEngine | None = None
param_registry: ParameterRegistry | None = None
console = None
adapters: list = []
audio_source = None
config = None
scene_manager = None  # SceneManager, set during startup
fixture_library = None  # FixtureLibrary, set during startup
patch_manager = None  # PatchManager, set during startup


def get_state() -> AppState:
    assert state is not None, "AppState not initialized"
    return state


def get_event_bus() -> AsyncEventBus:
    assert event_bus is not None, "EventBus not initialized"
    return event_bus


def get_mapping_engine() -> MappingEngine:
    assert mapping_engine is not None, "MappingEngine not initialized"
    return mapping_engine


def get_param_registry() -> ParameterRegistry:
    assert param_registry is not None, "ParameterRegistry not initialized"
    return param_registry
