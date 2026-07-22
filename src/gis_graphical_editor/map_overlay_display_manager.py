"""Green overlay markers and paths drawn on the tkintermapview map."""

_OVERLAY_PATH_COLOR = "#00AA00"
_OVERLAY_PATH_WIDTH = 9


class MapOverlayDisplayManager:
  """Draw captured overlay locations as green dots connected by green segments."""

  def __init__(self, map_widget, green_point_icon):
    """Store the map widget and icon used for every overlay location marker."""

    self._map_widget = map_widget
    self._green_point_icon = green_point_icon
    self._canvas_paths = []
    self._canvas_markers = []

  def clear_display(self):
    """Remove every overlay marker and path from the map widget."""

    for canvas_path in self._canvas_paths:
      canvas_path.delete()

    for canvas_marker in self._canvas_markers:
      canvas_marker.delete()

    self._canvas_paths = []
    self._canvas_markers = []

  def draw_overlays(self, pushed_overlays, pending_location_records):
    """Redraw every pushed overlay plus the current pending capture session."""

    self.clear_display()

    # Draw each completed overlay, then the in-progress capture list.
    for captured_overlay in pushed_overlays:
      self._draw_location_records(captured_overlay.location_records)

    self._draw_location_records(pending_location_records)

  def _draw_location_records(self, location_records):
    """Place green markers and optional connecting path for one location list."""

    if not location_records:
      return

    for location_record in location_records:
      canvas_marker = self._map_widget.set_marker(
        location_record.latitude,
        location_record.longitude,
        icon=self._green_point_icon,
        icon_anchor="center",
      )
      self._canvas_markers.append(canvas_marker)

    if len(location_records) >= 2:
      path_points = []

      for location_record in location_records:
        path_points.append((location_record.latitude, location_record.longitude))

      canvas_path = self._map_widget.set_path(
        path_points,
        color=_OVERLAY_PATH_COLOR,
        width=_OVERLAY_PATH_WIDTH,
      )
      self._canvas_paths.append(canvas_path)
