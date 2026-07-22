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


def test_each_segment_row_has_an_information_canvas():
  segment_summary = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [segment_summary],
  )

  assert len(segment_list_panel._segment_info_canvases) == 1

  root.destroy()


def test_segment_information_popup_shows_segment_metadata_and_focuses_close_button():
  segment_summary = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [segment_summary],
  )
  root.deiconify()

  segment_list_panel._show_segment_information_popup(0)
  root.update()
  root.update_idletasks()
  root.update()
  popup_children = root.winfo_children()
  popup_window = popup_children[-1]
  metadata_text_widget = None
  close_button = None

  for child_widget in popup_window.winfo_children():
    if child_widget.winfo_class() == "Text":
      metadata_text_widget = child_widget

    if child_widget.winfo_class() == "Button":
      close_button = child_widget

  assert metadata_text_widget is not None
  popup_text = metadata_text_widget.get("1.0", tkinter.END)
  assert "point_count: 1" in popup_text
  assert \
    int(metadata_text_widget.cget("width")) == \
    gis_graphical_editor.segment_list_panel._SEGMENT_INFORMATION_POPUP_TEXT_WIDTH
  assert close_button is not None
  assert popup_window.focus_get() == close_button
  popup_window.destroy()
  root.destroy()


def test_sync_segment_row_wraplengths_uses_list_canvas_width():
  first_segment = _build_segment_summary(
    40.0,
    -105.0,
    datetime.datetime(2024, 6, 1, 8, 0, 0),
  )
  root, segment_list_panel, _handle_selection_changed = _build_segment_list_panel(
    [first_segment],
  )
  list_canvas_width = 360
  segment_list_panel._sync_segment_row_wraplengths(list_canvas_width=list_canvas_width)
  expected_wraplength = \
    gis_graphical_editor.segment_list_panel._compute_segment_label_wraplength_for_list_canvas_width(
      list_canvas_width,
    )

  assert segment_list_panel._segment_checkbuttons[0].cget("wraplength") == expected_wraplength

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
