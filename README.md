# NMS Bases Viewer

An interactive browser-based viewer for No Man's Sky save data. Displays your bases and visited systems with real NMS portal glyphs, sortable columns, and text filtering.

This work was inspired by the work of ebaleytherogue's python base script.. I was going to make that display a simple web page and well....

## Requirements

- Install [uv](https://docs.astral.sh/uv/)

## Setup

**First time only** — update uv, create the virtual environment, and install dependencies from the lockfile:

```powershell
uv self update && uv venv --python 3.14 && uv sync --frozen
```

## Running the app

```powershell
uv run app.py
```

Then open your browser to **http://localhost:5000**

The app reads `save.hg.json` from the same directory by default. To load a different save file, pass it as a query parameter:

```
http://localhost:5000/?save=C:\path\to\your\save.hg.json
```

## Finding your NMS save file

NMS save files are typically located at:

```
%APPDATA%\HelloGames\NMS\<SteamID>\save.hg
```

The file has no `.json` extension by default. Either rename a copy to `save.hg.json` and place it in this directory, or use the `?save=` URL parameter to point to any `.hg.json` file you have prepared.

## Features

### Summary tab
- Count of bases per galaxy with galaxy name and human-readable galaxy number (e.g. `Euclid/1`, `Eissentam/10`)
- Glyph legend showing all 16 NMS portal symbols with their names

### Bases tab
- All player bases with galaxy, base name (starred if a favourite), portal address, and rendered glyphs
- Text filter — searches across name, portal address, and galaxy
- Click any column header to sort; click again to reverse

### Visited Systems tab
- Up to 512 visited systems decoded from the save file's `VisitedSystems` buffer
- Columns: galaxy, system index, region (X/Y/Z voxel coordinates), portal address, glyphs
- Systems that contain one of your bases are marked with a **Base** badge; hover it to see the base name(s)
- Note: `VisitedSystems` is a rolling buffer for the current galaxy only, so all entries will show the galaxy you are currently in

## Portal address format

Addresses are displayed as three groups of 4 hex digits (`PSSS YYZZ ZXXX`):

| Segment | Digits | Meaning |
|---------|--------|---------|
| P       | 1      | Planet index |
| SSS     | 3      | System index |
| YY      | 2      | Voxel Y coordinate |
| ZZZ     | 3      | Voxel Z coordinate |
| XXX     | 3      | Voxel X coordinate |

Sorting by the Portal Address column sorts by **system index first**, then planet, then voxel coordinates — the display order is unchanged so you can still copy the address directly into a portal decoder.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask server — loads save data, single route |
| `extract_nms_bases_v8.py` | Data engine — parses `.hg.json`, decodes portal addresses |
| `templates/index.html` | Single-page UI (tabs, filtering, sorting, glyph rendering) |
| `static/glyphs/glyph_0.png` … `glyph_F.png` | NMS portal glyph images |
| `save.hg.json` | Your NMS save file (not included — add your own) |
| `nms_base_reports/` | Legacy CSV reports produced by the original script |
