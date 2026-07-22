"""Tests for time_slider_panel timestamp label formatting."""

import datetime
import tkinter

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.track_analysis
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
    1,
    3,
    2,
    5,
  )

  assert label_text == \
    "2024-06-01 08:00:00 UTC\n" \
    "(Current: 2 of 3, All: 3 of 5)"


def test_format_current_slider_position_label_without_location_uses_metadata_placeholder():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = \
    gis_graphical_editor.time_slider_panel.format_current_slider_position_label_without_location(
      timestamp,
    )

  assert label_text == \
    "2024-06-01 08:00:00 UTC\n" \
    "(No location selected.)"


def test_update_timed_gpx_points_with_empty_list_shows_no_location_label():
  root = tkinter.Tk()
  root.withdraw()
  earliest_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  latest_timestamp = datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
  timed_gpx_points = [
    gis_graphical_editor.gpx_utility.GpxPointRecord(
      40.0,
      -105.0,
      earliest_timestamp,
    ),
  ]
  segment_summaries = [
    gis_graphical_editor.track_analysis.TrackSegmentSummary(
      timed_gpx_points,
      earliest_timestamp,
      latest_timestamp,
    ),
  ]
  timestamp_changes = []

  def record_timestamp_change(selected_timestamp):
    timestamp_changes.append(selected_timestamp)

  time_slider_panel = gis_graphical_editor.time_slider_panel.TimeSliderPanel(
    root,
    earliest_timestamp,
    latest_timestamp,
    timed_gpx_points,
    record_timestamp_change,
    segment_summaries,
  )
  time_slider_panel.update_timed_gpx_points(
    [],
    earliest_timestamp,
    latest_timestamp,
    [],
  )
  current_label_text = time_slider_panel._current_time_label.cget("text")
  root.destroy()

  assert "(No location selected.)" in current_label_text
  assert len(timestamp_changes) >= 2


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


def test_time_slider_panel_inside_container_has_minimum_animation_width():
  root = tkinter.Tk()
  root.withdraw()
  map_column_frame = tkinter.Frame(root)
  map_column_frame.pack()
  time_slider_container_frame = tkinter.Frame(map_column_frame)
  time_slider_container_frame.pack(side=tkinter.TOP, fill=tkinter.X)
  earliest_timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  latest_timestamp = datetime.datetime(2026, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
  first_gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    earliest_timestamp,
  )
  second_gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.1,
    -105.1,
    latest_timestamp,
  )
  timed_gpx_points = [first_gpx_point, second_gpx_point]
  segment_summaries = [
    gis_graphical_editor.track_analysis.TrackSegmentSummary(
      timed_gpx_points,
      earliest_timestamp,
      latest_timestamp,
    ),
  ]
  time_slider_panel = gis_graphical_editor.time_slider_panel.TimeSliderPanel(
    time_slider_container_frame,
    earliest_timestamp,
    latest_timestamp,
    timed_gpx_points,
    lambda selected_timestamp: None,
    segment_summaries,
  )
  time_slider_panel.pack(side=tkinter.TOP, fill=tkinter.X)
  time_slider_container_frame.update_idletasks()
  animation_container_minimum_width = time_slider_container_frame.winfo_reqwidth()
  root.destroy()

  assert animation_container_minimum_width >= 500
