"""Hover tooltips for tkintermapview canvas markers."""

import tkinter

import gis_graphical_editor.gpx_utility

_DEFAULT_WAYPOINT_HOVER_PIXEL_THRESHOLD = 16


class MapMarkerTooltip:
  """Floating label shown while the pointer rests over a map marker."""

  def __init__(self, master):
    """Create a hidden tooltip window bound to master for lifetime."""

    self._master = master
    self._tooltip_window = None
    self._tooltip_label = None

  def show(self, tooltip_text, screen_x, screen_y):
    """Display tooltip_text near the given screen coordinates."""

    if tooltip_text == "":
      return

    if self._tooltip_window is None:
      self._tooltip_window = tkinter.Toplevel(self._master)
      self._tooltip_window.wm_overrideredirect(True)
      self._tooltip_label = tkinter.Label(
        self._tooltip_window,
        text=tooltip_text,
        background="#ffffe0",
        relief=tkinter.SOLID,
        borderwidth=1,
        padx=4,
        pady=2,
      )
      self._tooltip_label.pack()

    self._tooltip_label.config(text=tooltip_text)
    offset_x = 12
    offset_y = 12
    self._tooltip_window.wm_geometry(
      "+{screen_x}+{screen_y}".format(
        screen_x=screen_x + offset_x,
        screen_y=screen_y + offset_y,
      ),
    )
    self._tooltip_window.deiconify()

  def hide(self):
    """Hide the tooltip window when the pointer leaves the marker."""

    if self._tooltip_window is not None:
      self._tooltip_window.withdraw()


class MapWaypointHoverTooltipManager:
  """Show waypoint name tooltips from canvas motion near star markers."""

  def __init__(self, root, map_widget, pixel_threshold=_DEFAULT_WAYPOINT_HOVER_PIXEL_THRESHOLD):
    """Store map widget bindings and the shared floating tooltip window."""

    self._root = root
    self._map_widget = map_widget
    self._pixel_threshold = pixel_threshold
    self._waypoint_marker_entries = []
    self._tooltip = MapMarkerTooltip(root)
    self._hovered_gpx_waypoint_record = None
    self._installed = False

  def install_on_map_widget(self, map_widget):
    """Bind canvas motion events once so hover survives marker redraws."""

    if self._installed:
      return

    self._installed = True
    map_canvas = map_widget.canvas
    map_canvas.bind("<Motion>", self._handle_map_canvas_motion, add="+")
    map_canvas.bind("<Leave>", self._handle_map_canvas_leave, add="+")

  def set_waypoint_marker_entries(self, waypoint_marker_entries):
    """Replace the waypoint markers consulted on each canvas motion event."""

    self._waypoint_marker_entries = list(waypoint_marker_entries)

    if not self._waypoint_marker_entries:
      self._tooltip.hide()
      self._hovered_gpx_waypoint_record = None

  def clear(self):
    """Forget waypoint markers and hide any visible tooltip."""

    self.set_waypoint_marker_entries([])

  def _handle_map_canvas_motion(self, event):
    """Show or hide the tooltip for the nearest waypoint under the pointer."""

    gpx_waypoint_record = find_gpx_waypoint_at_canvas_position(
      self._waypoint_marker_entries,
      event.x,
      event.y,
      self._pixel_threshold,
    )

    if gpx_waypoint_record is None:
      if self._hovered_gpx_waypoint_record is not None:
        self._tooltip.hide()
        self._hovered_gpx_waypoint_record = None

      return

    tooltip_text = \
      gis_graphical_editor.gpx_utility.build_gpx_waypoint_tooltip_text(gpx_waypoint_record)

    if tooltip_text == "":
      if self._hovered_gpx_waypoint_record is not None:
        self._tooltip.hide()
        self._hovered_gpx_waypoint_record = None

      return

    self._hovered_gpx_waypoint_record = gpx_waypoint_record
    self._tooltip.show(tooltip_text, event.x_root, event.y_root)

  def _handle_map_canvas_leave(self, event):
    """Hide the tooltip when the pointer leaves the map canvas."""

    self._tooltip.hide()
    self._hovered_gpx_waypoint_record = None


def find_gpx_waypoint_at_canvas_position(
  waypoint_marker_entries,
  canvas_x,
  canvas_y,
  pixel_threshold,
):
  """Return the nearest GPX waypoint record within pixel_threshold, if any."""

  closest_waypoint_record = None
  closest_distance_squared = pixel_threshold * pixel_threshold

  for map_marker, gpx_waypoint_record in waypoint_marker_entries:
    marker_canvas_x, marker_canvas_y = map_marker.get_canvas_pos(map_marker.position)
    delta_x = marker_canvas_x - canvas_x
    delta_y = marker_canvas_y - canvas_y
    distance_squared = delta_x * delta_x + delta_y * delta_y

    if distance_squared <= closest_distance_squared:
      closest_distance_squared = distance_squared
      closest_waypoint_record = gpx_waypoint_record

  return closest_waypoint_record
