import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "nms_viewer.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS loaded_files (
                filename  TEXT PRIMARY KEY,
                mtime     REAL NOT NULL,
                loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bases (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                portal_compact  TEXT NOT NULL,
                position        TEXT NOT NULL DEFAULT '',
                galaxy          TEXT,
                galaxy_num      INTEGER,
                galaxy_save_idx INTEGER,
                name            TEXT,
                portal_hex      TEXT,
                portal_sort_key TEXT,
                glyphs          TEXT,
                favourite       INTEGER DEFAULT 0,
                voxel_x         INTEGER,
                voxel_y         INTEGER,
                voxel_z         INTEGER,
                system_index    INTEGER,
                source_file     TEXT,
                notes           TEXT DEFAULT '',
                user_name       TEXT DEFAULT '',
                last_update_ts  INTEGER DEFAULT NULL,
                base_type       TEXT DEFAULT '',
                UNIQUE(portal_compact, position)
            );

            CREATE TABLE IF NOT EXISTS discoveries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                portal_compact  TEXT NOT NULL,
                dt              TEXT NOT NULL,
                galaxy          TEXT,
                galaxy_num      INTEGER,
                portal_hex      TEXT,
                portal_sort_key TEXT,
                glyphs          TEXT,
                custom_name     TEXT DEFAULT '',
                user_name       TEXT DEFAULT '',
                discoverer      TEXT DEFAULT '',
                source_file     TEXT,
                UNIQUE(portal_compact, dt)
            );

            CREATE TABLE IF NOT EXISTS players (
                uid  TEXT PRIMARY KEY,
                usn  TEXT NOT NULL DEFAULT ''
            );
        """)
        info = {row[1]: row for row in conn.execute("PRAGMA table_info(bases)").fetchall()}
        # Hard migration: position column missing — must rebuild from scratch
        if 'position' not in info:
            conn.executescript("""
                DROP TABLE bases;
                CREATE TABLE bases (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_compact  TEXT NOT NULL,
                    position        TEXT NOT NULL DEFAULT '',
                    galaxy          TEXT,
                    galaxy_num      INTEGER,
                    galaxy_save_idx INTEGER,
                    name            TEXT,
                    portal_hex      TEXT,
                    portal_sort_key TEXT,
                    glyphs          TEXT,
                    favourite       INTEGER DEFAULT 0,
                    voxel_x         INTEGER,
                    voxel_y         INTEGER,
                    voxel_z         INTEGER,
                    system_index    INTEGER,
                    source_file     TEXT,
                    notes           TEXT DEFAULT '',
                    user_name       TEXT DEFAULT '',
                    last_update_ts  INTEGER DEFAULT NULL,
                    base_type       TEXT DEFAULT '',
                    UNIQUE(portal_compact, position)
                );
                DELETE FROM loaded_files;
            """)
        # Safe migration: add base_type column without losing data; force reload to populate it
        elif 'base_type' not in info:
            conn.execute("ALTER TABLE bases ADD COLUMN base_type TEXT DEFAULT ''")
            conn.execute("DELETE FROM loaded_files")
        for table in ("discoveries",):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN notes TEXT DEFAULT ''")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE discoveries ADD COLUMN discovered_ts INTEGER DEFAULT NULL")
        except Exception:
            pass
        for col in ("owner TEXT DEFAULT ''", "owner_uid TEXT DEFAULT ''"):
            try:
                conn.execute(f"ALTER TABLE bases ADD COLUMN {col}")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE discoveries ADD COLUMN discoverer_uid TEXT DEFAULT ''")
        except Exception:
            pass


def needs_loading(filename: str, mtime: float) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT mtime FROM loaded_files WHERE filename = ?", (filename,)
        ).fetchone()
        return row is None or row["mtime"] != mtime


def clear_loaded_files():
    with _conn() as conn:
        conn.execute("DELETE FROM loaded_files")


def mark_loaded(filename: str, mtime: float):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO loaded_files (filename, mtime) VALUES (?, ?)",
            (filename, mtime),
        )


def upsert_player(uid: str, usn: str):
    if not uid:
        return
    with _conn() as conn:
        conn.execute(
            "INSERT INTO players (uid, usn) VALUES (?, ?)"
            " ON CONFLICT(uid) DO UPDATE SET"
            " usn = CASE WHEN excluded.usn != '' THEN excluded.usn ELSE usn END",
            (uid, usn or ""),
        )


def upsert_base(compact: str, base: dict, source_file: str) -> str:
    """Returns 'inserted' or 'updated'."""
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM bases WHERE portal_compact = ? AND position = ?",
            (compact, base["position"]),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO bases
                (portal_compact, position, galaxy, galaxy_num, galaxy_save_idx, name,
                 portal_hex, portal_sort_key, glyphs, favourite,
                 voxel_x, voxel_y, voxel_z, system_index, source_file, last_update_ts,
                 base_type, owner, owner_uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(portal_compact, position) DO UPDATE SET
                galaxy          = excluded.galaxy,
                galaxy_num      = excluded.galaxy_num,
                galaxy_save_idx = excluded.galaxy_save_idx,
                portal_hex      = excluded.portal_hex,
                portal_sort_key = excluded.portal_sort_key,
                glyphs          = excluded.glyphs,
                voxel_x         = excluded.voxel_x,
                voxel_y         = excluded.voxel_y,
                voxel_z         = excluded.voxel_z,
                system_index    = excluded.system_index,
                source_file     = excluded.source_file,
                base_type       = excluded.base_type,
                owner     = CASE WHEN excluded.owner != '' THEN excluded.owner ELSE owner END,
                owner_uid = CASE WHEN excluded.owner_uid != '' THEN excluded.owner_uid ELSE owner_uid END,
                name = CASE
                    WHEN excluded.last_update_ts IS NULL THEN name
                    WHEN last_update_ts IS NULL THEN excluded.name
                    WHEN excluded.last_update_ts >= last_update_ts THEN excluded.name
                    ELSE name
                END,
                favourite = CASE
                    WHEN excluded.last_update_ts IS NULL THEN favourite
                    WHEN last_update_ts IS NULL THEN excluded.favourite
                    WHEN excluded.last_update_ts >= last_update_ts THEN excluded.favourite
                    ELSE favourite
                END,
                last_update_ts = CASE
                    WHEN excluded.last_update_ts IS NULL THEN last_update_ts
                    WHEN last_update_ts IS NULL THEN excluded.last_update_ts
                    WHEN excluded.last_update_ts > last_update_ts THEN excluded.last_update_ts
                    ELSE last_update_ts
                END
            """,
            (
                compact,
                base["position"],
                base["galaxy"], base["galaxy_num"], base["galaxy_save_idx"], base["name"],
                base["portal_hex"], base["portal_sort_key"],
                json.dumps(base["glyphs"]),
                1 if base["favourite"] else 0,
                base.get("voxel_x"), base.get("voxel_y"), base.get("voxel_z"),
                base.get("system_index"),
                source_file,
                base.get("last_update_ts"),
                base.get("base_type", ""),
                base.get("owner", ""),
                base.get("owner_uid", ""),
            ),
        )
        return "inserted" if existing is None else "updated"


