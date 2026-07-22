"""Tests for top-left overlay mode button placement on the map widget."""

import tkinter

import gis_graphical_editor.map_overlay_mode_panel
import tkintermapview


class FakeCanvasButton:
  """Stand-in for tkintermapview.CanvasButton with fixed geometry."""

  def __init__(self, canvas_position, height):
    self.canvas_position = canvas_position
    self.height = height


class FakeMapWidget:
  """Minimal map stand-in exposing zoom button geometry for layout tests."""

  def __init__(self):
    self.button_zoom_in = FakeCanvasButton((20, 20), 29)
    self.button_zoom_out = FakeCanvasButton((20, 60), 29)


def test_compute_map_top_left_button_stack_gap_pixels_matches_zoom_button_spacing():
  map_widget = FakeMapWidget()

  stack_gap_pixels = \
    gis_graphical_editor.map_overlay_mode_panel.compute_map_top_left_button_stack_gap_pixels(
      map_widget)

  assert stack_gap_pixels == 11


def test_compute_first_overlay_button_y_uses_same_gap_as_zoom_buttons():
  map_widget = FakeMapWidget()

  first_overlay_button_y = \
    gis_graphical_editor.map_overlay_mode_panel.compute_first_overlay_button_y(
      map_widget)

  zoom_out_bottom = (
    map_widget.button_zoom_out.canvas_position[1]
    + map_widget.button_zoom_out.height
  )
  stack_gap_pixels = \
    gis_graphical_editor.map_overlay_mode_panel.compute_map_top_left_button_stack_gap_pixels(
      map_widget)

  assert first_overlay_button_y == zoom_out_bottom + stack_gap_pixels


def test_map_overlay_mode_panel_stack_step_uses_zoom_button_gap():
  root = tkinter.Tk()
  root.withdraw()
  map_widget = tkintermapview.TkinterMapView(root, width=400, height=300)
  map_widget.pack()
  root.update_idletasks()
  overlay_mode_panel = gis_graphical_editor.map_overlay_mode_panel.MapOverlayModePanel(
    map_widget,
    lambda: None,
    lambda: None,
    lambda: None)
  root.update_idletasks()

  toggle_button_height = overlay_mode_panel._toggle_overlay_mode_button.winfo_reqheight()
  stack_gap_pixels = \
    gis_graphical_editor.map_overlay_mode_panel.compute_map_top_left_button_stack_gap_pixels(
      map_widget)

  assert overlay_mode_panel._overlay_button_stack_step_pixels == \
    toggle_button_height + stack_gap_pixels

  root.destroy()
