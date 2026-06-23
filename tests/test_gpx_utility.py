"""Tests for gpx_utility GPX loading helpers."""

import datetime
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


def test_load_track_point_segments_from_gpx_preserves_segment_boundaries(tmp_path):
  gpx_document = gpxpy.gpx.GPX()
  track = gpxpy.gpx.GPXTrack()
  first_segment = gpxpy.gpx.GPXTrackSegment()
  first_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=40.0, longitude=-105.0))
  second_segment = gpxpy.gpx.GPXTrackSegment()
  second_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=41.0, longitude=-106.0))
  track.segments.append(first_segment)
  track.segments.append(second_segment)
  gpx_document.tracks.append(track)

  gpx_path = os.path.join(str(tmp_path), "segments.gpx")
  gpx_text = gpx_document.to_xml()
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  segment_point_lists = \
    gis_graphical_editor.gpx_utility.load_track_point_segments_from_gpx(gpx_path)

  assert len(segment_point_lists) == 2
  assert segment_point_lists[0][0].latitude == 40.0
  assert segment_point_lists[1][0].latitude == 41.0


def test_convert_gpx_point_timestamps_to_timezone_shifts_aware_utc_to_denver():
  utc_timestamp = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, utc_timestamp),
  ]

  converted_points, encountered_naive_timestamp = \
    gis_graphical_editor.gpx_utility.convert_gpx_point_timestamps_to_timezone(
      gpx_points,
      "America/Denver")

  assert encountered_naive_timestamp is False
  assert converted_points[0].timestamp == datetime.datetime(
    2024,
    6,
    1,
    6,
    0,
    0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=-6)),
  )


def test_convert_gpx_point_timestamps_to_timezone_treats_naive_as_utc():
  naive_timestamp = datetime.datetime(2024, 6, 1, 12, 0, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, naive_timestamp),
  ]

  converted_points, encountered_naive_timestamp = \
    gis_graphical_editor.gpx_utility.convert_gpx_point_timestamps_to_timezone(
      gpx_points,
      "America/New_York")

  assert encountered_naive_timestamp is True
  assert converted_points[0].timestamp.hour == 8
  assert converted_points[0].timestamp.tzinfo is not None
