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
  assert "09:00:00" in interval_markers[0].label
  assert "2024-06-01" not in interval_markers[0].label


def test_build_hour_interval_markers_includes_date_when_requested():
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
    show_dates=True,
  )

  assert "2024-06-01 09:00:00" in interval_markers[0].label


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
  assert "08:" in interval_markers[0].label
  assert "2024-06-01" not in interval_markers[0].label


def test_build_distance_interval_markers_includes_date_when_requested():
  start_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  end_timestamp = datetime.datetime(2024, 6, 1, 8, 30, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, start_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.5, -105.5, end_timestamp),
  ]

  interval_markers = gis_graphical_editor.track_analysis.build_distance_interval_markers(
    gpx_points,
    10,
    show_dates=True,
  )

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


def test_format_distance_interval_marker_label_omits_timezone_when_aware():
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

  assert label_text == "10 mi, 08:00:00"


def test_build_track_segment_summaries_sorts_by_earliest_timestamp():
  later_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 11, 0, 0),
    ),
  ]
  earlier_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.1,
      -106.1,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
  ]

  segment_summaries = gis_graphical_editor.track_analysis.build_track_segment_summaries(
    [later_segment, earlier_segment],
  )

  assert len(segment_summaries) == 2
  assert segment_summaries[0].earliest_timestamp.hour == 8
  assert segment_summaries[1].earliest_timestamp.hour == 10


def test_format_track_segment_interval_label_includes_point_count_and_duration():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 30, 15),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 30, 15),
  )

  label_text = gis_graphical_editor.track_analysis.format_track_segment_interval_label(
    segment_summary,
  )

  assert label_text == \
    "Start Timestamp: Saturday 2024-06-01 08:00:00\n" \
    "End Timestamp: Saturday 2024-06-01 10:30:15\n" \
    "Points: 2\n" \
    "Interval: 02:30:15\n" \
    "Distance: 9 mi\n" \
    "Velocity: AVG 3.5 mph, MIN 3.5 mph, MAX 3.5 mph"


def test_format_track_segment_interval_label_uses_kilometers_when_metric_requested():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 30, 15),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 30, 15),
  )

  label_text = gis_graphical_editor.track_analysis.format_track_segment_interval_label(
    segment_summary,
    use_metric_units=True,
  )

  assert "Distance: 14 km" in label_text
  assert "Velocity: AVG" in label_text
  assert "MIN" in label_text
  assert "MAX" in label_text
  assert "kph" in label_text


def test_format_track_segment_interval_label_includes_idle_leg_velocities_by_default():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0001,
      -105.0001,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 0, 0),
  )

  label_text = gis_graphical_editor.track_analysis.format_track_segment_interval_label(
    segment_summary,
  )

  assert "Velocity: AVG" in label_text
  assert "MIN 0.0 mph," in label_text
  assert "MAX 8.7 mph" in label_text


def test_format_track_segment_interval_label_omits_idle_leg_velocities_when_no_idle():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0001,
      -105.0001,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 0, 0),
  )

  label_text = gis_graphical_editor.track_analysis.format_track_segment_interval_label(
    segment_summary,
    exclude_idle_segments=True,
  )

  assert "Velocity: AVG" in label_text
  assert "MIN 8.7 mph," in label_text
  assert "MAX 8.7 mph" in label_text


def test_is_idle_track_segment_summary_uses_mph_threshold_by_default():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0001,
      -105.0001,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )

  assert gis_graphical_editor.track_analysis.is_idle_track_segment_summary(segment_summary) is True


def test_is_idle_track_segment_summary_uses_kph_threshold_when_metric_requested():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0001,
      -105.0001,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )

  assert gis_graphical_editor.track_analysis.is_idle_track_segment_summary(
    segment_summary,
    use_metric_units=True,
  ) is True


