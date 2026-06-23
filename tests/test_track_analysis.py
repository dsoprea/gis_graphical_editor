"""Tests for track_analysis interval markers and timestamp lookup."""

import datetime

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.track_analysis


def test_build_hour_interval_markers_labels_total_hours_and_miles():
  start_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  middle_timestamp = datetime.datetime(2024, 6, 1, 9, 0, 0)
  end_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, start_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.01, -105.01, middle_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.02, -105.02, end_timestamp),
  ]

  interval_markers = gis_graphical_editor.track_analysis.build_hour_interval_markers(
    gpx_points,
    1,
  )

  assert len(interval_markers) == 2
  assert interval_markers[0].label.startswith("1 h,")
  assert interval_markers[1].label.startswith("2 h,")
  assert "mi" in interval_markers[0].label


def test_build_distance_interval_markers_labels_total_miles_and_timestamp():
  start_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  end_timestamp = datetime.datetime(2024, 6, 1, 8, 30, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, start_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.5, -105.5, end_timestamp),
  ]

  interval_markers = gis_graphical_editor.track_analysis.build_distance_interval_markers(
    gpx_points,
    10,
  )

  assert len(interval_markers) >= 1
  assert interval_markers[0].label.startswith("10 mi,")
  assert "2024-06-01" in interval_markers[0].label


def test_find_position_at_timestamp_interpolates_between_points():
  start_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  end_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, start_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(42.0, -107.0, end_timestamp),
  ]
  target_timestamp = datetime.datetime(2024, 6, 1, 9, 0, 0)

  latitude, longitude = gis_graphical_editor.track_analysis.find_position_at_timestamp(
    gpx_points,
    target_timestamp,
  )

  assert latitude == 41.0
  assert longitude == -106.0


def test_get_timestamp_range_returns_earliest_and_latest():
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, datetime.datetime(2024, 6, 1, 10, 0, 0)),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, datetime.datetime(2024, 6, 1, 8, 0, 0)),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.2, -105.2, datetime.datetime(2024, 6, 1, 12, 0, 0)),
  ]

  timestamp_range = gis_graphical_editor.track_analysis.get_timestamp_range(gpx_points)

  assert timestamp_range[0] == datetime.datetime(2024, 6, 1, 8, 0, 0)
  assert timestamp_range[1] == datetime.datetime(2024, 6, 1, 12, 0, 0)


def test_format_distance_interval_marker_label_includes_timezone_when_aware():
  marker_timestamp = datetime.datetime(
    2024,
    6,
    1,
    8,
    0,
    0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=-4)),
  )

  label_text = gis_graphical_editor.track_analysis.format_distance_interval_marker_label(
    10,
    marker_timestamp,
  )

  assert label_text.startswith("10 mi,")
  assert "UTC-04:00" in label_text
