
# Last modified on: 23-May-2026 08:03:24

# NMS Bases Viewer
An interactive browser-based viewer for No Man's Sky save data. Displays your bases and visited systems with real NMS portal glyphs, sortable columns, and text filtering.

This work was inspired by the work of ebaleytherogue's python base script.. I was going to make that display a simple web page and well....

## Requirements

- Install [uv](https://docs.astral.sh/uv/)
- use GoatFungus or another NMS editor to save your game files as a JSON file (in GF its menu Edit->export JSON). You will want to be doing this regularly, so choose a name which includes the date so you arent overwriting them. eg "2026-05-21.json"

## Setup

**First time only** — update uv, create the virtual environment, and install dependencies from the lockfile:

```powershell
uv self update && uv venv --python 3.14 && uv sync --frozen
```

## Running the app

```powershell
uv run nms_viewer.py
```

Then open your browser to **http://localhost:5000**  (Note that the app may choose another port if you already have 5000 in use. Open the URL its showing. 127.0.0.1 is the same as localhost)

The app reads json files from its imports directory. It will load all the json files in imports into the current session. 

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
- Up to 512 visited systems decoded from the save file's `VisitedSystems` buffer. If you export a JSON file each week it will have all the 
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

## Items with no names
- Only if you explicitly name an item does it have a name in the json file. We arent able to duplicate the procedurally generated names..
- *However* if you click on 'rename' an item and just click 'accept', without changing the name, its still marked as explicitly named by you and will be in the json file.
- If you go into the game discoveries -> Visited Systems tab you can rename all the systems you have discovered (click X, then accept)
- For items that you didnt find the names will be blank since the game gets them from the servers. A future option will allow you to type in the names and have them saved in a local database.

## Files

| File | Purpose |
|------|---------|
| `nms_viewer.py` | Flask server — loads save data, single route |
| `templates/index.html` | Single-page UI (tabs, filtering, sorting, glyph rendering) |
| `static/glyphs/glyph_0.png` … `glyph_F.png` | NMS portal glyph images |
| `save.hg.json` | Your NMS save file (not included — add your own) |


# To be added:
- keep a local sqlite db so as discoveries, etc roll out of the save file we preserve them; so we can get back to them via the glpyhs

