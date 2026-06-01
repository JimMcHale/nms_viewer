import json
import sqlite3
from collections import Counter
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
                portal_compact  TEXT PRIMARY KEY,
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
                source_file     TEXT
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
        """)
        for table in ("bases", "discoveries"):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN notes TEXT DEFAULT ''")
            except Exception:
                pass


def needs_loading(filename: str, mtime: float) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT mtime FROM loaded_files WHERE filename = ?", (filename,)
        ).fetchone()
        return row is None or row["mtime"] != mtime


def mark_loaded(filename: str, mtime: float):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO loaded_files (filename, mtime) VALUES (?, ?)",
            (filename, mtime),
        )


def upsert_base(compact: str, base: dict, source_file: str):
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO bases
                (portal_compact, galaxy, galaxy_num, galaxy_save_idx, name,
                 portal_hex, portal_sort_key, glyphs, favourite,
                 voxel_x, voxel_y, voxel_z, system_index, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compact,
                base["galaxy"], base["galaxy_num"], base["galaxy_save_idx"], base["name"],
                base["portal_hex"], base["portal_sort_key"],
                json.dumps(base["glyphs"]),
                1 if base["favourite"] else 0,
                base.get("voxel_x"), base.get("voxel_y"), base.get("voxel_z"),
                base.get("system_index"),
                source_file,
            ),
        )


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
                       SET custom_name = ?, discoverer = ?,
                           galaxy = ?, galaxy_num = ?, source_file = ?
                     WHERE portal_compact = ? AND dt = ?
                    """,
                    (
                        disc["custom_name"], disc["discoverer"],
                        disc["galaxy"], disc["galaxy_num"], source_file,
                        compact, disc["dt"],
                    ),
                )
                return "updated"
            return "skipped"

        conn.execute(
            """
            INSERT INTO discoveries
                (portal_compact, dt, galaxy, galaxy_num, portal_hex,
                 portal_sort_key, glyphs, custom_name, discoverer, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compact, disc["dt"],
                disc["galaxy"], disc["galaxy_num"],
                disc["portal_hex"], disc["portal_sort_key"],
                json.dumps(disc["glyphs"]),
                disc["custom_name"], disc["discoverer"],
                source_file,
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
        rows = conn.execute("SELECT * FROM bases ORDER BY galaxy_num, name").fetchall()
        return [
            {
                "portal_compact": r["portal_compact"],
                "galaxy": r["galaxy"],
                "galaxy_num": r["galaxy_num"],
                "name": r["name"],
                "portal_hex": r["portal_hex"],
                "portal_sort_key": r["portal_sort_key"],
                "glyphs": json.loads(r["glyphs"]),
                "favourite": bool(r["favourite"]),
                "notes": r["notes"] or "",
            }
            for r in rows
        ]


def get_galaxy_summary(bases: list) -> list:
    counter = Counter((b["galaxy"], b["galaxy_num"]) for b in bases)
    return sorted(
        [{"name": g, "num": n, "count": c} for (g, n), c in counter.items()],
        key=lambda x: x["num"],
    )


def get_discoveries() -> list:
    with _conn() as conn:
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
                "discoverer": r["discoverer"] or "",
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


def update_base_notes(portal_compact: str, notes: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE bases SET notes = ? WHERE portal_compact = ?",
            (notes.strip(), portal_compact),
        )
        return cur.rowcount > 0
