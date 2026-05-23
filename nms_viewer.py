from flask import Flask, render_template, request, jsonify
from pathlib import Path
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from extract_nms_bases_v8 import (
    load_json_with_backslash_fix,
    extract_base_rows,
    dedupe_exact_rows,
    annotate_notes,
    sort_rows,
    decode_packed_galactic_address_signed,
    build_portal_fields,
    GALAXY_NAME_BY_SAVE_INDEX,
)
import db

app = Flask(__name__)
db.init_db()

IMPORTS_DIR = Path(__file__).parent / "imports"
PRINT_DT = {"Planet", "Sector", "SolarSystem"}


def fmt4(compact):
    if len(compact) == 12:
        return f"{compact[0:4]} {compact[4:8]} {compact[8:12]}"
    return compact


def portal_sort_key(compact):
    """Reorder PSSSYYZZZXXX → SSSPYYZZZXXX so hex sort gives system, planet, voxel order."""
    if len(compact) == 12:
        return compact[1:4] + compact[0] + compact[4:]
    return compact


def galaxy_label(save_idx):
    name = GALAXY_NAME_BY_SAVE_INDEX.get(save_idx, "")
    return (name or f"Galaxy {save_idx + 1}"), (save_idx + 1)


def decode_ua(ua_raw):
    """Decode a discovery UA value to portal fields. Returns (compact, decoded) or (None, None)."""
    if ua_raw is None:
        return None, None
    try:
        ua_int = int(ua_raw, 16) if isinstance(ua_raw, str) else int(ua_raw)
        dec = decode_packed_galactic_address_signed(ua_int)
        if not dec:
            return None, None
        pf = build_portal_fields(
            planet_index=dec["PlanetIndex"],
            system_index=dec["SolarSystemIndex"],
            voxel_x=dec["VoxelX"],
            voxel_y=dec["VoxelY"],
            voxel_z=dec["VoxelZ"],
        )
        compact = pf["Glyph String (No Spaces)"]
        return (compact or None), dec
    except (ValueError, TypeError):
        return None, None


def _file_sort_key(path: Path) -> float:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").timestamp()
        except ValueError:
            pass
    return path.stat().st_mtime


