"""Tests for TrackDisplayOptions CLI mapping."""

import argparse

import gis_graphical_editor.track_display_options


def test_track_display_options_hide_mark_labels_when_requested():
  argument_parser = argparse.ArgumentParser()
  argument_parser.add_argument("--no-mark-labels", action="store_true")
  arguments = argument_parser.parse_args(["--no-mark-labels"])

  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    show_mark_labels=not arguments.no_mark_labels,
  )

  assert track_display_options.show_mark_labels is False


def test_track_display_options_stores_initial_gpx_filepath():
  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    initial_gpx_filepath="/tmp/track.gpx",
  )

  assert track_display_options.initial_gpx_filepath == "/tmp/track.gpx"


def test_track_display_options_stores_as_timezone_name():
  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    as_timezone_name="America/Chicago",
  )

  assert track_display_options.as_timezone_name == "America/Chicago"


def test_track_display_options_stores_show_dates_in_mark_labels():
  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    show_dates_in_mark_labels=True,
  )

  assert track_display_options.show_dates_in_mark_labels is True


def test_track_display_options_stores_use_metric_units():
  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    use_metric_units=True,
  )

  assert track_display_options.use_metric_units is True