def test_build_track_segment_summaries_excludes_idle_segments_when_requested():
  idle_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0001,
      -105.0001,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
  ]
  active_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.1,
      -106.1,
      datetime.datetime(2024, 6, 1, 11, 0, 0),
    ),
  ]

  segment_summaries = gis_graphical_editor.track_analysis.build_track_segment_summaries(
    [idle_segment, active_segment],
    exclude_idle_segments=True,
  )

  assert len(segment_summaries) == 1
  assert segment_summaries[0].earliest_timestamp.hour == 10


def test_compute_total_path_distance_for_gpx_points_sums_consecutive_legs():
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.2, -105.2, None),
  ]

  total_distance = gis_graphical_editor.track_analysis.compute_total_path_distance_for_gpx_points(
    gpx_points,
  )
  first_leg_distance = gis_graphical_editor.track_analysis.compute_distance_between_points(
    gpx_points[0],
    gpx_points[1],
  )
  second_leg_distance = gis_graphical_editor.track_analysis.compute_distance_between_points(
    gpx_points[1],
    gpx_points[2],
  )

  assert total_distance == first_leg_distance + second_leg_distance


def test_format_track_segment_interval_label_describes_untimed_segments():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, None),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    None,
    None,
  )

  label_text = gis_graphical_editor.track_analysis.format_track_segment_interval_label(
    segment_summary,
  )

  assert label_text == \
    "Points: 2\n" \
    "Distance: 9 mi\n" \
    "no timestamps"


def test_format_track_segment_delete_confirmation_text_includes_timestamps_and_point_count():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 0, 0),
  )

  confirmation_text = \
    gis_graphical_editor.track_analysis.format_track_segment_delete_confirmation_text(
      segment_summary,
    )

  assert confirmation_text.startswith("From:")
  assert "To:" in confirmation_text
  assert "Points: 2" in confirmation_text
  assert "Distance:" not in confirmation_text
  assert "Interval:" not in confirmation_text
  assert "Velocity:" not in confirmation_text


def test_format_track_segment_delete_confirmation_text_describes_untimed_segments():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, None),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    None,
    None,
  )

  confirmation_text = \
    gis_graphical_editor.track_analysis.format_track_segment_delete_confirmation_text(
      segment_summary,
    )

  assert confirmation_text == \
    "Points: 2\n" \
    "no timestamps"


def test_build_hour_interval_markers_uses_kilometers_when_metric_requested():
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
    use_metric_units=True,
  )

  assert "km" in interval_markers[0].label
  assert "mi" not in interval_markers[0].label


def test_format_distance_interval_marker_label_uses_kilometers_when_metric_requested():
  marker_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)

  label_text = gis_graphical_editor.track_analysis.format_distance_interval_marker_label(
    10,
    marker_timestamp,
    use_metric_units=True,
  )

  assert label_text == "10 km, 08:00:00"


def test_find_gpx_point_nearest_timestamp_returns_closest_point():
  first_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  second_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, first_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, second_timestamp),
  ]
  target_timestamp = datetime.datetime(2024, 6, 1, 9, 30, 0)

  nearest_gpx_point = gis_graphical_editor.track_analysis.find_gpx_point_nearest_timestamp(
    gpx_points,
    target_timestamp,
  )

  assert nearest_gpx_point is gpx_points[1]


def test_find_gpx_point_nearest_timestamp_returns_first_point_before_track_start():
  first_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0)
  second_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)
  gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, first_timestamp),
    gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, second_timestamp),
  ]
  target_timestamp = datetime.datetime(2024, 6, 1, 7, 0, 0)

  nearest_gpx_point = gis_graphical_editor.track_analysis.find_gpx_point_nearest_timestamp(
    gpx_points,
    target_timestamp,
  )

  assert nearest_gpx_point is gpx_points[0]


def test_find_segment_summary_for_gpx_point_matches_by_identity():
  first_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    41.0,
    -106.0,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  first_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [first_point],
    first_point.timestamp,
    first_point.timestamp,
  )
  second_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [second_point],
    second_point.timestamp,
    second_point.timestamp,
  )

  segment_summary = gis_graphical_editor.track_analysis.find_segment_summary_for_gpx_point(
    [first_segment, second_segment],
    second_point,
  )

  assert segment_summary is second_segment


