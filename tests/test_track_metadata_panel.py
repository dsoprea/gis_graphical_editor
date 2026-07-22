"""Tests for track metadata panel layout."""

import tkinter

import gis_graphical_editor.track_metadata_panel


def test_track_metadata_panel_exposes_only_current_point_section():
  root = tkinter.Tk()
  root.withdraw()
  track_metadata_panel = gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
    root,
    panel_width=400,
  )

  assert hasattr(track_metadata_panel, "_point_metadata_text")
  assert not hasattr(track_metadata_panel, "_segment_metadata_text")

  root.destroy()
