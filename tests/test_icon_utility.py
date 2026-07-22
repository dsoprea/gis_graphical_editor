"""Tests for SVG asset icon loading."""

import os

import tkinter

import gis_graphical_editor.icon_utility


def test_get_asset_icon_filepath_resolves_hide_svg():
  hide_icon_filepath = gis_graphical_editor.icon_utility.get_asset_icon_filepath("hide.svg")

  assert hide_icon_filepath.endswith(os.path.join("asset", "icon", "hide.svg"))
  assert os.path.isfile(hide_icon_filepath)


def test_create_drawer_handle_icons_load_hide_svg():
  root = tkinter.Tk()
  root.withdraw()
  hide_handle_icon = \
    gis_graphical_editor.icon_utility.create_drawer_hide_handle_icon(root)
  show_handle_icon = \
    gis_graphical_editor.icon_utility.create_drawer_show_handle_icon(root)
  root.destroy()

  assert hide_handle_icon.width() == gis_graphical_editor.icon_utility._DEFAULT_ICON_PIXEL_SIZE
  assert show_handle_icon.width() == gis_graphical_editor.icon_utility._DEFAULT_ICON_PIXEL_SIZE
  assert str(hide_handle_icon) != str(show_handle_icon)


def test_create_drawer_handle_icons_use_black_foreground():
  hide_icon_filepath = gis_graphical_editor.icon_utility.get_asset_icon_filepath("hide.svg")
  black_svg_text = gis_graphical_editor.icon_utility._read_svg_text_with_foreground_color(
    hide_icon_filepath,
    "#000000",
  )

  assert 'fill="#000000"' in black_svg_text
  assert 'fill="#e3e3e3"' not in black_svg_text
