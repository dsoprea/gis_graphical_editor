"""Tests for overlay mode GPX export and filename helpers."""

import datetime
import os

import gpxpy

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.overlay_mode


def test_build_suggested_overlay_gpx_filename_replaces_spaces_and_unsafe_characters():
  export_timestamp = datetime.datetime(2026, 7, 22, 16, 30, 45)
  suggested_filename = gis_graphical_editor.overlay_mode.build_suggested_overlay_gpx_filename(
    "Key West / Bahia Honda",
    export_timestamp=export_timestamp,
  )

  assert suggested_filename == "20260722-163045_Key_West_Bahia_Honda.gpx"


def test_write_captured_overlays_to_gpx_writes_one_segment_per_overlay(tmp_path):
  first_location = gis_graphical_editor.gpx_utility.GpxPointRecord(
    24.555,
    -81.802,
    None,
    {"name": "Waypoint A"},
  )
  second_location = gis_graphical_editor.gpx_utility.GpxPointRecord(
    24.556,
    -81.803,
    None,
    {},
  )
  captured_overlays = [
    gis_graphical_editor.overlay_mode.CapturedOverlay(
      "overlay-1",
      "First overlay",
      [first_location],
    ),
    gis_graphical_editor.overlay_mode.CapturedOverlay(
      "overlay-2",
      "Second overlay",
      [first_location, second_location],
    ),
  ]
  gpx_filepath = os.path.join(str(tmp_path), "overlays.gpx")

  gis_graphical_editor.overlay_mode.write_captured_overlays_to_gpx(
    gpx_filepath,
    "Trip overlays",
    captured_overlays,
  )

  with open(gpx_filepath, "r", encoding="utf-8") as gpx_file:
    gpx_text = gpx_file.read()

  gpx_document = gpxpy.parse(gpx_text)

  assert gpx_document.description == "Trip overlays"
  assert len(gpx_document.tracks) == 1
  assert len(gpx_document.tracks[0].segments) == 2
  assert len(gpx_document.tracks[0].segments[0].points) == 1
  assert len(gpx_document.tracks[0].segments[1].points) == 2
  assert gpx_document.tracks[0].segments[0].points[0].name == "Waypoint A"
