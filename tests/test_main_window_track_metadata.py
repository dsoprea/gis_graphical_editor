"""Tests for main window track metadata panel lifecycle."""

import datetime
import tkinter

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.main_window
import gis_graphical_editor.right_sidebar_drawer
import gis_graphical_editor.track_metadata_panel


def test_resolve_gpx_points_for_timestamp_range_falls_back_to_loaded_points():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  loaded_gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    datetime.datetime(2024, 1, 1, 12, 0, 0),
  )
  main_window._loaded_gpx_points = [loaded_gpx_point]
  resolved_gpx_points = main_window._resolve_gpx_points_for_timestamp_range([])
  root.destroy()

  assert resolved_gpx_points is main_window._loaded_gpx_points


def test_refresh_track_display_keeps_metadata_placeholder_when_no_segments_visible():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)
  loaded_gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    timestamp,
  )
  main_window._loaded_gpx_points = [loaded_gpx_point]
  main_window._loaded_gpx_segments = [[loaded_gpx_point]]
  main_window._last_slider_timestamp = timestamp
  main_window._track_metadata_panel = \
    gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
      root,
      panel_width=400,
    )
  main_window._get_visible_gpx_points = lambda: []
  main_window._setup_time_slider_if_needed = lambda gpx_points: None
  main_window._refresh_track_display()
  placeholder_text = \
    main_window._track_metadata_panel._point_metadata_text.get("1.0", tkinter.END).strip()
  root.destroy()

  assert placeholder_text == \
    gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_PLACEHOLDER


def test_ensure_window_wide_enough_for_content_expands_narrow_root():
  root = tkinter.Tk()
  root.withdraw()
  root.geometry("700x600")
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  main_window._main_frame.grid_columnconfigure(0, minsize=500)
  main_window._right_sidebar_drawer = \
    gis_graphical_editor.right_sidebar_drawer.RightSidebarDrawer(main_window._main_frame)
  main_window._right_sidebar_drawer.set_content_width(450)
  main_window._right_sidebar_drawer.grid(row=0, column=1, sticky="ns")
  main_window._ensure_window_wide_enough_for_content()
  root.update_idletasks()
  expanded_window_width = root.winfo_width()
  root.destroy()

  assert expanded_window_width >= 950


def test_handle_slider_timestamp_changed_shows_metadata_placeholder_without_visible_points():
  root = tkinter.Tk()
  root.withdraw()
  main_window = gis_graphical_editor.main_window.MainWindow(root)
  selected_timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)
  main_window._map_widget = object()
  main_window._loaded_gpx_points = []
  main_window._track_metadata_panel = \
    gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
      root,
      panel_width=400,
    )
  main_window._track_metadata_panel.set_point_metadata(["latitude: 40.0"])
  main_window._segment_list_panel = None
  main_window._time_slider_panel = object()
  main_window._get_visible_gpx_points = lambda: []
  main_window._handle_slider_timestamp_changed(selected_timestamp)
  placeholder_text = \
    main_window._track_metadata_panel._point_metadata_text.get("1.0", tkinter.END).strip()
  root.destroy()

  assert placeholder_text == \
    gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_PLACEHOLDER
