"""Tests for FastAPI REST routes."""

import pytest
from fastapi.testclient import TestClient

from src.api import dependencies as deps
from src.api.app import create_app
from src.console.simulator import SimulatorConsole
from src.engine.events import AsyncEventBus
from src.engine.state import AppState
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.config import AppConfig
from src.fixtures.library import FixtureLibrary
from src.fixtures.patch import PatchManager


@pytest.fixture(autouse=True)
def setup_deps():
    """Wire up test dependencies before each test."""
    console = SimulatorConsole(num_playbacks=3)
    registry = ParameterRegistry()
    registry.register_console(console)

    deps.state = AppState()
    deps.state.active_console = console.name
    deps.event_bus = AsyncEventBus()
    deps.mapping_engine = MappingEngine(registry=registry)
    deps.param_registry = registry
    deps.console = console
    deps.adapters = []
    deps.audio_source = None
    deps.config = AppConfig()
    deps.scene_manager = None

    library = FixtureLibrary()
    library.load_profiles()
    deps.fixture_library = library
    deps.patch_manager = PatchManager(library)

    yield

    # Clean up
    deps.state = None
    deps.event_bus = None
    deps.mapping_engine = None
    deps.param_registry = None
    deps.console = None
    deps.adapters = []
    deps.audio_source = None
    deps.config = None
    deps.scene_manager = None
    deps.fixture_library = None
    deps.patch_manager = None


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestSystemRoutes:
    def test_health(self, client):
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["engine_running"] is False
        assert "fps" in data
        assert "active_console" in data


class TestProtocolRoutes:
    def test_protocol_status_empty(self, client):
        resp = client.get("/api/protocols/status")
        assert resp.status_code == 200
        assert resp.json()["protocols"] == []

    def test_protocol_status_with_adapters(self, client):
        from src.engine.state import ProtocolStatus
        deps.state.protocol_statuses["osc"] = ProtocolStatus(
            name="osc", connected=True, dry_run=True, messages_sent=42
        )
        resp = client.get("/api/protocols/status")
        assert resp.status_code == 200
        protos = resp.json()["protocols"]
        assert len(protos) == 1
        assert protos[0]["name"] == "osc"
        assert protos[0]["messages_sent"] == 42


class TestMappingRoutes:
    def test_list_rules_empty(self, client):
        resp = client.get("/api/mappings")
        assert resp.status_code == 200
        assert resp.json()["rules"] == []

    def test_create_rule(self, client):
        resp = client.post("/api/mappings", json={
            "name": "Test Rule",
            "input_param": "audio.rms",
            "output_param": "simulator.playback.1.fader",
            "transform_chain": [{"type": "Scale", "min_out": 0, "max_out": 255}],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Rule"
        assert data["input_param"] == "audio.rms"
        assert data["enabled"] is True
        assert "id" in data

    def test_create_and_list_rules(self, client):
        client.post("/api/mappings", json={
            "name": "Rule 1",
            "input_param": "audio.rms",
            "output_param": "simulator.playback.1.fader",
        })
        client.post("/api/mappings", json={
            "name": "Rule 2",
            "input_param": "audio.peak",
            "output_param": "simulator.playback.2.fader",
        })
        resp = client.get("/api/mappings")
        assert len(resp.json()["rules"]) == 2

    def test_get_rule_by_id(self, client):
        create_resp = client.post("/api/mappings", json={
            "name": "Findable",
            "input_param": "audio.rms",
            "output_param": "simulator.playback.1.fader",
        })
        rule_id = create_resp.json()["id"]

        resp = client.get(f"/api/mappings/{rule_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Findable"

    def test_get_rule_not_found(self, client):
        resp = client.get("/api/mappings/nonexistent")
        assert resp.status_code == 404

    def test_update_rule(self, client):
        create_resp = client.post("/api/mappings", json={
            "name": "Original",
            "input_param": "audio.rms",
            "output_param": "simulator.playback.1.fader",
        })
        rule_id = create_resp.json()["id"]

        resp = client.put(f"/api/mappings/{rule_id}", json={
            "name": "Updated",
            "enabled": False,
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"
        assert resp.json()["enabled"] is False

    def test_delete_rule(self, client):
        create_resp = client.post("/api/mappings", json={
            "name": "Deletable",
            "input_param": "audio.rms",
            "output_param": "simulator.playback.1.fader",
        })
        rule_id = create_resp.json()["id"]

        resp = client.delete(f"/api/mappings/{rule_id}")
        assert resp.status_code == 204

        list_resp = client.get("/api/mappings")
        assert len(list_resp.json()["rules"]) == 0

    def test_list_parameters(self, client):
        resp = client.get("/api/mappings/parameters/list")
        assert resp.status_code == 200
        data = resp.json()
        input_names = [p["name"] for p in data["inputs"]]
        assert "audio.rms" in input_names
        assert len(data["outputs"]) > 0


class TestAudioRoutes:
    def test_get_audio_config(self, client):
        resp = client.get("/api/audio/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "sample_rate" in data
        assert "simulator_enabled" in data

    def test_list_devices_no_source(self, client):
        resp = client.get("/api/audio/devices")
        assert resp.status_code == 200
        assert resp.json()["devices"] == []


class TestSceneRoutes:
    def test_list_scenes_placeholder(self, client):
        resp = client.get("/api/scenes")
        assert resp.status_code == 200
        assert resp.json()["scenes"] == []


class TestFixtureRoutes:
    def test_list_profiles(self, client):
        resp = client.get("/api/fixtures/profiles")
        assert resp.status_code == 200
        assert len(resp.json()["profiles"]) == 10

    def test_get_profile(self, client):
        resp = client.get("/api/fixtures/profiles/generic_rgb")
        assert resp.status_code == 200
        assert resp.json()["name"] == "RGB Fixture"

    def test_search_profiles(self, client):
        resp = client.get("/api/fixtures/profiles/search?q=moving")
        assert resp.status_code == 200
        assert len(resp.json()["profiles"]) == 2

    def test_get_empty_patch(self, client):
        resp = client.get("/api/fixtures/patch")
        assert resp.status_code == 200
        assert resp.json()["entries"] == []

    def test_add_patch_entry(self, client):
        resp = client.post("/api/fixtures/patch", json={
            "profile_id": "generic_rgb",
            "mode_index": 0,
            "universe": 1,
            "start_address": 1,
            "label": "Front Wash",
        })
        assert resp.status_code == 201
        assert resp.json()["label"] == "Front Wash"

    def test_patch_conflict(self, client):
        client.post("/api/fixtures/patch", json={
            "profile_id": "generic_rgb", "universe": 1,
            "start_address": 1, "label": "A",
        })
        resp = client.post("/api/fixtures/patch", json={
            "profile_id": "generic_rgb", "universe": 1,
            "start_address": 2, "label": "B",
        })
        assert resp.status_code == 409
