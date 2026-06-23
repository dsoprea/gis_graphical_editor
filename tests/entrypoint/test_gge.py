"""Tests for the gge CLI entrypoint."""

import gis_graphical_editor.entrypoint.gge


def test_main_rejects_non_positive_mark_hours():
  exit_code = 1

  try:
    gis_graphical_editor.entrypoint.gge.main(["--mark-hours", "0"])
  except SystemExit as error:
    exit_code = error.code

  assert exit_code != 0
