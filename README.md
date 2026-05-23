# NMS Viewer

An interactive browser-based viewer for No Man's Sky save data. Displays your bases and discoveries (planets, sectors, solar systems, flora, fauna, minerals) with real NMS portal glyphs, sortable columns, and text filtering.

Inspired by ebaleytherogue's Python base script.

## Requirements

- Install [uv](https://docs.astral.sh/uv/)
- Use GoatFungus or another NMS save editor to export your save as JSON (in GoatFungus: **Edit → Export JSON**)

## Setup

**First time only** — update uv, create the virtual environment, and install dependencies:

```powershell
uv self update && uv venv --python 3.14 && uv sync --frozen
```

## Adding save files

Place exported JSON files in the `imports/` directory. Name them with a `YYYY-MM-DD` date prefix so they load in chronological order:

```
imports/2026-05-16.json
imports/2026-05-22.json
```

Files without a date prefix are sorted by their modification time on disk and loaded after any dated files that predate them.

All files in `imports/` are merged on each load. Duplicate records across files are deduplicated — if the same discovery appears in multiple exports, the version with the most data (name, discoverer) is kept.

## Running the app

```powershell
uv run nms_viewer.py
```

Then open **http://localhost:5000** in your browser. (If port 5000 is in use the app will pick another — check the terminal output.)

On startup the console prints a summary for each file loaded, followed by overall totals:

```
--- 2026-05-16.json ---
  Bases: 12  Planets: 97  Sectors: 18  Solar Systems: 45
  NEW Planet: Ayphos Sigma | 1024 AB23 456C | Euclid | JimMcHale

--- 2026-05-22.json ---
  Bases: 14  Planets: 102  Sectors: 19  Solar Systems: 47
  UPDATED SolarSystem: 1024 AB23 456C  name: '' -> 'New Lennox'  discoverer: '' -> 'JimMcHale'

=== TOTALS ===
  Bases: 14  Planets: 102  Sectors: 19  Solar Systems: 47
  Named systems: 12  Unnamed systems: 35
```

## Features

### Summary tab
- Count of bases per galaxy with galaxy name and human-readable galaxy number 
- Glyph legend showing all 16 NMS portal symbols with their names

### Bases tab
- All player bases with galaxy, base name (starred if a favourite), portal address, and rendered glyphs
- Text filter — searches across name, portal address, and galaxy
- Click any column header to sort; click again to reverse

### Discoveries tab
- All discoveries decoded from `DiscoveryManagerData` in the save file
- Types: Planet, Sector, SolarSystem, Animal, Flora, Mineral
- Defaults to showing **Planets only** — use the type checkboxes to add or remove types
- Text filter searches across name, discoverer, galaxy, and portal address
- **Name column**: a name only appears here if you have explicitly saved it in-game. To save a name without changing it, open the discovery, click **Rename**, and accept. NMS only writes the name to the save once you confirm it.

## Portal address format

Addresses are displayed as three groups of 4 hex digits (`PSSS YYZZ ZXXX`):

| Segment | Digits | Meaning |
|---------|--------|---------|
| P       | 1      | Planet index |
| SSS     | 3      | System index |
| YY      | 2      | Voxel Y coordinate |
| ZZZ     | 3      | Voxel Z coordinate |
| XXX     | 3      | Voxel X coordinate |

Sorting by Portal Address sorts by **system index first**, then planet, then voxel coordinates — the display order is unchanged so you can copy the address directly into a portal decoder.

## Getting discovery names into the save

NMS does not store procedurally generated names — it fetches them from its servers at runtime. The only names that appear in the save (and therefore here) are ones you have explicitly confirmed in-game:

- Go to **Discoveries → Visited Systems**
- Click on a system, hit **Rename**, and accept (no need to change anything)
- That name is now written to your save and will appear here after the next export

## Files

| File | Purpose |
|------|---------|
| `nms_viewer.py` | Flask server — loads and merges all imports, single route |
| `extract_nms_bases_v8.py` | Save file parser (bases, portal decoding, galaxy names) |
| `templates/index.html` | Single-page UI (tabs, filtering, sorting, glyph rendering) |
| `static/glyphs/glyph_0.png` … `glyph_F.png` | NMS portal glyph images |
| `imports/` | Drop your exported JSON save files here |

## To be added

- Local SQLite database to preserve discoveries as they roll out of the save file's fixed-size buffer, so portal addresses are never lost
