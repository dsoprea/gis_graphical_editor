"""Launch the GIS graphical editor application."""

import argparse
import logging
import sys
import tkinter

import gis_graphical_editor.main_window
import gis_graphical_editor.track_display_options

_LOGGER = logging.getLogger(__name__)


def main(argv=None):
  logging.basicConfig(level=logging.INFO)

  argument_parser = argparse.ArgumentParser(
    description="View GPX tracks on an OpenStreetMap map.",
  )
  argument_parser.add_argument(
    "--mark-hours",
    metavar="N",
    type=int,
    help="Place an orange marker every N hours along the path.",
  )
  argument_parser.add_argument(
    "--mark-distance",
    metavar="N",
    type=int,
    help="Place a red marker every N miles along the path.",
  )
  argument_parser.add_argument(
    "--points",
    action="store_true",
    help="Draw a green dot at every recorded GPX point.",
  )
  argument_parser.add_argument(
    "--no-mark-labels",
    action="store_true",
    help="Hide text labels on --mark-hours and --mark-distance markers.",
  )
  argument_parser.add_argument(
    "--filepath",
    metavar="PATH",
    help="Load this GPX file immediately on startup.",
  )

  if argv is None:
    arguments = argument_parser.parse_args()
  else:
    arguments = argument_parser.parse_args(argv)

  if arguments.mark_hours is not None and arguments.mark_hours <= 0:
    argument_parser.error("--mark-hours requires a positive integer.")

  if arguments.mark_distance is not None and arguments.mark_distance <= 0:
    argument_parser.error("--mark-distance requires a positive integer.")

  track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions(
    mark_hours_interval=arguments.mark_hours,
    mark_distance_interval=arguments.mark_distance,
    show_points=arguments.points,
    show_mark_labels=not arguments.no_mark_labels,
    initial_gpx_filepath=arguments.filepath,
  )

  root = tkinter.Tk()
  gis_graphical_editor.main_window.MainWindow(root, track_display_options)
  root.mainloop()


if __name__ == "__main__":
  main(sys.argv[1:])
