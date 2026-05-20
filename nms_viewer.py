from flask import Flask, render_template, request
from pathlib import Path
import sys

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

DEFAULT_SAVE = Path(__file__).parent / "save.hg.json"


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


def load_data(save_path):
    data = load_json_with_backslash_fix(Path(save_path))

    rows = extract_base_rows(data)
    rows = dedupe_exact_rows(rows)
    rows = annotate_notes(rows)
    rows = sort_rows(rows)

    galaxy_counter = Counter(
        (row["Galaxy Number (Save)"], row["Galaxy"], row["Galaxy Number (Human)"])
        for row in rows
    )
    galaxy_summary = sorted(
        [
            {"name": name, "num": human_num, "count": galaxy_counter[(sn, name, human_num)]}
            for (sn, name, human_num) in galaxy_counter
        ],
        key=lambda x: x["num"],
    )

    # Build coordinate → galaxy lookup from base rows so discoveries in known
    # systems get the correct galaxy even when VP[1] is absent.
    system_galaxy = {}
    for row in rows:
        key = (row["VoxelX"], row["VoxelY"], row["VoxelZ"], row["SystemIndex"])
        if None not in key:
            system_galaxy[key] = row["Galaxy Number (Save)"]

    bases = []
    for row in rows:
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

    # Discoveries from DiscoveryManagerData
    discovery_records = (
        data.get("DiscoveryManagerData", {})
            .get("DiscoveryData-v1", {})
            .get("Store", {})
            .get("Record", [])
    )

    discoveries = []
    seen_discoveries = set()
    for rec in discovery_records:
        dd = rec.get("DD", {})
        dm = rec.get("DM", {})
        ows = rec.get("OWS", {})
        vp = dd.get("VP", [])

        compact, dec = decode_ua(dd.get("UA"))
        if not compact:
            continue

        dedup_key = (compact, dd.get("DT", ""))
        if dedup_key in seen_discoveries:
            continue
        seen_discoveries.add(dedup_key)

        # Prefer coordinate lookup (works even when VP[1] is absent).
        # Fall back to VP[1], then 0.
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
        discoveries.append(
            {
                "dt": dd.get("DT", ""),
                "galaxy": gal_name,
                "galaxy_num": gal_num,
                "portal_hex": fmt4(compact),
                "portal_sort_key": portal_sort_key(compact),
                "glyphs": list(compact),
                "custom_name": dm.get("CN", ""),
                "discoverer": ows.get("USN", ""),
            }
        )

    stats = {
        "total_bases": len(bases),
        "favourites": sum(1 for b in bases if b["favourite"]),
        "galaxies": len(galaxy_summary),
        "discoveries": len(discoveries),
    }

    return stats, galaxy_summary, bases, discoveries


@app.route("/")
def index():
    save_path = request.args.get("save", str(DEFAULT_SAVE))
    stats, galaxy_summary, bases, discoveries = load_data(save_path)
    return render_template(
        "index.html",
        stats=stats,
        galaxy_summary=galaxy_summary,
        bases=bases,
        discoveries=discoveries,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