def test_find_track_segment_summary_index_at_timestamp_returns_middle_segment():
  first_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  second_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 10, 0, 0),
    datetime.datetime(2024, 6, 1, 11, 0, 0),
  )
  third_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 12, 0, 0),
    datetime.datetime(2024, 6, 1, 13, 0, 0),
  )
  segment_summaries = [first_segment, second_segment, third_segment]
  target_timestamp = datetime.datetime(2024, 6, 1, 10, 30, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      segment_summaries,
      target_timestamp,
    )

  assert segment_index == 1


def test_find_track_segment_summary_index_at_timestamp_returns_none_before_first_segment():
  first_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  target_timestamp = datetime.datetime(2024, 6, 1, 7, 0, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      [first_segment],
      target_timestamp,
    )

  assert segment_index is None


def test_find_track_segment_summary_index_at_timestamp_returns_none_after_last_segment():
  last_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  target_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      [last_segment],
      target_timestamp,
    )

  assert segment_index is None


def test_find_track_segment_summary_index_at_timestamp_returns_none_in_gap():
  first_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  second_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 10, 0, 0),
    datetime.datetime(2024, 6, 1, 11, 0, 0),
  )
  target_timestamp = datetime.datetime(2024, 6, 1, 9, 30, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      [first_segment, second_segment],
      target_timestamp,
    )

  assert segment_index is None


def test_find_track_segment_summary_index_at_timestamp_skips_untimed_segment():
  untimed_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    None,
    None,
  )
  timed_segment = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    [],
    datetime.datetime(2024, 6, 1, 10, 0, 0),
    datetime.datetime(2024, 6, 1, 11, 0, 0),
  )
  target_timestamp = datetime.datetime(2024, 6, 1, 10, 30, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      [untimed_segment, timed_segment],
      target_timestamp,
    )

  assert segment_index == 1


def test_find_track_segment_summary_index_at_timestamp_returns_none_for_empty_list():
  target_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0)

  segment_index = \
    gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
      [],
      target_timestamp,
    )

  assert segment_index is None


def test_collect_timed_gpx_points_preserves_order_and_skips_untimed_points():
  first_timed_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  untimed_point = gis_graphical_editor.gpx_utility.GpxPointRecord(40.1, -105.1, None)
  second_timed_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.2,
    -105.2,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )

  timed_gpx_points = gis_graphical_editor.track_analysis.collect_timed_gpx_points([
    first_timed_point,
    untimed_point,
    second_timed_point,
  ])

  assert timed_gpx_points == [first_timed_point, second_timed_point]


def test_find_timed_gpx_point_index_nearest_timestamp_returns_closest_index():
  timed_gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.2,
      -105.2,
      datetime.datetime(2024, 6, 1, 12, 0, 0),
    ),
  ]
  target_timestamp = datetime.datetime(2024, 6, 1, 10, 30, 0)

  point_index = \
    gis_graphical_editor.track_analysis.find_timed_gpx_point_index_nearest_timestamp(
      timed_gpx_points,
      target_timestamp,
    )

  assert point_index == 1


def test_format_gpx_point_metadata_lines_includes_additional_metadata():
  gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    additional_metadata={
      "elevation": "7",
      "speed": "11.75",
    },
  )

  metadata_lines = gis_graphical_editor.track_analysis.format_gpx_point_metadata_lines(
    gpx_point,
  )

  assert metadata_lines[0] == "latitude: 40.0"
  assert metadata_lines[1] == "longitude: -105.0"
  assert metadata_lines[2] == "timestamp: 2024-06-01 08:00:00"
  assert "elevation: 7" in metadata_lines
  assert "speed: 11.75" in metadata_lines


