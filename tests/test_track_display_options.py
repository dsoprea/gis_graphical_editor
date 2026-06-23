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