def upsert_discovery(compact: str, disc: dict, source_file: str) -> str:
    """Returns 'inserted', 'updated', or 'skipped'."""
    with _conn() as conn:
        existing = conn.execute(
            "SELECT custom_name, discoverer FROM discoveries WHERE portal_compact = ? AND dt = ?",
            (compact, disc["dt"]),
        ).fetchone()

        new_score = sum(bool(v) for v in (disc["custom_name"], disc["discoverer"]))

        if existing:
            old_score = sum(bool(v) for v in (existing["custom_name"], existing["discoverer"]))
            if new_score > old_score:
                conn.execute(
                    """
                    UPDATE discoveries
                       SET custom_name = ?, discoverer = ?, discoverer_uid = ?,
                           galaxy = ?, galaxy_num = ?, source_file = ?,
                           discovered_ts = COALESCE(discovered_ts, ?)
                     WHERE portal_compact = ? AND dt = ?
                    """,
                    (
                        disc["custom_name"], disc["discoverer"], disc.get("discoverer_uid", ""),
                        disc["galaxy"], disc["galaxy_num"], source_file,
                        disc.get("discovered_ts"),
                        compact, disc["dt"],
                    ),
                )
                return "updated"
            # Fill in discovered_ts and discoverer_uid even when the rest of the row is skipped.
            if disc.get("discovered_ts") is not None:
                conn.execute(
                    "UPDATE discoveries SET discovered_ts = ? "
                    "WHERE portal_compact = ? AND dt = ? AND discovered_ts IS NULL",
                    (disc["discovered_ts"], compact, disc["dt"]),
                )
            if disc.get("discoverer_uid"):
                conn.execute(
                    "UPDATE discoveries SET discoverer_uid = ? "
                    "WHERE portal_compact = ? AND dt = ? AND (discoverer_uid IS NULL OR discoverer_uid = '')",
                    (disc["discoverer_uid"], compact, disc["dt"]),
                )
            return "skipped"

        conn.execute(
            """
            INSERT INTO discoveries
                (portal_compact, dt, galaxy, galaxy_num, portal_hex,
                 portal_sort_key, glyphs, custom_name, discoverer, discoverer_uid,
                 source_file, discovered_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compact, disc["dt"],
                disc["galaxy"], disc["galaxy_num"],
                disc["portal_hex"], disc["portal_sort_key"],
                json.dumps(disc["glyphs"]),
                disc["custom_name"], disc["discoverer"], disc.get("discoverer_uid", ""),
                source_file,
                disc.get("discovered_ts"),
            ),
        )
        return "inserted"


def get_system_galaxy() -> dict:
    """Return coord→galaxy_save_idx mapping from all stored bases."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT voxel_x, voxel_y, voxel_z, system_index, galaxy_save_idx "
            "FROM bases WHERE voxel_x IS NOT NULL"
        ).fetchall()
        return {
            (r["voxel_x"], r["voxel_y"], r["voxel_z"], r["system_index"]): r["galaxy_save_idx"]
            for r in rows
        }


