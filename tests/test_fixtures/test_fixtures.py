"""Tests for fixture library and patch manager."""

import pytest

from src.fixtures.library import FixtureLibrary
from src.fixtures.models import ChannelDef, ChannelType, FixtureMode, FixtureProfile, PatchEntry
from src.fixtures.patch import PatchConflictError, PatchManager


class TestFixtureModels:
    def test_channel_def_roundtrip(self):
        ch = ChannelDef(offset=0, name="Red", channel_type=ChannelType.RED)
        d = ch.to_dict()
        restored = ChannelDef.from_dict(d)
        assert restored.name == "Red"
        assert restored.channel_type == ChannelType.RED
        assert restored.offset == 0

    def test_fixture_profile_roundtrip(self):
        profile = FixtureProfile(
            id="test", manufacturer="Test Co", name="Test Fixture",
            modes=[
                FixtureMode(name="3ch", channels=[
                    ChannelDef(0, "R", ChannelType.RED),
                    ChannelDef(1, "G", ChannelType.GREEN),
                    ChannelDef(2, "B", ChannelType.BLUE),
                ])
            ],
        )
        d = profile.to_dict()
        restored = FixtureProfile.from_dict(d)
        assert restored.id == "test"
        assert len(restored.modes) == 1
        assert len(restored.modes[0].channels) == 3

    def test_patch_entry_roundtrip(self):
        entry = PatchEntry(
            id="p1", fixture_profile_id="rgb", mode_index=0,
            universe=1, start_address=1, label="Front Wash 1",
        )
        d = entry.to_dict()
        restored = PatchEntry.from_dict(d)
        assert restored.label == "Front Wash 1"
        assert restored.universe == 1


class TestFixtureLibrary:
    def test_load_profiles_from_fixtures_dir(self):
        lib = FixtureLibrary()
        count = lib.load_profiles()
        assert count == 10
        assert lib.count == 10

    def test_get_profile(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        p = lib.get_profile("generic_rgb")
        assert p is not None
        assert p.name == "RGB Fixture"
        assert len(p.modes) == 1
        assert len(p.modes[0].channels) == 3

    def test_get_nonexistent(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        assert lib.get_profile("nope") is None

    def test_search_by_name(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        results = lib.search("moving")
        assert len(results) == 2  # spot + wash

    def test_search_by_manufacturer(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        results = lib.search("generic")
        assert len(results) == 10

    def test_search_case_insensitive(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        results = lib.search("RGB")
        assert any("RGB" in p.name for p in results)

    def test_list_all(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        assert len(lib.list_all()) == 10

    def test_load_empty_directory(self, tmp_path):
        lib = FixtureLibrary()
        count = lib.load_profiles(tmp_path)
        assert count == 0

    def test_load_nonexistent_directory(self):
        lib = FixtureLibrary()
        count = lib.load_profiles("/nonexistent/path")
        assert count == 0


class TestPatchManager:
    @pytest.fixture
    def library(self):
        lib = FixtureLibrary()
        lib.load_profiles()
        return lib

    @pytest.fixture
    def pm(self, library):
        return PatchManager(library)

    def test_add_fixture(self, pm):
        entry = pm.add_fixture("generic_rgb", 0, 1, 1, "Front Wash")
        assert entry.label == "Front Wash"
        assert entry.universe == 1
        assert entry.start_address == 1

    def test_add_fixture_unknown_profile(self, pm):
        with pytest.raises(ValueError, match="Unknown fixture"):
            pm.add_fixture("nonexistent", 0, 1, 1, "Bad")

    def test_add_fixture_invalid_mode(self, pm):
        with pytest.raises(ValueError, match="Invalid mode"):
            pm.add_fixture("generic_rgb", 99, 1, 1, "Bad")

    def test_add_fixture_address_too_low(self, pm):
        with pytest.raises(ValueError, match="1-512"):
            pm.add_fixture("generic_rgb", 0, 1, 0, "Bad")

    def test_add_fixture_extends_past_512(self, pm):
        with pytest.raises(ValueError, match="beyond channel 512"):
            pm.add_fixture("generic_rgb", 0, 1, 511, "Bad")  # 3ch: 511+2=513

    def test_address_conflict(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 1, "First")  # occupies 1-3
        with pytest.raises(PatchConflictError):
            pm.add_fixture("generic_rgb", 0, 1, 3, "Overlap")  # occupies 3-5

    def test_no_conflict_different_universe(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 1, "Uni1")
        entry = pm.add_fixture("generic_rgb", 0, 2, 1, "Uni2")
        assert entry is not None

    def test_no_conflict_adjacent(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 1, "First")   # 1-3
        entry = pm.add_fixture("generic_rgb", 0, 1, 4, "Second")  # 4-6
        assert entry is not None

    def test_remove_fixture(self, pm):
        entry = pm.add_fixture("generic_rgb", 0, 1, 1, "Removable")
        assert pm.remove_fixture(entry.id) is True
        assert len(pm.get_entries()) == 0

    def test_remove_nonexistent(self, pm):
        assert pm.remove_fixture("nope") is False

    def test_move_fixture(self, pm):
        entry = pm.add_fixture("generic_rgb", 0, 1, 1, "Movable")
        moved = pm.move_fixture(entry.id, 2, 100)
        assert moved.universe == 2
        assert moved.start_address == 100

    def test_move_conflict(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 1, "Fixed")
        entry = pm.add_fixture("generic_rgb", 0, 1, 10, "Mobile")
        with pytest.raises(PatchConflictError):
            pm.move_fixture(entry.id, 1, 1)  # conflicts with Fixed

    def test_validate_clean(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 1, "A")
        pm.add_fixture("generic_rgb", 0, 1, 10, "B")
        errors = pm.validate()
        assert errors == []

    def test_get_channel_map(self, pm):
        pm.add_fixture("generic_rgb", 0, 1, 100, "RGB at 100")
        cmap = pm.get_channel_map()
        assert (1, 100) in cmap
        assert (1, 101) in cmap
        assert (1, 102) in cmap
        assert (1, 103) not in cmap
        entry, ch_def = cmap[(1, 100)]
        assert ch_def.channel_type == ChannelType.RED

    def test_get_entries(self, pm):
        pm.add_fixture("generic_dimmer", 0, 1, 1, "D1")
        pm.add_fixture("generic_dimmer", 0, 1, 2, "D2")
        assert len(pm.get_entries()) == 2
