"""Patch manager: tracks which fixtures are patched to which DMX addresses."""

import uuid

import structlog

from src.fixtures.library import FixtureLibrary
from src.fixtures.models import ChannelDef, PatchEntry

logger = structlog.get_logger()


class PatchConflictError(Exception):
    """Raised when a patch operation would create an address conflict."""


class PatchManager:
    """Manages fixture patching: which fixtures occupy which DMX addresses."""

    def __init__(self, library: FixtureLibrary) -> None:
        self._library = library
        self._entries: dict[str, PatchEntry] = {}

    def add_fixture(
        self,
        profile_id: str,
        mode_index: int,
        universe: int,
        start_address: int,
        label: str,
    ) -> PatchEntry:
        """Patch a fixture at the given universe/address."""
        profile = self._library.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Unknown fixture profile: {profile_id}")
        if mode_index >= len(profile.modes):
            raise ValueError(f"Invalid mode index {mode_index} for {profile_id}")
        if start_address < 1 or start_address > 512:
            raise ValueError(f"Start address must be 1-512, got {start_address}")

        mode = profile.modes[mode_index]
        end_address = start_address + mode.channel_count - 1
        if end_address > 512:
            raise ValueError(f"Fixture extends beyond channel 512 (ends at {end_address})")

        # Check for conflicts
        conflicts = self._find_conflicts(universe, start_address, end_address, exclude_id=None)
        if conflicts:
            labels = [self._entries[c].label for c in conflicts]
            raise PatchConflictError(
                f"Address conflict with: {', '.join(labels)}"
            )

        entry = PatchEntry(
            id=str(uuid.uuid4()),
            fixture_profile_id=profile_id,
            mode_index=mode_index,
            universe=universe,
            start_address=start_address,
            label=label,
        )
        self._entries[entry.id] = entry
        logger.info("fixture_patched", label=label, universe=universe, address=start_address)
        return entry

    def remove_fixture(self, patch_id: str) -> bool:
        entry = self._entries.pop(patch_id, None)
        if entry:
            logger.info("fixture_unpatched", label=entry.label)
            return True
        return False

    def move_fixture(self, patch_id: str, new_universe: int, new_address: int) -> PatchEntry:
        """Move a patched fixture to a new universe/address."""
        entry = self._entries.get(patch_id)
        if entry is None:
            raise ValueError(f"Patch entry not found: {patch_id}")

        profile = self._library.get_profile(entry.fixture_profile_id)
        mode = profile.modes[entry.mode_index]
        end_address = new_address + mode.channel_count - 1

        if new_address < 1 or end_address > 512:
            raise ValueError(f"Invalid address range: {new_address}-{end_address}")

        conflicts = self._find_conflicts(new_universe, new_address, end_address, exclude_id=patch_id)
        if conflicts:
            labels = [self._entries[c].label for c in conflicts]
            raise PatchConflictError(f"Address conflict with: {', '.join(labels)}")

        entry.universe = new_universe
        entry.start_address = new_address
        return entry

    def validate(self) -> list[str]:
        """Check for address conflicts. Returns a list of error messages (empty = valid)."""
        errors = []
        entries = list(self._entries.values())
        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                if a.universe != b.universe:
                    continue
                a_range = self._get_address_range(a)
                b_range = self._get_address_range(b)
                if a_range and b_range and self._ranges_overlap(a_range, b_range):
                    errors.append(
                        f"Conflict: '{a.label}' ({a.start_address}-{a_range[1]}) "
                        f"overlaps with '{b.label}' ({b.start_address}-{b_range[1]}) "
                        f"on universe {a.universe}"
                    )
        return errors

    def get_channel_map(self) -> dict[tuple[int, int], tuple[PatchEntry, ChannelDef]]:
        """Return a mapping of (universe, channel) → (patch_entry, channel_def).

        Used by Art-Net/sACN output to know what fixture occupies each DMX channel.
        """
        channel_map: dict[tuple[int, int], tuple[PatchEntry, ChannelDef]] = {}
        for entry in self._entries.values():
            profile = self._library.get_profile(entry.fixture_profile_id)
            if profile is None:
                continue
            mode = profile.modes[entry.mode_index]
            for ch in mode.channels:
                address = entry.start_address + ch.offset
                if 1 <= address <= 512:
                    channel_map[(entry.universe, address)] = (entry, ch)
        return channel_map

    def get_entries(self) -> list[PatchEntry]:
        return list(self._entries.values())

    def get_entry(self, patch_id: str) -> PatchEntry | None:
        return self._entries.get(patch_id)

    def _find_conflicts(
        self, universe: int, start: int, end: int, exclude_id: str | None
    ) -> list[str]:
        """Find patch entries that conflict with the given address range."""
        conflicts = []
        for entry in self._entries.values():
            if entry.id == exclude_id:
                continue
            if entry.universe != universe:
                continue
            e_range = self._get_address_range(entry)
            if e_range and self._ranges_overlap((start, end), e_range):
                conflicts.append(entry.id)
        return conflicts

    def _get_address_range(self, entry: PatchEntry) -> tuple[int, int] | None:
        profile = self._library.get_profile(entry.fixture_profile_id)
        if profile is None:
            return None
        mode = profile.modes[entry.mode_index]
        return (entry.start_address, entry.start_address + mode.channel_count - 1)

    @staticmethod
    def _ranges_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return a[0] <= b[1] and b[0] <= a[1]