def test_format_segment_summary_metadata_lines_includes_derived_values():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_summary = gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
    datetime.datetime(2024, 6, 1, 10, 0, 0),
  )

  metadata_lines = gis_graphical_editor.track_analysis.format_segment_summary_metadata_lines(
    segment_summary,
  )

  assert metadata_lines[0] == "point_count: 2"
  assert metadata_lines[1] == "distance: 9 mi"
  assert metadata_lines[3] == "latest_timestamp: 2024-06-01 10:00:00"
  assert metadata_lines[4] == "interval: 02:00:00"
  assert metadata_lines[6] == "idle: False"


def test_is_segment_split_allowed_at_point_index_rejects_endpoints():
  assert gis_graphical_editor.track_analysis.is_segment_split_allowed_at_point_index(0, 5) is False
  assert gis_graphical_editor.track_analysis.is_segment_split_allowed_at_point_index(4, 5) is False
  assert gis_graphical_editor.track_analysis.is_segment_split_allowed_at_point_index(2, 5) is True


def test_split_gpx_segment_point_lists_at_point_index_moves_tail_into_new_segment():
  first_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.1,
    -105.1,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  third_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.2,
    -105.2,
    datetime.datetime(2024, 6, 1, 10, 0, 0),
  )
  fourth_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.3,
    -105.3,
    datetime.datetime(2024, 6, 1, 11, 0, 0),
  )
  other_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 12, 0, 0),
    ),
  ]
  segment_points = [first_point, second_point, third_point, fourth_point]
  segment_point_lists = [segment_points, other_segment]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.split_gpx_segment_point_lists_at_point_index(
      segment_point_lists,
      segment_points,
      2,
    )

  assert updated_segment_point_lists[0] == [first_point, second_point]
  assert updated_segment_point_lists[1] == [third_point, fourth_point]
  assert updated_segment_point_lists[2] is other_segment


def test_split_gpx_segment_point_lists_at_point_index_returns_none_for_invalid_split():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.1,
      -105.1,
      datetime.datetime(2024, 6, 1, 9, 0, 0),
    ),
  ]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.split_gpx_segment_point_lists_at_point_index(
      [segment_points],
      segment_points,
      0,
    )

  assert updated_segment_point_lists is None


def test_remove_gpx_segment_from_segment_point_lists_removes_target_segment():
  first_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
  ]
  second_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  third_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      42.0,
      -107.0,
      datetime.datetime(2024, 6, 1, 12, 0, 0),
    ),
  ]
  segment_point_lists = [first_segment, second_segment, third_segment]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.remove_gpx_segment_from_segment_point_lists(
      segment_point_lists,
      second_segment,
    )

  assert updated_segment_point_lists == [first_segment, third_segment]
  assert updated_segment_point_lists[0] is first_segment
  assert updated_segment_point_lists[1] is third_segment


def test_remove_gpx_segment_from_segment_point_lists_removes_first_segment():
  first_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
  ]
  second_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_point_lists = [first_segment, second_segment]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.remove_gpx_segment_from_segment_point_lists(
      segment_point_lists,
      first_segment,
    )

  assert updated_segment_point_lists == [second_segment]
  assert updated_segment_point_lists[0] is second_segment


def test_remove_gpx_segment_from_segment_point_lists_removes_last_segment():
  first_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
  ]
  second_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]
  segment_point_lists = [first_segment, second_segment]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.remove_gpx_segment_from_segment_point_lists(
      segment_point_lists,
      second_segment,
    )

  assert updated_segment_point_lists == [first_segment]
  assert updated_segment_point_lists[0] is first_segment


def test_remove_gpx_segment_from_segment_point_lists_returns_none_when_not_found():
  segment_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      datetime.datetime(2024, 6, 1, 8, 0, 0),
    ),
  ]
  other_segment = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      41.0,
      -106.0,
      datetime.datetime(2024, 6, 1, 10, 0, 0),
    ),
  ]

  updated_segment_point_lists = \
    gis_graphical_editor.track_analysis.remove_gpx_segment_from_segment_point_lists(
      [other_segment],
      segment_points,
    )

  assert updated_segment_point_lists is None
