"""SceneManager: orchestrates scene activation, deactivation, and transitions."""

import uuid

import structlog

from src.console.base import ConsoleInterface
from src.engine.events import AsyncEventBus
from src.mapping.engine import MappingEngine
from src.mapping.types import MappingRule
from src.protocols.base import ProtocolAdapter
from src.scenes.models import Scene
from src.scenes.storage import SceneStorage

logger = structlog.get_logger()


class SceneManager:
    """Manages scene lifecycle: load, activate, deactivate, persist."""

    def __init__(
        self,
        storage: SceneStorage,
        mapping_engine: MappingEngine,
        console: ConsoleInterface,
        adapters: list[ProtocolAdapter],
        event_bus: AsyncEventBus,
    ) -> None:
        self._storage = storage
        self._mapping_engine = mapping_engine
        self._console = console
        self._adapters = adapters
        self._event_bus = event_bus
        self._active_scene_id: str | None = None
        self._active_rule_ids: list[str] = []

    @property
    def active_scene_id(self) -> str | None:
        return self._active_scene_id

    async def init(self) -> None:
        """Initialize the underlying storage."""
        await self._storage.init_db()

    async def close(self) -> None:
        await self._storage.close()

    # --- CRUD ---

    async def create_scene(self, name: str, description: str = "", transition_time_ms: int = 0) -> Scene:
        scene = Scene(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            transition_time_ms=transition_time_ms,
        )
        await self._storage.save_scene(scene)
        logger.info("scene_created", scene_id=scene.id, name=name)
        return scene

    async def get_scene(self, scene_id: str) -> Scene | None:
        return await self._storage.get_scene(scene_id)

    async def list_scenes(self) -> list[Scene]:
        return await self._storage.list_scenes()

    async def update_scene(self, scene: Scene) -> None:
        await self._storage.save_scene(scene)

    async def delete_scene(self, scene_id: str) -> bool:
        if self._active_scene_id == scene_id:
            await self.deactivate()
        return await self._storage.delete_scene(scene_id)

    # --- Activation ---

    async def activate(self, scene_id: str) -> bool:
        """Activate a scene: load its rules into the mapping engine and fire triggers."""
        scene = await self._storage.get_scene(scene_id)
        if scene is None:
            logger.warning("scene_not_found", scene_id=scene_id)
            return False

        # Deactivate current scene first
        if self._active_scene_id is not None:
            await self.deactivate()

        # Load mapping rules into the engine
        for rule in scene.mapping_rules:
            self._mapping_engine.add_rule(rule)
            self._active_rule_ids.append(rule.id)

        # Fire cuelist triggers
        for trigger in scene.cuelist_triggers:
            messages = self._console.translate(trigger)
            for msg in messages:
                self._send_to_adapters(msg)

        self._active_scene_id = scene_id
        logger.info("scene_activated", scene_id=scene_id, name=scene.name, rules=len(scene.mapping_rules))
        await self._event_bus.publish("scene.activated", {"scene_id": scene_id, "name": scene.name})
        return True

    async def deactivate(self) -> None:
        """Remove the current scene's rules from the mapping engine."""
        if self._active_scene_id is None:
            return

        for rule_id in self._active_rule_ids:
            self._mapping_engine.remove_rule(rule_id)

        old_id = self._active_scene_id
        self._active_rule_ids.clear()
        self._active_scene_id = None

        logger.info("scene_deactivated", scene_id=old_id)
        await self._event_bus.publish("scene.deactivated", {"scene_id": old_id})

    def _send_to_adapters(self, message) -> None:
        """Route a protocol message to the appropriate adapter."""
        from src.protocols.types import OSCMessage, MIDIMessage, DMXFrame

        for adapter in self._adapters:
            try:
                if isinstance(message, OSCMessage) and "osc" in adapter.name.lower():
                    adapter.send(message)
                elif isinstance(message, MIDIMessage) and "midi" in adapter.name.lower():
                    adapter.send(message)
                elif isinstance(message, DMXFrame) and (
                    "artnet" in adapter.name.lower() or "sacn" in adapter.name.lower()
                ):
                    adapter.send(message)
            except Exception:
                logger.exception("scene_trigger_send_error", adapter=adapter.name)
