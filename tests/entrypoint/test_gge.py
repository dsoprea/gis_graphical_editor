"""Tests for the gge CLI entrypoint."""

import gis_graphical_editor.entrypoint.gge


def test_main_rejects_non_positive_mark_hours():
  exit_code = 1

  try:
    gis_graphical_editor.entrypoint.gge.main(["--mark-hours", "0"])
  except SystemExit as error:
    exit_code = error.code

  assert exit_code != 0


def test_parse_iana_timezone_name_accepts_valid_zone():
  timezone_name = gis_graphical_editor.entrypoint.gge._parse_iana_timezone_name("America/Denver")

  assert timezone_name == "America/Denver"


def test_main_rejects_invalid_as_timezone():
  exit_code = 0

  try:
    gis_graphical_editor.entrypoint.gge.main(["--as-timezone", "Not/A/Zone"])
  except SystemExit as error:
    exit_code = error.code

  assert exit_code != 0
