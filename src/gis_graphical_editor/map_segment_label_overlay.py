"""Rotated trkseg name labels drawn on the tkintermapview canvas."""

import math

import tkintermapview.utility_functions


class MapSegmentLabelOverlayManager:
  """Draw and refresh segment labels parallel to each segment's local direction."""

  def __init__(self, root, text_color="#003366"):
    """Store root for idle scheduling and the label text color."""

    self._root = root
    self._map_widget = None
    self._segment_label_placements = []
    self._canvas_text_item_ids = []
    self._text_color = text_color
    self._outline_color = "#FFFFFF"
    self._font = ("Tahoma", 12, "bold")
    self._outline_offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
    self._redraw_scheduled = False

  def install_on_map_widget(self, map_widget):
    """Bind map pan and zoom events so labels stay aligned with the track."""

    self._map_widget = map_widget
    map_canvas = map_widget.canvas
    map_canvas.bind("<B1-Motion>", self._handle_map_canvas_changed, add="+")
    map_canvas.bind("<ButtonRelease-1>", self._handle_map_canvas_changed, add="+")
    map_canvas.bind("<MouseWheel>", self._handle_map_canvas_changed, add="+")
    map_canvas.bind("<Button-4>", self._handle_map_canvas_changed, add="+")
    map_canvas.bind("<Button-5>", self._handle_map_canvas_changed, add="+")
    map_canvas.bind("<Configure>", self._handle_map_canvas_changed, add="+")
    self._install_map_widget_redraw_hooks(map_widget)

  def set_segment_label_placements(self, segment_label_placements):
    """Replace the segment labels that should appear on the next draw."""

    self._segment_label_placements = list(segment_label_placements)

  def clear(self):
    """Remove every segment label canvas item and forget placements."""

    self.clear_canvas_text()
    self._segment_label_placements = []

  def clear_canvas_text(self):
    """Remove segment label canvas items but keep placements for the next redraw."""

    self._delete_canvas_text_items()

  def draw_all(self):
    """Redraw every segment label at the current map zoom and pan."""

    if self._map_widget is None:
      return

    self._delete_canvas_text_items()

    # Project each placement onto the canvas with a screen-parallel text angle.
    for segment_label_placement in self._segment_label_placements:
      self._draw_segment_label_placement(segment_label_placement)

    if self._canvas_text_item_ids:
      map_canvas = self._map_widget.canvas
      self._raise_segment_labels_above_map_overlays(map_canvas)

  def _raise_segment_labels_above_map_overlays(self, map_canvas):
    """Keep segment labels above paths and markers after tkintermapview z-order updates."""

    if not map_canvas.find_withtag("segment_label"):
      return

    if map_canvas.find_withtag("path"):
      map_canvas.tag_raise("segment_label", "path")
    else:
      map_canvas.tag_raise("segment_label")

    if map_canvas.find_withtag("marker"):
      map_canvas.tag_raise("segment_label", "marker")

    for canvas_text_item_id in map_canvas.find_withtag("segment_label"):
      map_canvas.lift(canvas_text_item_id)

  def _install_map_widget_redraw_hooks(self, map_widget):
    """Redraw labels after tkintermapview programmatic pan and zoom updates."""

    if getattr(map_widget, "_gge_segment_label_overlay_redraw_hooks_installed", False):
      return

    map_widget._gge_segment_label_overlay_redraw_hooks_installed = True
    overlay_manager = self
    original_draw_initial_array = map_widget.draw_initial_array
    original_draw_move = map_widget.draw_move

    def draw_initial_array_with_segment_labels():
      original_draw_initial_array()
      overlay_manager.draw_all()

    def draw_move_with_segment_labels(called_after_zoom=False):
      original_draw_move(called_after_zoom)
      # Redraw immediately so labels track tiles during continuous map drags.
      overlay_manager.draw_all()

    map_widget.draw_initial_array = draw_initial_array_with_segment_labels
    map_widget.draw_move = draw_move_with_segment_labels
    self._install_map_widget_z_order_hook(map_widget)

  def _install_map_widget_z_order_hook(self, map_widget):
    """Raise segment labels after every tkintermapview overlay z-order pass."""

    if getattr(map_widget, "_gge_segment_label_overlay_z_order_hook_installed", False):
      return

    map_widget._gge_segment_label_overlay_z_order_hook_installed = True
    overlay_manager = self
    original_manage_z_order = map_widget.manage_z_order

    def manage_z_order_with_segment_labels():
      original_manage_z_order()
      overlay_manager._raise_segment_labels_above_map_overlays(map_widget.canvas)

    map_widget.manage_z_order = manage_z_order_with_segment_labels

  def _handle_map_canvas_changed(self, event=None):
    """Schedule a label redraw after map pan or zoom input."""

    self._schedule_draw_all()

  def schedule_draw_all(self):
    """Coalesce rapid map events into one idle redraw."""

    self._schedule_draw_all()

  def _schedule_draw_all(self, event=None):
    """Coalesce rapid map events into one idle redraw."""

    if self._redraw_scheduled:
      return

    self._redraw_scheduled = True
    self._root.after_idle(self._run_scheduled_draw_all)

  def _run_scheduled_draw_all(self):
    """Redraw labels once Tk has finished processing the current map event."""

    self._redraw_scheduled = False
    self.draw_all()

  def _draw_segment_label_placement(self, segment_label_placement):
    """Create one rotated canvas text item for a segment label placement."""

    first_canvas_x, first_canvas_y = self._get_canvas_position(
      segment_label_placement.first_latitude,
      segment_label_placement.first_longitude,
    )
    second_canvas_x, second_canvas_y = self._get_canvas_position(
      segment_label_placement.second_latitude,
      segment_label_placement.second_longitude,
    )
    center_canvas_x = (first_canvas_x + second_canvas_x) / 2.0
    center_canvas_y = (first_canvas_y + second_canvas_y) / 2.0
    label_angle_degrees = self._compute_readable_canvas_angle_degrees(
      first_canvas_x,
      first_canvas_y,
      second_canvas_x,
      second_canvas_y,
    )

    for outline_offset_x, outline_offset_y in self._outline_offsets:
      outline_canvas_text_item_id = self._map_widget.canvas.create_text(
        center_canvas_x + outline_offset_x,
        center_canvas_y + outline_offset_y,
        text=segment_label_placement.label,
        fill=self._outline_color,
        font=self._font,
        angle=label_angle_degrees,
        tags=("segment_label",),
      )
      self._canvas_text_item_ids.append(outline_canvas_text_item_id)

    canvas_text_item_id = self._map_widget.canvas.create_text(
      center_canvas_x,
      center_canvas_y,
      text=segment_label_placement.label,
      fill=self._text_color,
      font=self._font,
      angle=label_angle_degrees,
      tags=("segment_label",),
    )
    self._canvas_text_item_ids.append(canvas_text_item_id)

  def _get_canvas_position(self, latitude, longitude):
    """Return canvas pixel coordinates for one latitude and longitude."""

    tile_position = tkintermapview.utility_functions.decimal_to_osm(
      latitude,
      longitude,
      round(self._map_widget.zoom),
    )
    widget_tile_width = \
      self._map_widget.lower_right_tile_pos[0] - self._map_widget.upper_left_tile_pos[0]
    widget_tile_height = \
      self._map_widget.lower_right_tile_pos[1] - self._map_widget.upper_left_tile_pos[1]
    canvas_x = \
      ((tile_position[0] - self._map_widget.upper_left_tile_pos[0]) / widget_tile_width) \
      * self._map_widget.width
    canvas_y = \
      ((tile_position[1] - self._map_widget.upper_left_tile_pos[1]) / widget_tile_height) \
      * self._map_widget.height

    return canvas_x, canvas_y

  def _compute_readable_canvas_angle_degrees(
    self,
    first_canvas_x,
    first_canvas_y,
    second_canvas_x,
    second_canvas_y,
  ):
    """Return a screen angle that keeps label text upright and parallel to the segment."""

    delta_x = second_canvas_x - first_canvas_x
    delta_y = second_canvas_y - first_canvas_y
    angle_degrees = math.degrees(math.atan2(delta_y, delta_x))

    if angle_degrees > 90:
      angle_degrees = angle_degrees - 180
    elif angle_degrees < -90:
      angle_degrees = angle_degrees + 180

    return angle_degrees

  def _delete_canvas_text_items(self):
    """Delete previously drawn segment label canvas items."""

    if self._map_widget is None:
      self._canvas_text_item_ids = []

      return

    for canvas_text_item_id in self._canvas_text_item_ids:
      self._map_widget.canvas.delete(canvas_text_item_id)

    self._canvas_text_item_ids = []
