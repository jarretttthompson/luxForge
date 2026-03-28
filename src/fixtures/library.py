"""Fixture profile library: loads and searches fixture profiles from JSON files."""

import json
from pathlib import Path

import structlog

from src.fixtures.models import FixtureProfile

logger = structlog.get_logger()

DEFAULT_FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class FixtureLibrary:
    """Loads fixture profiles from a directory of JSON files."""

    def __init__(self) -> None:
        self._profiles: dict[str, FixtureProfile] = {}

    def load_profiles(self, directory: str | Path | None = None) -> int:
        """Scan directory for JSON files and parse into FixtureProfile objects.

        Returns the number of profiles loaded.
        """
        path = Path(directory) if directory else DEFAULT_FIXTURES_DIR
        if not path.is_dir():
            logger.warning("fixtures_directory_not_found", path=str(path))
            return 0

        count = 0
        for json_file in sorted(path.glob("*.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                profile = FixtureProfile.from_dict(data)
                self._profiles[profile.id] = profile
                count += 1
            except Exception:
                logger.exception("fixture_profile_load_error", file=str(json_file))

        logger.info("fixtures_loaded", count=count, directory=str(path))
        return count

    def get_profile(self, profile_id: str) -> FixtureProfile | None:
        return self._profiles.get(profile_id)

    def search(self, query: str) -> list[FixtureProfile]:
        """Search profiles by name or manufacturer (case-insensitive)."""
        q = query.lower()
        return [
            p for p in self._profiles.values()
            if q in p.name.lower() or q in p.manufacturer.lower()
        ]

    def list_all(self) -> list[FixtureProfile]:
        return list(self._profiles.values())

    @property
    def count(self) -> int:
        return len(self._profiles)
