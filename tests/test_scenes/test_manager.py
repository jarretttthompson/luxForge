"""Tests for scene storage and manager."""

import pytest

from src.console.simulator import SimulatorConsole
from src.console.types import ConsoleCapability, ConsoleCommand
from src.engine.events import AsyncEventBus
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.mapping.types import MappingRule
from src.scenes.manager import SceneManager
from src.scenes.models import Preset, Scene
from src.scenes.storage import SceneStorage


@pytest.fixture
async def storage():
    s = SceneStorage(db_path=":memory:")
    await s.init_db()
    yield s
    await s.close()


@pytest.fixture
def console():
    return SimulatorConsole(num_playbacks=5)


@pytest.fixture
def mapping_engine(console):
    reg = ParameterRegistry()
    reg.register_console(console)
    return MappingEngine(registry=reg)


@pytest.fixture
async def manager(storage, mapping_engine, console):
    event_bus = AsyncEventBus()
    mgr = SceneManager(
        storage=storage,
        mapping_engine=mapping_engine,
        console=console,
        adapters=[],
        event_bus=event_bus,
    )
    return mgr


# --- Scene Model Tests ---

class TestSceneModel:
    def test_scene_roundtrip(self):
        rule = MappingRule(
            id="r1", name="Test", input_param="audio.rms",
            output_param="simulator.playback.1.fader",
        )
        trigger = ConsoleCommand(
            target="playback.1.go", value=1.0,
            command_type=ConsoleCapability.PLAYBACK_GO,
        )
        scene = Scene(
            id="s1", name="My Scene", description="A test",
            mapping_rules=[rule], cuelist_triggers=[trigger],
            transition_time_ms=500,
        )
        d = scene.to_dict()
        restored = Scene.from_dict(d)
        assert restored.id == "s1"
        assert restored.name == "My Scene"
        assert len(restored.mapping_rules) == 1
        assert restored.mapping_rules[0].input_param == "audio.rms"
        assert len(restored.cuelist_triggers) == 1
        assert restored.cuelist_triggers[0].target == "playback.1.go"
        assert restored.transition_time_ms == 500

    def test_preset_roundtrip(self):
        preset = Preset(
            id="p1", name="Smooth Fade",
            transform_chain=[{"type": "Smooth", "attack": 0.1, "release": 0.3}],
        )
        d = preset.to_dict()
        restored = Preset.from_dict(d)
        assert restored.id == "p1"
        assert restored.name == "Smooth Fade"
        assert len(restored.transform_chain) == 1


# --- Storage Tests ---

@pytest.mark.asyncio
class TestSceneStorage:
    async def test_save_and_get_scene(self, storage):
        scene = Scene(id="s1", name="Test Scene", description="desc")
        await storage.save_scene(scene)

        loaded = await storage.get_scene("s1")
        assert loaded is not None
        assert loaded.name == "Test Scene"
        assert loaded.description == "desc"

    async def test_get_nonexistent_returns_none(self, storage):
        assert await storage.get_scene("nope") is None

    async def test_list_scenes(self, storage):
        await storage.save_scene(Scene(id="a", name="Alpha"))
        await storage.save_scene(Scene(id="b", name="Beta"))
        scenes = await storage.list_scenes()
        assert len(scenes) == 2
        names = [s.name for s in scenes]
        assert "Alpha" in names
        assert "Beta" in names

    async def test_delete_scene(self, storage):
        await storage.save_scene(Scene(id="d1", name="Doomed"))
        assert await storage.delete_scene("d1") is True
        assert await storage.get_scene("d1") is None

    async def test_delete_nonexistent(self, storage):
        assert await storage.delete_scene("nope") is False

    async def test_save_scene_with_rules(self, storage):
        rule = MappingRule(id="r1", name="RMS", input_param="audio.rms", output_param="sim.pb.1.fader")
        scene = Scene(id="s1", name="With Rules", mapping_rules=[rule])
        await storage.save_scene(scene)

        loaded = await storage.get_scene("s1")
        assert len(loaded.mapping_rules) == 1
        assert loaded.mapping_rules[0].id == "r1"

    async def test_upsert_scene(self, storage):
        await storage.save_scene(Scene(id="u1", name="V1"))
        await storage.save_scene(Scene(id="u1", name="V2"))
        loaded = await storage.get_scene("u1")
        assert loaded.name == "V2"

    async def test_save_and_get_preset(self, storage):
        preset = Preset(id="p1", name="Chill", transform_chain=[{"type": "Smooth", "attack": 0.2, "release": 0.5}])
        await storage.save_preset(preset)

        loaded = await storage.get_preset("p1")
        assert loaded is not None
        assert loaded.name == "Chill"
        assert len(loaded.transform_chain) == 1

    async def test_list_presets(self, storage):
        await storage.save_preset(Preset(id="p1", name="A"))
        await storage.save_preset(Preset(id="p2", name="B"))
        presets = await storage.list_presets()
        assert len(presets) == 2

    async def test_delete_preset(self, storage):
        await storage.save_preset(Preset(id="p1", name="Gone"))
        assert await storage.delete_preset("p1") is True
        assert await storage.get_preset("p1") is None


