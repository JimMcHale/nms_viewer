from flask import Flask, render_template
from pathlib import Path
import re
import sys
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
from collections import Counter

app = Flask(__name__)

IMPORTS_DIR = Path(__file__).parent / "imports"
PRINT_DT = {"Planet", "Sector", "SolarSystem"}

_cache = None
_cache_file_state = None


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


def _file_state():
    files = sorted(IMPORTS_DIR.glob("*.json"), key=_file_sort_key)
    return {f: f.stat().st_mtime for f in files}


def load_all_data():
    global _cache, _cache_file_state

    current_state = _file_state()
    if current_state == _cache_file_state and _cache is not None:
        return _cache

    json_files = sorted(current_state.keys(), key=_file_sort_key)
    if not json_files:
        print("No JSON files found in imports/")
        return {}, [], [], []

    all_base_rows = []
    seen_base_keys = set()
    all_discoveries = []
    seen_discovery_keys = {}  # (compact, dt) -> index in all_discoveries
    system_galaxy = {}

    for json_path in json_files:
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

        for row in rows:
            key = row.get("Glyph String (No Spaces)")
            if key and key != "0" * 12 and key not in seen_base_keys:
                seen_base_keys.add(key)
                all_base_rows.append(row)

        discovery_records = (
            data.get("DiscoveryManagerData", {})
                .get("DiscoveryData-v1", {})
                .get("Store", {})
                .get("Record", [])
        )

        file_base_count = sum(
            1 for row in rows
            if row["Base Name"] and row["Glyph String (No Spaces)"] != "0" * 12
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
            new_rec = {
                "dt": dt,
                "galaxy": gal_name,
                "galaxy_num": gal_num,
                "portal_hex": fmt4(compact),
                "portal_sort_key": portal_sort_key(compact),
                "glyphs": list(compact),
                "custom_name": dm.get("CN", ""),
                "discoverer": ows.get("USN", ""),
            }
            new_score = sum(bool(v) for v in (new_rec["custom_name"], new_rec["discoverer"]))

            dedup_key = (compact, dt)
            if dedup_key in seen_discovery_keys:
                idx = seen_discovery_keys[dedup_key]
                existing = all_discoveries[idx]
                existing_score = sum(bool(v) for v in (existing["custom_name"], existing["discoverer"]))
                if new_score > existing_score:
                    print(
                        f"  UPDATED {dt}: {fmt4(compact)}"
                        f" name: {existing['custom_name']!r} -> {new_rec['custom_name']!r}"
                        f" discoverer: {existing['discoverer']!r} -> {new_rec['discoverer']!r}"
                    )
                    all_discoveries[idx] = new_rec
                continue

            seen_discovery_keys[dedup_key] = len(all_discoveries)
            all_discoveries.append(new_rec)

            if dt in PRINT_DT:
                custom_name = new_rec["custom_name"] or "(unnamed)"
                discoverer = new_rec["discoverer"] or "unknown"
                print(f"  NEW {dt}: {custom_name} | {fmt4(compact)} | {gal_name} | {discoverer}")

    galaxy_counter = Counter(
        (row["Galaxy Number (Save)"], row["Galaxy"], row["Galaxy Number (Human)"])
        for row in all_base_rows
    )
    galaxy_summary = sorted(
        [
            {"name": name, "num": human_num, "count": galaxy_counter[(sn, name, human_num)]}
            for (sn, name, human_num) in galaxy_counter
        ],
        key=lambda x: x["num"],
    )

    bases = []
    for row in all_base_rows:
        compact = row["Glyph String (No Spaces)"]
        if not row["Base Name"] or compact == "0" * 12:
            continue
        bases.append(
            {
                "galaxy": row["Galaxy"],
                "galaxy_num": row["Galaxy Number (Human)"],
                "name": row["Base Name"],
                "portal_hex": fmt4(compact),
                "portal_sort_key": portal_sort_key(compact),
                "glyphs": list(compact),
                "favourite": row["IsFavourite"],
            }
        )

    stats = {
        "total_bases": len(bases),
        "favourites": sum(1 for b in bases if b["favourite"]),
        "galaxies": len(galaxy_summary),
        "discoveries": len(all_discoveries),
    }

    dt_totals = Counter(d["dt"] for d in all_discoveries)
    solar_systems = [d for d in all_discoveries if d["dt"] == "SolarSystem"]
    named_systems = sum(1 for d in solar_systems if d["custom_name"])
    unnamed_systems = len(solar_systems) - named_systems
    print(
        f"\n=== TOTALS ==="
        f"\n  Bases: {len(bases)}"
        f"  Planets: {dt_totals['Planet']}"
        f"  Sectors: {dt_totals['Sector']}"
        f"  Solar Systems: {dt_totals['SolarSystem']}"
        f"\n  Named systems: {named_systems}  Unnamed systems: {unnamed_systems}"
    )

    result = stats, galaxy_summary, bases, all_discoveries
    _cache = result
    _cache_file_state = current_state
    return result


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
