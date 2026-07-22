"""Tests for track metadata panel layout."""

import tkinter

import gis_graphical_editor.right_sidebar_drawer
import gis_graphical_editor.track_metadata_panel


def test_track_metadata_panel_exposes_only_current_location_section():
  root = tkinter.Tk()
  root.withdraw()
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
  )

  assert hasattr(track_metadata_panel, "_point_metadata_text")
  assert not hasattr(track_metadata_panel, "_segment_metadata_text")

  root.destroy()


def test_track_metadata_panel_shows_dark_gray_placeholder_when_no_location_is_selected():
  root = tkinter.Tk()
  root.withdraw()
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
  )
  point_metadata_text = track_metadata_panel._point_metadata_text
  placeholder_text = point_metadata_text.get("1.0", tkinter.END).strip()
  placeholder_tag_names = point_metadata_text.tag_names("1.0")

  assert placeholder_text == \
    gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_PLACEHOLDER
  assert gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_TEXT_TAG in placeholder_tag_names
  assert \
    point_metadata_text.tag_cget(
      gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_TEXT_TAG,
      "foreground",
    ) == gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_FOREGROUND

  track_metadata_panel.set_point_metadata(["latitude: 40.0", "longitude: -105.0"])
  metadata_text = point_metadata_text.get("1.0", tkinter.END).strip()

  assert "latitude: 40.0" in metadata_text
  assert gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_PLACEHOLDER not in metadata_text

  track_metadata_panel.clear()
  cleared_placeholder_text = point_metadata_text.get("1.0", tkinter.END).strip()

  assert cleared_placeholder_text == \
    gis_graphical_editor.track_metadata_panel._NO_LOCATION_SELECTED_PLACEHOLDER

  root.destroy()


def test_track_metadata_panel_mounts_collapse_handle_on_current_location_title_row():
  root = tkinter.Tk()
  root.withdraw()
  drawer = gis_graphical_editor.right_sidebar_drawer.RightSidebarDrawer(root)
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
    sidebar_drawer=drawer,
  )
  title_row = drawer._collapse_handle_button.master
  title_label_texts = [
    child.cget("text")
    for child in title_row.winfo_children()
    if isinstance(child, tkinter.Label)
  ]
  collapse_handle_pack_info = drawer._collapse_handle_button.pack_info()
  root.destroy()

  assert collapse_handle_pack_info["side"] == "right"
  assert collapse_handle_pack_info["in"] is title_row
  assert title_label_texts == ["Current location"]


def test_track_metadata_panel_metadata_text_height_fits_content_up_to_maximum():
  root = tkinter.Tk()
  root.withdraw()
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
  )
  point_metadata_text = track_metadata_panel._point_metadata_text
  text_container_children = point_metadata_text.master.winfo_children()
  scrollbar_children = [
    child
    for child in text_container_children
    if isinstance(child, tkinter.Scrollbar)
  ]

  assert int(point_metadata_text.cget("height")) == 1

  track_metadata_panel.set_point_metadata(["latitude: 40.0"])
  assert int(point_metadata_text.cget("height")) == 1

  track_metadata_panel.set_point_metadata([
    "latitude: 40.0",
    "longitude: -105.0",
    "timestamp: 2024-06-01 08:00:00 UTC",
  ])
  assert int(point_metadata_text.cget("height")) == 3

  many_metadata_lines = [
    "line_{index}: value".format(index=line_index)
    for line_index in range(20)
  ]
  track_metadata_panel.set_point_metadata(many_metadata_lines)
  displayed_metadata_text = point_metadata_text.get("1.0", tkinter.END).strip()
  displayed_metadata_line_count = len(displayed_metadata_text.splitlines())

  assert int(point_metadata_text.cget("height")) == \
    gis_graphical_editor.track_metadata_panel._METADATA_BOX_HEIGHT
  assert displayed_metadata_line_count == \
    gis_graphical_editor.track_metadata_panel._METADATA_BOX_HEIGHT
  assert scrollbar_children == []

  root.destroy()


def test_track_metadata_panel_set_panel_width_updates_metadata_text_width():
  root = tkinter.Tk()
  root.withdraw()
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
  )
  point_metadata_text = track_metadata_panel._point_metadata_text
  initial_metadata_text_width = int(point_metadata_text.cget("width"))

  track_metadata_panel.set_panel_width(500)
  updated_metadata_text_width = int(point_metadata_text.cget("width"))

  assert updated_metadata_text_width > initial_metadata_text_width
  assert int(point_metadata_text.cget("height")) == 1

  root.destroy()
