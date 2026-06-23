"""Small map marker images for GPX point display."""

import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk

_PATH_LINE_WIDTH = 9
_DOT_ICON_SIZE = _PATH_LINE_WIDTH + 2
_GREEN_POINT_FILL = "#00AA00"
_GREEN_POINT_OUTLINE = "#006600"
_ORANGE_INTERVAL_FILL = "#FF8800"
_ORANGE_INTERVAL_OUTLINE = "#FF6600"
_RED_INTERVAL_FILL = "#CC0000"
_RED_INTERVAL_OUTLINE = "#FF0000"


def create_green_point_icon():
  """Return a PhotoImage green dot slightly wider than the path line."""

  return create_dot_icon(_GREEN_POINT_FILL, _GREEN_POINT_OUTLINE)


def create_orange_interval_icon():
  """Return a PhotoImage orange dot slightly wider than the path line."""

  return create_dot_icon(_ORANGE_INTERVAL_FILL, _ORANGE_INTERVAL_OUTLINE)


def create_red_interval_icon():
  """Return a PhotoImage red dot slightly wider than the path line."""

  return create_dot_icon(_RED_INTERVAL_FILL, _RED_INTERVAL_OUTLINE)


def create_dot_icon(fill_color, outline_color):
  image = PIL.Image.new("RGBA", (_DOT_ICON_SIZE, _DOT_ICON_SIZE), (0, 0, 0, 0))
  draw = PIL.ImageDraw.Draw(image)
  draw.ellipse(
    (1, 1, _DOT_ICON_SIZE - 2, _DOT_ICON_SIZE - 2),
    fill=fill_color,
    outline=outline_color,
  )
  photo_image = PIL.ImageTk.PhotoImage(image)

  return photo_image
