"""Tests for segment list panel selection controls."""

import datetime
import tkinter

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.segment_list_panel
import gis_graphical_editor.track_analysis


def _build_segment_summary(latitude, longitude, timestamp):
  """Return one TrackSegmentSummary with a single timed point."""

  gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    latitude,
    longitude,
    timestamp,
  )
  segment_points = [gpx_point]

  return gis_graphical_editor.track_analysis.TrackSegmentSummary(
    segment_points,
    timestamp,
    timestamp,
  )


def _build_segment_list_panel(segment_summaries):
  """Return a hidden SegmentListPanel wired to a no-op selection callback."""

  root = tkinter.Tk()
  root.withdraw()
  selection_change_count = 0

  def handle_selection_changed():
    nonlocal selection_change_count
    selection_change_count += 1

  segment_list_panel = gis_graphical_editor.segment_list_panel.SegmentListPanel(
    root,
    segment_summaries,
    handle_selection_changed,
    lambda: None,
    lambda: None,
    lambda: None,
    panel_width=400,
  )

  return root, segment_list_panel, handle_selection_changed


def test_select_all_and_select_none_buttons_start_enabled_for_all_checked_segments():
  first_segment = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_segment = _build_segment_summary(
    40.1,
    -105.1,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [first_segment, second_segment],
  )

  assert str(segment_list_panel._select_all_button.cget("state")) == "disabled"
  assert str(segment_list_panel._select_none_button.cget("state")) == "normal"

  root.destroy()


def test_select_none_button_unchecks_every_segment_and_disables_itself():
  first_segment = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_segment = _build_segment_summary(
    40.1,
    -105.1,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  root, segment_list_panel, handle_selection_changed = _build_segment_list_panel(
    [first_segment, second_segment],
  )
  selection_change_count = 0

  def count_selection_changes():
    nonlocal selection_change_count
    selection_change_count += 1

  segment_list_panel._on_selection_changed = count_selection_changes
  segment_list_panel._handle_select_none_button_clicked()

  assert segment_list_panel.get_checked_segment_indices() == []
  assert str(segment_list_panel._select_none_button.cget("state")) == "disabled"
  assert str(segment_list_panel._select_all_button.cget("state")) == "normal"
  assert selection_change_count == 1

  root.destroy()


def test_select_all_button_checks_every_segment_and_disables_itself():
  first_segment = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_segment = _build_segment_summary(
    40.1,
    -105.1,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [first_segment, second_segment],
  )
  segment_list_panel._selection_variables[0].set(False)
  segment_list_panel._refresh_selection_button_states()
  selection_change_count = 0

  def count_selection_changes():
    nonlocal selection_change_count
    selection_change_count += 1

  segment_list_panel._on_selection_changed = count_selection_changes
  segment_list_panel._handle_select_all_button_clicked()

  assert segment_list_panel.get_checked_segment_indices() == [0, 1]
  assert str(segment_list_panel._select_all_button.cget("state")) == "disabled"
  assert str(segment_list_panel._select_none_button.cget("state")) == "normal"
  assert selection_change_count == 1

  root.destroy()


def test_selection_button_states_update_when_one_checkbox_is_toggled():
  first_segment = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  second_segment = _build_segment_summary(
    40.1,
    -105.1,
    datetime.datetime(2024, 6, 1, 9, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [first_segment, second_segment],
  )

  segment_list_panel._selection_variables[0].set(False)
  segment_list_panel._handle_selection_changed()

  assert str(segment_list_panel._select_all_button.cget("state")) == "normal"
  assert str(segment_list_panel._select_none_button.cget("state")) == "normal"

  root.destroy()
