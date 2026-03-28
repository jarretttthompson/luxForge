"""SQLite-backed persistence for scenes and presets."""

import json

import aiosqlite
import structlog

from src.scenes.models import Preset, Scene

logger = structlog.get_logger()


class SceneStorage:
    """Async SQLite storage for scenes and presets."""

    def __init__(self, db_path: str = "luxforge.db") -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init_db(self) -> None:
        """Create tables if they don't exist and store the connection."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                mapping_rules TEXT DEFAULT '[]',
                cuelist_triggers TEXT DEFAULT '[]',
                transition_time_ms INTEGER DEFAULT 0
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                transform_chain TEXT DEFAULT '[]'
            )
        """)
        await self._db.commit()
        logger.info("scene_storage_initialized", db_path=self._db_path)

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    # --- Scenes ---

    async def save_scene(self, scene: Scene) -> None:
        assert self._db is not None
        await self._db.execute(
            """INSERT OR REPLACE INTO scenes
               (id, name, description, mapping_rules, cuelist_triggers, transition_time_ms)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                scene.id,
                scene.name,
                scene.description,
                json.dumps([r.to_dict() for r in scene.mapping_rules]),
                json.dumps([
                    {"target": c.target, "value": c.value, "command_type": c.command_type.value}
                    for c in scene.cuelist_triggers
                ]),
                scene.transition_time_ms,
            ),
        )
        await self._db.commit()

    async def get_scene(self, scene_id: str) -> Scene | None:
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT id, name, description, mapping_rules, cuelist_triggers, transition_time_ms FROM scenes WHERE id = ?",
            (scene_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_scene(row)

    async def list_scenes(self) -> list[Scene]:
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT id, name, description, mapping_rules, cuelist_triggers, transition_time_ms FROM scenes ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [self._row_to_scene(row) for row in rows]

    async def delete_scene(self, scene_id: str) -> bool:
        assert self._db is not None
        cursor = await self._db.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
        await self._db.commit()
        return cursor.rowcount > 0

    def _row_to_scene(self, row: tuple) -> Scene:
        data = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "mapping_rules": json.loads(row[3]),
            "cuelist_triggers": json.loads(row[4]),
            "transition_time_ms": row[5],
        }
        return Scene.from_dict(data)

    # --- Presets ---

    async def save_preset(self, preset: Preset) -> None:
        assert self._db is not None
        await self._db.execute(
            "INSERT OR REPLACE INTO presets (id, name, transform_chain) VALUES (?, ?, ?)",
            (preset.id, preset.name, json.dumps(preset.transform_chain)),
        )
        await self._db.commit()

    async def get_preset(self, preset_id: str) -> Preset | None:
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT id, name, transform_chain FROM presets WHERE id = ?",
            (preset_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Preset(id=row[0], name=row[1], transform_chain=json.loads(row[2]))

    async def list_presets(self) -> list[Preset]:
        assert self._db is not None
        cursor = await self._db.execute("SELECT id, name, transform_chain FROM presets ORDER BY name")
        rows = await cursor.fetchall()
        return [Preset(id=r[0], name=r[1], transform_chain=json.loads(r[2])) for r in rows]

    async def delete_preset(self, preset_id: str) -> bool:
        assert self._db is not None
        cursor = await self._db.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
        await self._db.commit()
        return cursor.rowcount > 0
