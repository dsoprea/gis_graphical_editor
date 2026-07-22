"""Load SVG asset icons for Tkinter widgets."""

import io
import os
import re

import cairosvg
import PIL.Image
import PIL.ImageTk


_DEFAULT_ICON_PIXEL_SIZE = 24
_DRAWER_HANDLE_FOREGROUND_COLOR = "#000000"
_HIDE_ICON_FILENAME = "hide.svg"


def get_asset_icon_filepath(icon_filename):
  """Return the absolute path to icon_filename under asset/icon/."""

  package_directory_path = os.path.dirname(os.path.abspath(__file__))
  candidate_icon_directory_paths = [
    os.path.join(package_directory_path, "asset", "icon"),
    os.path.join(package_directory_path, "..", "..", "asset", "icon"),
  ]

  # Resolve hide.svg from the package tree or the repository asset/icon directory.
  for icon_directory_path in candidate_icon_directory_paths:
    icon_filepath = os.path.join(icon_directory_path, icon_filename)

    if os.path.isfile(icon_filepath):
      return icon_filepath

  raise FileNotFoundError(
    "asset icon not found filename={icon_filename}".format(icon_filename=icon_filename),
  )


def _read_svg_text_with_foreground_color(icon_filepath, icon_foreground_color):
  """Return SVG source with the root fill replaced by icon_foreground_color."""

  with open(icon_filepath) as icon_file:
    svg_text = icon_file.read()

  if icon_foreground_color is None:
    return svg_text

  return re.sub(
    r'fill="[^"]*"',
    'fill="{icon_foreground_color}"'.format(icon_foreground_color=icon_foreground_color),
    svg_text,
    count=1,
  )


def create_photo_image_from_svg(
  master,
  icon_filename,
  icon_pixel_size=_DEFAULT_ICON_PIXEL_SIZE,
  flip_horizontally=False,
  icon_foreground_color=None,
):
  """Rasterize an SVG asset icon into a Tk PhotoImage bound to master."""

  icon_filepath = get_asset_icon_filepath(icon_filename)
  svg_text = _read_svg_text_with_foreground_color(icon_filepath, icon_foreground_color)
  png_bytes = cairosvg.svg2png(
    bytestring=svg_text.encode("utf-8"),
    output_width=icon_pixel_size,
    output_height=icon_pixel_size,
  )
  image = PIL.Image.open(io.BytesIO(png_bytes))

  if flip_horizontally:
    image = image.transpose(PIL.Image.FLIP_LEFT_RIGHT)

  photo_image = PIL.ImageTk.PhotoImage(image, master=master)

  return photo_image


def create_drawer_hide_handle_icon(master, icon_pixel_size=_DEFAULT_ICON_PIXEL_SIZE):
  """Return hide.svg for collapsing the right sidebar drawer."""

  return create_photo_image_from_svg(
    master,
    _HIDE_ICON_FILENAME,
    icon_pixel_size=icon_pixel_size,
    flip_horizontally=False,
    icon_foreground_color=_DRAWER_HANDLE_FOREGROUND_COLOR,
  )


def create_drawer_show_handle_icon(master, icon_pixel_size=_DEFAULT_ICON_PIXEL_SIZE):
  """Return hide.svg mirrored horizontally for expanding the drawer."""

  return create_photo_image_from_svg(
    master,
    _HIDE_ICON_FILENAME,
    icon_pixel_size=icon_pixel_size,
    flip_horizontally=True,
    icon_foreground_color=_DRAWER_HANDLE_FOREGROUND_COLOR,
  )
