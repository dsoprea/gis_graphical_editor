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
