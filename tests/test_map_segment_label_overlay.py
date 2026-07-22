"""Tests for map_segment_label_overlay angle helpers and map redraw hooks."""

import tkinter

import gis_graphical_editor.map_segment_label_overlay
import gis_graphical_editor.track_analysis


def test_compute_readable_canvas_angle_degrees_keeps_text_upright():
  overlay_manager = gis_graphical_editor.map_segment_label_overlay.MapSegmentLabelOverlayManager(
    root=None,
  )

  angle_degrees = overlay_manager._compute_readable_canvas_angle_degrees(0.0, 0.0, 10.0, 0.0)

  assert angle_degrees == 0.0


def test_compute_readable_canvas_angle_degrees_flips_downward_lines():
  overlay_manager = gis_graphical_editor.map_segment_label_overlay.MapSegmentLabelOverlayManager(
    root=None,
  )

  angle_degrees = overlay_manager._compute_readable_canvas_angle_degrees(0.0, 0.0, -10.0, 0.0)

  assert angle_degrees == 0.0


def test_install_on_map_widget_redraws_labels_after_draw_initial_array():
  root = tkinter.Tk()
  root.withdraw()
  overlay_manager = gis_graphical_editor.map_segment_label_overlay.MapSegmentLabelOverlayManager(
    root,
  )
  draw_all_call_count = 0
  original_draw_all = overlay_manager.draw_all

  def draw_all_spy():
    nonlocal draw_all_call_count
    draw_all_call_count += 1

  overlay_manager.draw_all = draw_all_spy
  draw_initial_array_call_count = 0

  class FakeMapWidget:
    def __init__(self):
      self.canvas = tkinter.Canvas(root, width=400, height=300)
      self._gge_segment_label_overlay_redraw_hooks_installed = False
      self._gge_segment_label_overlay_z_order_hook_installed = False

    def draw_initial_array(self):
      nonlocal draw_initial_array_call_count
      draw_initial_array_call_count += 1

    def draw_move(self, called_after_zoom=False):
      pass

    def manage_z_order(self):
      pass

  map_widget = FakeMapWidget()
  overlay_manager.install_on_map_widget(map_widget)
  map_widget.draw_initial_array()
  root.update_idletasks()
  root.update()
  overlay_manager.draw_all = original_draw_all
  root.destroy()

  assert draw_initial_array_call_count == 1
  assert draw_all_call_count == 1


def test_manage_z_order_hook_keeps_segment_labels_above_path():
  root = tkinter.Tk()
  root.withdraw()
  overlay_manager = gis_graphical_editor.map_segment_label_overlay.MapSegmentLabelOverlayManager(
    root,
  )

  class FakeMapWidget:
    zoom = 15
    width = 400
    height = 300
    upper_left_tile_pos = (0.0, 0.0)
    lower_right_tile_pos = (1.0, 1.0)

    def __init__(self):
      self.canvas = tkinter.Canvas(root, width=400, height=300)
      self._gge_segment_label_overlay_redraw_hooks_installed = False
      self._gge_segment_label_overlay_z_order_hook_installed = False

    def draw_initial_array(self):
      pass

    def draw_move(self, called_after_zoom=False):
      pass

    def manage_z_order(self):
      self.canvas.lift("path")

  map_widget = FakeMapWidget()
  overlay_manager.install_on_map_widget(map_widget)
  map_widget.canvas.create_line(0, 0, 100, 100, tags=("path",), width=8)
  segment_label_placement = gis_graphical_editor.track_analysis.SegmentLabelPlacement(
    label="Lake Nona",
    first_latitude=28.4,
    first_longitude=-81.2,
    second_latitude=28.41,
    second_longitude=-81.19,
  )
  overlay_manager.set_segment_label_placements([segment_label_placement])
  overlay_manager.draw_all()
  label_canvas_item_id = overlay_manager._canvas_text_item_ids[-1]
  map_widget.manage_z_order()
  root.update()

  assert map_widget.canvas.find_above(label_canvas_item_id) == ()

  root.destroy()
