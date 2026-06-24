"""Capture README and FEATURES screenshots for a sample GPX track."""

import argparse
import logging
import os
import subprocess
import sys
import tkinter

import PIL.Image

import gis_graphical_editor.main_window
import gis_graphical_editor.track_analysis
import gis_graphical_editor.track_display_options

_LOGGER = logging.getLogger(__name__)

_DEFAULT_GPX_FILENAME = "2026-04-20_181129_AutoLog_Key_West.gpx"
_OUTPUT_DIRECTORY = os.path.join("asset", "documentation", "image")
_TILE_LOAD_WAIT_MILLISECONDS = 12000
_WINDOW_GEOMETRY = "1024x768"
_SIDEBAR_CROP_WIDTH = 420


def _capture_root_window_image(root):
  """Return a PIL image of the root Tk window using ImageMagick import."""

  root.update_idletasks()
  root.update()

  window_identifier = root.winfo_id()
  temporary_path = os.path.join(
    os.environ.get("TMPDIR", "/tmp"),
    "gge_screenshot_{window_identifier}.png".format(
      window_identifier=window_identifier,
    ),
  )

  # ImageMagick import captures the X11 window reliably on Linux.
  subprocess.run(
    [
      "import",
      "-window",
      str(window_identifier),
      temporary_path,
    ],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  screenshot_image = PIL.Image.open(temporary_path)
  screenshot_image.load()
  os.remove(temporary_path)

  return screenshot_image


def _crop_sidebar_image(screenshot_image):
  """Return the right-hand sidebar region from a full-window screenshot."""

  image_width, image_height = screenshot_image.size
  left_edge = image_width - _SIDEBAR_CROP_WIDTH

  if left_edge < 0:
    left_edge = 0

  return screenshot_image.crop((left_edge, 0, image_width, image_height))


def _save_screenshot_variants(root, output_directory, output_variants):
  """Write one or more PNG outputs, optionally cropping the captured window."""

  screenshot_image = _capture_root_window_image(root)

  for output_filename, crop_sidebar in output_variants:
    if crop_sidebar:
      output_image = _crop_sidebar_image(screenshot_image)
    else:
      output_image = screenshot_image

    output_path = os.path.join(output_directory, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_image.save(output_path, format="PNG")
    _LOGGER.info("Wrote %s", output_path)


def _build_track_display_options(gpx_path, screenshot_profile):
  """Return TrackDisplayOptions for the named documentation screenshot profile."""

  if screenshot_profile == "recorded-points":
    return gis_graphical_editor.track_display_options.TrackDisplayOptions(
      initial_gpx_filepath=gpx_path,
      show_points=True,
    )

  if screenshot_profile == "interval-markers":
    return gis_graphical_editor.track_display_options.TrackDisplayOptions(
      initial_gpx_filepath=gpx_path,
      mark_hours_interval=2,
      mark_distance_interval=10,
    )

  if screenshot_profile == "combined-overlays":
    return gis_graphical_editor.track_display_options.TrackDisplayOptions(
      initial_gpx_filepath=gpx_path,
      show_points=True,
      mark_hours_interval=2,
      mark_distance_interval=10,
    )

  return gis_graphical_editor.track_display_options.TrackDisplayOptions(
    initial_gpx_filepath=gpx_path,
  )


def _prepare_time_slider_midpoint(main_window, root):
  """Move the slider to a mid-track timed point for animation documentation."""

  if main_window._loaded_gpx_points is None:
    return

  if main_window._time_slider_panel is None:
    return

  timed_gpx_points = \
    gis_graphical_editor.track_analysis.collect_timed_gpx_points(
      main_window._loaded_gpx_points,
    )

  if not timed_gpx_points:
    return

  midpoint_index = len(timed_gpx_points) // 2
  midpoint_point = timed_gpx_points[midpoint_index]
  main_window._time_slider_panel.set_selected_timestamp(midpoint_point.timestamp)
  root.update_idletasks()
  root.update()


def _prepare_segments_after_split(main_window, root):
  """Split the track at the mid-track slider position for segment editing docs."""

  _prepare_time_slider_midpoint(main_window, root)
  main_window._handle_segment_split_requested()
  root.update_idletasks()
  root.update()


def _capture_screenshot_job(gpx_path, output_directory, screenshot_job):
  """Load gge for one job, run optional UI setup, and save PNG variant(s)."""

  screenshot_profile = screenshot_job["profile"]
  track_display_options = _build_track_display_options(gpx_path, screenshot_profile)
  root = tkinter.Tk()
  root.geometry(_WINDOW_GEOMETRY)
  main_window = gis_graphical_editor.main_window.MainWindow(root, track_display_options)
  prepare_window = screenshot_job["prepare_window"]
  output_variants = screenshot_job["outputs"]

  def _finish_capture():
    """Run prepare hooks, save PNGs, and exit the Tk main loop."""

    if prepare_window is not None:
      prepare_window(main_window, root)

    _save_screenshot_variants(root, output_directory, output_variants)
    root.quit()

  root.after(_TILE_LOAD_WAIT_MILLISECONDS, _finish_capture)
  root.mainloop()
  root.destroy()


def _build_screenshot_jobs():
  """Return the standard documentation capture jobs for README and FEATURES."""

  screenshot_jobs = [
    {
      "profile": "overview",
      "prepare_window": None,
      "outputs": [
        ("track-overview.png", False),
      ],
    },
    {
      "profile": "recorded-points",
      "prepare_window": None,
      "outputs": [
        ("track-recorded-points.png", False),
      ],
    },
    {
      "profile": "interval-markers",
      "prepare_window": None,
      "outputs": [
        ("track-interval-markers.png", False),
      ],
    },
    {
      "profile": "combined-overlays",
      "prepare_window": None,
      "outputs": [
        ("track-combined-overlays.png", False),
      ],
    },
    {
      "profile": "overview",
      "prepare_window": _prepare_time_slider_midpoint,
      "outputs": [
        ("track-time-slider-midpoint.png", False),
        ("track-metadata-panel.png", True),
      ],
    },
    {
      "profile": "overview",
      "prepare_window": _prepare_segments_after_split,
      "outputs": [
        ("track-segments-after-split.png", False),
      ],
    },
  ]

  return screenshot_jobs


def _resolve_repository_root():
  """Return the repository root containing pyproject.toml."""

  script_directory = os.path.dirname(os.path.abspath(__file__))
  repository_root = os.path.dirname(script_directory)

  return repository_root


def main(argv=None):
  """Capture the standard documentation screenshot set for the sample GPX file."""

  logging.basicConfig(level=logging.INFO)

  argument_parser = argparse.ArgumentParser(
    description="Capture GIS Graphical Editor documentation screenshots.",
  )
  argument_parser.add_argument(
    "--gpx-path",
    metavar="PATH",
    help="GPX file to load (defaults to the Key West AutoLog sample in the repo root).",
  )
  argument_parser.add_argument(
    "--output-directory",
    metavar="DIR",
    default=_OUTPUT_DIRECTORY,
    help="Directory for PNG output (default: asset/documentation/image).",
  )

  if argv is None:
    arguments = argument_parser.parse_args()
  else:
    arguments = argument_parser.parse_args(argv)

  repository_root = _resolve_repository_root()

  if arguments.gpx_path is None:
    gpx_path = os.path.join(repository_root, _DEFAULT_GPX_FILENAME)
  else:
    gpx_path = arguments.gpx_path

  if not os.path.isfile(gpx_path):
    message = "GPX file not found: {path}".format(path=gpx_path)
    _LOGGER.error(message)

    return 1

  output_directory = arguments.output_directory

  if not os.path.isabs(output_directory):
    output_directory = os.path.join(repository_root, output_directory)

  screenshot_jobs = _build_screenshot_jobs()

  for screenshot_job in screenshot_jobs:
    _capture_screenshot_job(gpx_path, output_directory, screenshot_job)

  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