def get_bases() -> list:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bases WHERE base_type NOT IN ('PlayerShipBase', 'FreighterBase')"
            " ORDER BY galaxy_num, name"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "portal_compact": r["portal_compact"],
                "galaxy": r["galaxy"],
                "galaxy_num": r["galaxy_num"],
                "name": r["name"],
                "portal_hex": r["portal_hex"],
                "portal_sort_key": r["portal_sort_key"],
                "glyphs": json.loads(r["glyphs"]),
                "favourite": bool(r["favourite"]),
                "notes": r["notes"] or "",
                "user_name": r["user_name"] or "",
                "owner": r["owner"] or "",
            }
            for r in rows
        ]


def get_galaxy_summary(bases: list) -> list:
    counter = Counter((b["galaxy"], b["galaxy_num"]) for b in bases)
    return sorted(
        [{"name": g, "num": n, "count": c} for (g, n), c in counter.items()],
        key=lambda x: x["num"],
    )


def _fmt_ts(ts) -> str:
    if ts is None:
        return ""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def get_discoveries() -> list:
    with _conn() as conn:
        players = {
            r["uid"]: r["usn"]
            for r in conn.execute("SELECT uid, usn FROM players").fetchall()
        }
        rows = conn.execute(
            "SELECT * FROM discoveries ORDER BY dt, galaxy_num, portal_sort_key"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "dt": r["dt"],
                "galaxy": r["galaxy"],
                "galaxy_num": r["galaxy_num"],
                "portal_hex": r["portal_hex"],
                "portal_sort_key": r["portal_sort_key"],
                "glyphs": json.loads(r["glyphs"]),
                "custom_name": r["custom_name"] or "",
                "user_name": r["user_name"] or "",
                "discoverer": r["discoverer"] or players.get(r["discoverer_uid"] or "", ""),
                "discovered_ts": r["discovered_ts"],
                "discovered_date": _fmt_ts(r["discovered_ts"]),
                "notes": r["notes"] or "",
            }
            for r in rows
        ]


def update_user_name(discovery_id: int, name: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE discoveries SET user_name = ? WHERE id = ?",
            (name.strip(), discovery_id),
        )
        return cur.rowcount > 0


def update_discovery_notes(discovery_id: int, notes: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE discoveries SET notes = ? WHERE id = ?",
            (notes.strip(), discovery_id),
        )
        return cur.rowcount > 0


def update_base_user_name(base_id: int, name: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE bases SET user_name = ? WHERE id = ?",
            (name.strip(), base_id),
        )
        return cur.rowcount > 0


def update_base_notes(base_id: int, notes: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE bases SET notes = ? WHERE id = ?",
            (notes.strip(), base_id),
        )
        return cur.rowcount > 0