# --- Manager Tests ---

@pytest.mark.asyncio
class TestSceneManager:
    async def test_create_scene(self, manager):
        scene = await manager.create_scene("Live Show", description="Friday night")
        assert scene.name == "Live Show"
        assert scene.id is not None

        loaded = await manager.get_scene(scene.id)
        assert loaded is not None
        assert loaded.name == "Live Show"

    async def test_list_scenes(self, manager):
        await manager.create_scene("A")
        await manager.create_scene("B")
        scenes = await manager.list_scenes()
        assert len(scenes) == 2

    async def test_activate_and_deactivate(self, manager, mapping_engine):
        scene = await manager.create_scene("Active")
        rule = MappingRule(
            id="ar1", name="RMS Rule",
            input_param="audio.rms",
            output_param="simulator.playback.1.fader",
        )
        scene.mapping_rules = [rule]
        await manager.update_scene(scene)

        success = await manager.activate(scene.id)
        assert success is True
        assert manager.active_scene_id == scene.id
        # Rule should be in the mapping engine
        engine_rules = mapping_engine.get_rules()
        assert any(r.id == "ar1" for r in engine_rules)

        await manager.deactivate()
        assert manager.active_scene_id is None
        engine_rules = mapping_engine.get_rules()
        assert not any(r.id == "ar1" for r in engine_rules)

    async def test_activate_nonexistent_returns_false(self, manager):
        assert await manager.activate("nonexistent") is False

    async def test_activate_replaces_previous(self, manager, mapping_engine):
        s1 = await manager.create_scene("Scene1")
        r1 = MappingRule(id="r1", name="R1", input_param="audio.rms", output_param="sim.pb.1.fader")
        s1.mapping_rules = [r1]
        await manager.update_scene(s1)

        s2 = await manager.create_scene("Scene2")
        r2 = MappingRule(id="r2", name="R2", input_param="audio.peak", output_param="sim.pb.2.fader")
        s2.mapping_rules = [r2]
        await manager.update_scene(s2)

        await manager.activate(s1.id)
        await manager.activate(s2.id)

        assert manager.active_scene_id == s2.id
        rules = mapping_engine.get_rules()
        rule_ids = [r.id for r in rules]
        assert "r1" not in rule_ids
        assert "r2" in rule_ids

    async def test_delete_active_scene_deactivates(self, manager, mapping_engine):
        scene = await manager.create_scene("Deletable")
        rule = MappingRule(id="dr1", name="D", input_param="audio.rms", output_param="sim.pb.1.fader")
        scene.mapping_rules = [rule]
        await manager.update_scene(scene)

        await manager.activate(scene.id)
        assert manager.active_scene_id == scene.id

        await manager.delete_scene(scene.id)
        assert manager.active_scene_id is None
        assert len(mapping_engine.get_rules()) == 0
