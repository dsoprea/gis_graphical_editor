"""Tests for rotated trkseg label placement helpers."""

import datetime

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.track_analysis


def test_compute_middle_adjacent_segment_point_pair_returns_central_points():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.5, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(41.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(41.5, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(42.0, -105.0, None),
  ]

  middle_point_pair = \
    gis_graphical_editor.track_analysis.compute_middle_adjacent_segment_point_pair(
      segment_points,
    )

  assert middle_point_pair[0].latitude == 41.0
  assert middle_point_pair[1].latitude == 41.5


def test_build_segment_label_placements_skips_empty_labels():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(42.0, -105.0, None),
  ]
  segment_point_lists = [segment_points]
  segment_label_texts = [""]

  segment_label_placements = \
    gis_graphical_editor.track_analysis.build_segment_label_placements(
      segment_point_lists,
      segment_label_texts,
      [0],
    )

  assert segment_label_placements == []


def test_build_segment_label_placements_returns_middle_point_pair_for_checked_segment():
  start_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  end_timestamp = datetime.datetime(2024, 6, 1, 9, 0, 0)
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, start_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(42.0, -105.0, end_timestamp),
  ]
  segment_point_lists = [segment_points]
  segment_label_texts = ["Key West"]

  segment_label_placements = \
    gis_graphical_editor.track_analysis.build_segment_label_placements(
      segment_point_lists,
      segment_label_texts,
      [0],
    )

  assert len(segment_label_placements) == 1
  assert segment_label_placements[0].label == "Key West"
  assert segment_label_placements[0].first_latitude == 40.0
  assert segment_label_placements[0].second_latitude == 42.0


def test_split_segment_label_texts_at_index_keeps_head_label_and_clears_tail():
  segment_label_texts = ["Original"]

  updated_segment_label_texts = \
    gis_graphical_editor.track_analysis.split_segment_label_texts_at_index(
      segment_label_texts,
      0,
    )

  assert updated_segment_label_texts == ["Original", ""]
