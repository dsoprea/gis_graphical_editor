"""Tests for time_slider_panel timestamp label formatting."""

import datetime

import gis_graphical_editor.time_slider_panel


def test_format_slider_endpoint_timestamp_includes_timezone_name():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(timestamp)

  assert label_text == "2024-06-01 08:00:00 UTC"


def test_format_slider_endpoint_timestamp_includes_numeric_offset():
  mountain_timezone = datetime.timezone(datetime.timedelta(hours=-6))
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=mountain_timezone)
  label_text = gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(timestamp)

  assert label_text == "2024-06-01 08:00:00 UTC-06:00"


def test_format_display_timestamp_omits_date_and_timezone_by_default():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = gis_graphical_editor.time_slider_panel.format_display_timestamp(timestamp)

  assert label_text == "08:00:00"


def test_format_display_timestamp_includes_day_of_week_when_requested():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = gis_graphical_editor.time_slider_panel.format_display_timestamp(
    timestamp,
    include_date=True,
    include_day_of_week=True,
  )

  assert label_text == "Saturday 2024-06-01 08:00:00"


def test_format_current_slider_position_label_includes_point_position_suffix():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = gis_graphical_editor.time_slider_panel.format_current_slider_position_label(
    timestamp,
    2,
    5,
  )

  assert label_text == "2024-06-01 08:00:00 UTC (3 of 5)"


def test_clamp_selected_seconds_clamps_before_earliest():
  earliest_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  latest_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
  clamped_seconds = gis_graphical_editor.time_slider_panel.clamp_selected_seconds(
    earliest_timestamp.timestamp() - 60.0,
    earliest_timestamp,
    latest_timestamp,
  )

  assert clamped_seconds == earliest_timestamp.timestamp()


def test_clamp_selected_seconds_clamps_after_latest():
  earliest_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  latest_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
  clamped_seconds = gis_graphical_editor.time_slider_panel.clamp_selected_seconds(
    latest_timestamp.timestamp() + 60.0,
    earliest_timestamp,
    latest_timestamp,
  )

  assert clamped_seconds == latest_timestamp.timestamp()