def _process_new_files():
    json_files = sorted(IMPORTS_DIR.glob("*.json"), key=_file_sort_key)
    if not json_files:
        print("No JSON files found in imports/")
        return

    # Seed system→galaxy from already-indexed bases so new files resolve correctly.
    system_galaxy = db.get_system_galaxy()
    any_new = False

    for json_path in json_files:
        mtime = json_path.stat().st_mtime
        if not db.needs_loading(json_path.name, mtime):
            print(f"\n--- {json_path.name} [cached] ---")
            continue

        any_new = True
        print(f"\n--- {json_path.name} ---")
        data = load_json_with_backslash_fix(json_path)

        rows = extract_base_rows(data)
        rows = dedupe_exact_rows(rows)
        rows = annotate_notes(rows)
        rows = sort_rows(rows)

        for row in rows:
            coord_key = (row["VoxelX"], row["VoxelY"], row["VoxelZ"], row["SystemIndex"])
            if None not in coord_key:
                system_galaxy[coord_key] = row["Galaxy Number (Save)"]

        file_base_count = 0
        for row in rows:
            compact = row["Glyph String (No Spaces)"]
            if not row["Base Name"] or compact == "0" * 12:
                continue
            base = {
                "galaxy": row["Galaxy"],
                "galaxy_num": row["Galaxy Number (Human)"],
                "galaxy_save_idx": row["Galaxy Number (Save)"],
                "name": row["Base Name"],
                "portal_hex": fmt4(compact),
                "portal_sort_key": portal_sort_key(compact),
                "glyphs": list(compact),
                "favourite": row["IsFavourite"],
                "voxel_x": row["VoxelX"],
                "voxel_y": row["VoxelY"],
                "voxel_z": row["VoxelZ"],
                "system_index": row["SystemIndex"],
            }
            db.upsert_base(compact, base, json_path.name)
            file_base_count += 1

        discovery_records = (
            data.get("DiscoveryManagerData", {})
                .get("DiscoveryData-v1", {})
                .get("Store", {})
                .get("Record", [])
        )

        file_dt_counts = Counter(
            rec.get("DD", {}).get("DT", "") for rec in discovery_records
        )
        print(
            f"  Bases: {file_base_count}"
            f"  Planets: {file_dt_counts['Planet']}"
            f"  Sectors: {file_dt_counts['Sector']}"
            f"  Solar Systems: {file_dt_counts['SolarSystem']}"
        )

        for rec in discovery_records:
            dd = rec.get("DD", {})
            dm = rec.get("DM", {})
            ows = rec.get("OWS", {})
            vp = dd.get("VP", [])
            dt = dd.get("DT", "")

            compact, dec = decode_ua(dd.get("UA"))
            if not compact:
                continue

            coord_key = (dec["VoxelX"], dec["VoxelY"], dec["VoxelZ"], dec["SolarSystemIndex"])
            if coord_key in system_galaxy:
                gal_idx = system_galaxy[coord_key]
            else:
                try:
                    vp1 = int(vp[1]) if isinstance(vp, list) and len(vp) >= 2 else None
                    gal_idx = vp1 if vp1 is not None and 0 <= vp1 <= 255 else 0
                except (ValueError, TypeError):
                    gal_idx = 0

            gal_name, gal_num = galaxy_label(gal_idx)
            disc = {
                "dt": dt,
                "galaxy": gal_name,
                "galaxy_num": gal_num,
                "portal_hex": fmt4(compact),
                "portal_sort_key": portal_sort_key(compact),
                "glyphs": list(compact),
                "custom_name": dm.get("CN", ""),
                "discoverer": ows.get("USN", ""),
            }

            result = db.upsert_discovery(compact, disc, json_path.name)

            if result == "inserted" and dt in PRINT_DT:
                cn = disc["custom_name"] or "(unnamed)"
                dis = disc["discoverer"] or "unknown"
                print(f"  NEW {dt}: {cn} | {fmt4(compact)} | {gal_name} | {dis}")
            elif result == "updated":
                cn = disc["custom_name"] or "(unnamed)"
                print(f"  UPDATED {dt}: {cn} | {fmt4(compact)} | {gal_name}")

        db.mark_loaded(json_path.name, mtime)

    if any_new:
        all_bases = db.get_bases()
        all_disc = db.get_discoveries()
        dt_totals = Counter(d["dt"] for d in all_disc)
        solar = [d for d in all_disc if d["dt"] == "SolarSystem"]
        named = sum(1 for d in solar if d["user_name"] or d["custom_name"])
        print(
            f"\n=== TOTALS ==="
            f"\n  Bases: {len(all_bases)}"
            f"  Planets: {dt_totals['Planet']}"
            f"  Sectors: {dt_totals['Sector']}"
            f"  Solar Systems: {dt_totals['SolarSystem']}"
            f"\n  Named systems: {named}  Unnamed systems: {len(solar) - named}"
        )


def load_all_data():
    _process_new_files()
    bases = db.get_bases()
    discoveries = db.get_discoveries()
    galaxy_summary = db.get_galaxy_summary(bases)
    stats = {
        "total_bases": len(bases),
        "favourites": sum(1 for b in bases if b["favourite"]),
        "galaxies": len(galaxy_summary),
        "discoveries": len(discoveries),
    }
    return stats, galaxy_summary, bases, discoveries


@app.route("/")
def index():
    stats, galaxy_summary, bases, discoveries = load_all_data()
    return render_template(
        "index.html",
        stats=stats,
        galaxy_summary=galaxy_summary,
        bases=bases,
        discoveries=discoveries,
    )


@app.route("/api/discovery/name", methods=["POST"])
def api_set_name():
    data = request.get_json(force=True)
    disc_id = data.get("id")
    name = data.get("name", "")
    if not isinstance(disc_id, int):
        return jsonify({"ok": False, "error": "invalid id"}), 400
    ok = db.update_user_name(disc_id, name)
    return jsonify({"ok": ok})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
