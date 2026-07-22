"""Tests for map ctrl+click zoom-out handling."""

import tkinter

import gis_graphical_editor.main_window


class FakeMapWidget:
  """Minimal map stand-in for zoom handler tests without tile network I/O."""

  def __init__(self, starting_zoom=12):
    self.zoom = starting_zoom
    self.width = 800
    self.height = 600

  def set_zoom(self, zoom, relative_pointer_x=0.5, relative_pointer_y=0.5):
    self.zoom = zoom


def test_is_control_modifier_active_when_either_control_key_is_tracked():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  map_event = type("MapEvent", (), {"state": 0})()

  main_window._pressed_control_key_names.add("Control_L")
  assert main_window._is_control_modifier_active_for_map_event(map_event)

  main_window._pressed_control_key_names.clear()
  main_window._pressed_control_key_names.add("Control_R")
  assert main_window._is_control_modifier_active_for_map_event(map_event)

  root.destroy()


def test_is_control_modifier_active_when_pointer_motion_saw_control_state():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  motion_event = type("MotionEvent", (), {"state": gis_graphical_editor.main_window._MAP_CONTROL_CLICK_STATE_MASK})()
  click_event = type("ClickEvent", (), {"state": 0})()
  main_window._handle_map_pointer_motion(motion_event)

  assert main_window._is_control_modifier_active_for_map_event(click_event)

  root.destroy()


def test_handle_map_canvas_button_one_zooms_out_when_control_is_held():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  map_widget = FakeMapWidget(starting_zoom=12)
  main_window._map_widget = map_widget
  click_calls = []

  def record_click(event):
    click_calls.append(event)

  main_window._original_map_mouse_click = record_click
  main_window._pressed_control_key_names.add("Control_R")
  button_one_event = type(
    "ButtonOneEvent",
    (),
    {"num": 1, "x": 200, "y": 150, "state": 0},
  )()
  main_window._handle_map_canvas_button_one(button_one_event)
  root.destroy()

  assert map_widget.zoom == 11
  assert click_calls == []


def test_handle_map_canvas_zoom_button_zooms_out_when_control_is_held():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  map_widget = FakeMapWidget(starting_zoom=12)
  main_window._map_widget = map_widget
  main_window._original_map_mouse_zoom = lambda event: setattr(
    map_widget,
    "zoom",
    map_widget.zoom + 1,
  )
  main_window._pressed_control_key_names.add("Control_L")
  button_four_event = type(
    "ButtonFourEvent",
    (),
    {"num": 4, "x": 200, "y": 150, "state": 0},
  )()
  main_window._handle_map_canvas_zoom_button(button_four_event)
  root.destroy()

  assert map_widget.zoom == 11


def test_handle_map_canvas_zoom_button_zooms_in_without_control():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  map_widget = FakeMapWidget(starting_zoom=12)
  main_window._map_widget = map_widget
  main_window._original_map_mouse_zoom = lambda event: setattr(
    map_widget,
    "zoom",
    map_widget.zoom + 1,
  )
  button_four_event = type(
    "ButtonFourEvent",
    (),
    {"num": 4, "x": 200, "y": 150, "state": 0},
  )()
  main_window._handle_map_canvas_zoom_button(button_four_event)
  root.destroy()

  assert map_widget.zoom == 13
