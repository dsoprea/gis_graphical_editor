# Features

Complete catalog of GIS Graphical Editor (`gge`) capabilities.

## Application shell

- **Desktop GUI** built with Tkinter and [tkintermapview](https://github.com/TomSchimansky/TkinterMapView).
- **Default window** size 1024×768 with title "GIS Graphical Editor".
- **Console entry point** `gge` (package name `gge`, import path `gis_graphical_editor`).
- **Lazy map creation**: the map widget is created only after a GPX file is successfully loaded; closing the track destroys the widget.

## GPX loading

- **File dialog load** via **File → Load** (Ctrl+O) or startup prompt when no `--filepath` is given.
- **Startup load** via `--filepath PATH` without opening the dialog first.
- **Supported geometry sources** (first non-empty wins):
  - Track segment points, in file order across all tracks and segments.
  - Route points when the file has no track segments.
  - Standalone waypoints when tracks and routes are absent.
- **Point model** (`GpxPointRecord`): latitude, longitude, and optional timestamp per point.
- **Timestamp normalization**: timezone-aware GPX timestamps are converted to naive datetimes for analysis.
- **Error feedback**:
  - Error dialog when the path is not a file.
  - Error dialog when the GPX cannot be parsed.
  - Warning dialog when no track points are found.
  - Warning when `--mark-hours` is set but the loaded GPX has no timestamps (hour markers are skipped; the path still draws).

## GPX export

- **Save As** via **File → Save As** (Ctrl+Shift+S) writes the in-memory track to a user-chosen `.gpx` path.
- Exports **all** segments in `_loaded_gpx_segments`, preserving segment boundaries after split/delete edits.
- Segment checklist checkboxes affect map display only; unchecked segments remain in the exported file.
- Standard GPX point fields (elevation, speed, course, and similar metadata) round-trip through save and reload.
- Error dialog when the file cannot be written.
- Menu item disabled until a track with at least one point is loaded.

## Map display

- **Base map**: OpenStreetMap tiles through tkintermapview.
- **Track path**: blue polyline (`#0066CC`, width 9) through all loaded coordinates.
- **Auto framing**: after each load, the map fits a bounding box around the track (max/min latitude and longitude).
- **Double-click zoom**: double-clicking the map canvas increases zoom by one level, centered on the click position.
- **Close track**: **File → Close** (Ctrl+W) clears paths, markers, and removes the map widget. The menu item is disabled until a track is loaded.

## Recorded point overlay (`--points`)

- **Green dot** at every loaded GPX coordinate.
- Icons are slightly wider than the path line for visibility.
- Independent of timestamps (all points are drawn).

## Hour interval markers (`--mark-hours N`)

- **Orange dot** placed every *N* hours along the path (*N* must be a positive integer).
- **Requires timestamps** on GPX points; segments without both endpoint timestamps are skipped.
- **Position interpolation**: marker latitude/longitude are linearly interpolated along the segment that crosses each hour boundary.
- **Default labels** (unless `--no-mark-labels`): rounded total hours and rounded cumulative miles, e.g. `2 h, 15 mi`.
- **Distance along path** for labels uses haversine great-circle miles between consecutive points.

## Distance interval markers (`--mark-distance N`)

- **Red dot** placed every *N* miles along the path (*N* must be a positive integer).
- **Does not require timestamps** for placement (distance-only segments are used).
- **Position interpolation**: marker coordinates are linearly interpolated at each mile boundary along a segment.
- **Default labels** (unless `--no-mark-labels`): rounded total miles and interpolated timestamp when available, e.g. `10 mi, 2024-06-01 09:30:00`. Mile-only label when no timestamp can be interpolated.
- **Timestamp interpolation**: linear between segment endpoint timestamps when both exist; otherwise falls back to whichever endpoint has a time.

## Marker appearance

| Marker type | Color | Trigger |
|-------------|-------|---------|
| Recorded point | Green (`#00AA00`) | `--points` |
| Hour interval | Orange (`#FF8800`) | `--mark-hours N` |
| Distance interval | Red (`#CC0000`) | `--mark-distance N` |

- All marker icons are filled ellipses with outline, rendered via Pillow and sized to match path width.
- Interval marker text uses orange (`#CC5500`) or red (`#990000`) when labels are shown.

## Command-line interface

| Flag | Effect |
|------|--------|
| `--filepath PATH` | Load GPX on startup |
| `--points` | Show green dots at every point |
| `--mark-hours N` | Orange markers every *N* hours |
| `--mark-distance N` | Red markers every *N* miles |
| `--no-mark-labels` | Icons only; no text on interval markers |
| `--help` | Print usage and exit |

- **Validation**: non-positive `--mark-hours` or `--mark-distance` values produce an argparse error and non-zero exit.
- **Combinable options**: e.g. `--points --mark-hours 1 --mark-distance 5` on the same run.
- **Default label behavior**: interval marker labels are shown unless `--no-mark-labels` is passed.

## Menus and keyboard shortcuts

| Menu | Item | Shortcut | When available |
|------|------|----------|----------------|
| File | Load | Ctrl+O | Always |
| File | Save As | Ctrl+Shift+S | After a track with points is loaded |
| File | Close | Ctrl+W | After a track is loaded |
| File | Exit | Ctrl+Q | Always |

- Load opens a file dialog filtered to `*.gpx` with an "All files" option.
- Save As opens a save dialog filtered to `*.gpx` and writes the current in-memory segments.
- Exit calls `root.quit()` to end the main loop.

## Track analysis (library)

Reusable logic in `track_analysis.py`:

- `has_timestamps(gpx_points)` — whether any point carries a time.
- `compute_miles_between_points(first, second)` — haversine distance in miles (Earth radius 3958.8 mi).
- `compute_hours_between_timestamps(first, second)` — elapsed hours between datetimes.
- `build_hour_interval_markers(gpx_points, interval_hours)` — list of `TrackIntervalMarker`.
- `build_distance_interval_markers(gpx_points, interval_miles)` — list of `TrackIntervalMarker`.
- `interpolate_timestamp(first_point, second_point, fraction)` — time at a fractional position along a segment.
- Label formatters for hour and distance markers.

## GPX utilities (library)

- `load_gpx_points_from_gpx(path)` — ordered `GpxPointRecord` list.
- `load_track_points_from_gpx(path)` — ordered `(latitude, longitude)` tuples.
- `write_track_point_segments_to_gpx(path, segment_point_lists)` — write segment lists as one GPX track.

## Configuration object

`TrackDisplayOptions` holds display settings passed from the CLI to the main window:

- `mark_hours_interval`
- `mark_distance_interval`
- `show_points`
- `show_mark_labels`
- `initial_gpx_filepath`

## Dependencies

| Package | Role |
|---------|------|
| `gpxpy` | GPX parsing |
| `tkintermapview` | OSM map widget (pulls in Pillow, requests, etc.) |
| Pillow (transitive) | Marker icon rendering |
| `pytest` (optional) | Test runner |

## Automated tests

Pytest coverage includes:

- GPX track segment loading and export round-trips (`test_gpx_utility.py`)
- Hour and distance interval marker labels (`test_track_analysis.py`)
- Track display options (`test_track_display_options.py`)
- CLI validation for non-positive `--mark-hours` (`tests/entrypoint/test_gge.py`)

## Out of scope (current version)

- KMZ/KML import (only `.gpx` is supported).
- Multiple simultaneous tracks with separate styling.
- GUI controls for display options (options are CLI-only at launch).
