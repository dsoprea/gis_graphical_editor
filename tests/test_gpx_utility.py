"""Tests for gpx_utility GPX loading helpers."""

import os

import gpxpy
import gpxpy.gpx

import gis_graphical_editor.gpx_utility


def test_load_track_points_from_gpx_reads_track_segment(tmp_path):
  gpx_document = gpxpy.gpx.GPX()
  track = gpxpy.gpx.GPXTrack()
  segment = gpxpy.gpx.GPXTrackSegment()
  segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=40.0, longitude=-105.0))
  segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=40.1, longitude=-105.1))
  track.segments.append(segment)
  gpx_document.tracks.append(track)

  gpx_path = os.path.join(str(tmp_path), "sample.gpx")
  gpx_text = gpx_document.to_xml()
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  track_points = gis_graphical_editor.gpx_utility.load_track_points_from_gpx(gpx_path)

  assert track_points == [(40.0, -105.0), (40.1, -105.1)]
