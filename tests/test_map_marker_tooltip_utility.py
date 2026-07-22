"""Tests for waypoint hover tooltip helpers."""

import tkinter

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.map_marker_tooltip_utility


class FakeWaypointMapMarker:
  """Minimal marker stub exposing get_canvas_pos for hover hit tests."""

  def __init__(self, canvas_x, canvas_y):
    """Store the canvas position returned by get_canvas_pos."""

    self.position = (0.0, 0.0)
    self._canvas_x = canvas_x
    self._canvas_y = canvas_y

  def get_canvas_pos(self, position):
    """Return the fixed canvas coordinates for this stub marker."""

    return self._canvas_x, self._canvas_y


def test_find_gpx_waypoint_at_canvas_position_returns_nearest_within_threshold():
  start_waypoint = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    None,
    additional_metadata={"name": "Start"},
  )
  finish_waypoint = gis_graphical_editor.gpx_utility.GpxPointRecord(
    41.0,
    -106.0,
    None,
    additional_metadata={"name": "Finish"},
  )
  waypoint_marker_entries = [
    (FakeWaypointMapMarker(100.0, 100.0), start_waypoint),
    (FakeWaypointMapMarker(200.0, 200.0), finish_waypoint),
  ]

  matched_waypoint = \
    gis_graphical_editor.map_marker_tooltip_utility.find_gpx_waypoint_at_canvas_position(
      waypoint_marker_entries,
      104.0,
      98.0,
      8,
    )

  assert matched_waypoint is start_waypoint


def test_find_gpx_waypoint_at_canvas_position_returns_none_outside_threshold():
  waypoint = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    None,
    additional_metadata={"name": "Start"},
  )
  waypoint_marker_entries = [
    (FakeWaypointMapMarker(100.0, 100.0), waypoint),
  ]

  matched_waypoint = \
    gis_graphical_editor.map_marker_tooltip_utility.find_gpx_waypoint_at_canvas_position(
      waypoint_marker_entries,
      130.0,
      100.0,
      8,
    )

  assert matched_waypoint is None


def test_map_waypoint_hover_tooltip_manager_shows_named_waypoint_tooltip():
  root = tkinter.Tk()
  root.withdraw()
  map_canvas = tkinter.Canvas(root, width=400, height=300)
  map_canvas.pack()
  waypoint = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    None,
    additional_metadata={"name": "Start: Key West"},
  )

  class FakeMapWidget:
    def __init__(self):
      self.canvas = map_canvas

  map_widget = FakeMapWidget()
  tooltip_manager = \
    gis_graphical_editor.map_marker_tooltip_utility.MapWaypointHoverTooltipManager(
      root,
      map_widget,
      pixel_threshold=16,
    )
  tooltip_manager.install_on_map_widget(map_widget)
  tooltip_manager.set_waypoint_marker_entries(
    [(FakeWaypointMapMarker(100.0, 100.0), waypoint)],
  )

  class MotionEvent:
    def __init__(self):
      self.x = 100
      self.y = 100
      self.x_root = 200
      self.y_root = 200

  tooltip_manager._handle_map_canvas_motion(MotionEvent())
  root.update()
  tooltip_window = tooltip_manager._tooltip._tooltip_window

  assert tooltip_window is not None
  assert tooltip_window.state() == "normal"
  assert tooltip_manager._tooltip._tooltip_label.cget("text") == "Start: Key West"

  tooltip_manager._handle_map_canvas_leave(MotionEvent())
  root.update()

  assert tooltip_window.state() == "withdrawn"

  root.destroy()
