# GIS Graphical Editor

Desktop application for viewing GPX tracks on an interactive OpenStreetMap map. Load a GPX file, inspect the path, split or delete segments along the time slider, and optionally overlay recorded points or interval markers along time and distance.

![GIS Graphical Editor showing the Key West AutoLog GPX track on OpenStreetMap with the time slider, metadata panel, and segment list](asset/documentation/image/track-overview.png)

## Requirements

- Python 3.10 or newer
- Tkinter (included with most Python installations on Linux)

## Installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

This installs the `gge` console script and optional pytest dependencies.

## Quick start

Launch the application:

```bash
gge
```

Without a filepath argument, the **File → Load** dialog opens on startup. Choose a `.gpx` file to display the track.

Load a specific file immediately:

```bash
gge /path/to/track.gpx
```

Show every recorded point as a green dot:

```bash
gge /path/to/track.gpx --points
```

![Green dots at every recorded GPX point along the Key West track](asset/documentation/image/track-recorded-points.png)

Place orange markers every 2 hours and red markers every 10 miles:

```bash
gge /path/to/track.gpx --mark-hours 2 --mark-distance 10
```

![Orange hour markers and red distance markers with labels along the Key West track](asset/documentation/image/track-interval-markers.png)

All three overlay types together:

![Green point dots with orange hour markers and red distance markers on the same track](asset/documentation/image/track-combined-overlays.png)

## Command-line options

| Option | Description |
|--------|-------------|
| `PATH` (optional positional) | Load this GPX file on startup instead of prompting |
| `--ref-segment-name NAMESPACE.NODE.LABEL_ATTRIBUTE` | Label visible `<trkseg>` segments from extensions (e.g. `circuit.lap.label`) |
| `--points` | Draw a green dot at every recorded GPX point |
| `--mark-hours N` | Place an orange marker every *N* hours along the path (requires timestamps) |
| `--mark-distance N` | Place a red marker every *N* miles along the path |
| `--no-mark-labels` | Hide text labels on hour and distance interval markers |

`--mark-hours` and `--mark-distance` require positive integers. Run `gge --help` for full usage text.

## Using the map

![Time slider scrubbed to a mid-track point with the red position marker on the map](asset/documentation/image/track-time-slider-midpoint.png)

- **Pan and zoom** using the map widget controls (provided by [tkintermapview](https://github.com/TomSchimansky/TkinterMapView)).
- **Double-click** the map to zoom in centered on the pointer.
- On load, the view **fits the track bounding box** automatically.
- **Time slider** (when the GPX has timestamps): scrub or use **Reverse play** / **Forward play** and step buttons to animate along the path; a red marker shows the current position.

## Track segments

![Two segments after splitting the track at the slider position, with Split, Delete, and Undo controls](asset/documentation/image/track-segments-after-split.png)

- **Segment checklist** in the right sidebar toggles which segments are drawn on the map.
- **Split** divides the current segment at the slider’s nearest point; **Delete** removes the highlighted segment after confirmation.
- **Undo** restores the segment structure from before the last split or delete.
- **Save As** (Ctrl+Shift+S) exports all in-memory segments, including edits.

## File menu

| Action | Shortcut | Description |
|--------|----------|-------------|
| Load | Ctrl+O | Open a GPX file via file dialog |
| Save As | Ctrl+Shift+S | Export the current track (including segment edits) to a GPX file |
| Close | Ctrl+W | Remove the current map and track (disabled until a file is loaded) |
| Exit | Ctrl+Q | Quit the application |

## GPX support

The loader reads points in this order:

1. Track segment points (primary)
2. Route points (when no track segments exist)
3. Standalone waypoints (when tracks and routes are absent)

Coordinates are kept as decimal degrees. Timestamps are used for hour-based markers and distance-marker labels when present.

## Development

Run the test suite:

```bash
pytest -q
```

### Project layout

```
src/gis_graphical_editor/
  entrypoint/gge.py          CLI entry and argument parsing
  main_window.py             Tkinter shell, menus, map display
  gpx_utility.py             GPX parsing
  track_analysis.py          Hour/distance interval markers
  track_display_options.py   CLI-driven display settings
  map_icon_utility.py        Marker icon images
tests/                       Pytest modules mirroring src layout
```

## Feature reference

See [FEATURES.md](FEATURES.md) for a complete list of application capabilities.
