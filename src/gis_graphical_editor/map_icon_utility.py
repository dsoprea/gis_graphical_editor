"""Small map marker images for GPX point display."""

import math

import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk
import tkinter

_PATH_LINE_WIDTH = 9
_DOT_ICON_SIZE = _PATH_LINE_WIDTH + 2
_GREEN_POINT_FILL = "#00AA00"
_GREEN_POINT_OUTLINE = "#006600"
_ORANGE_INTERVAL_FILL = "#FF8800"
_ORANGE_INTERVAL_OUTLINE = "#FF6600"
_RED_INTERVAL_FILL = "#CC0000"
_RED_INTERVAL_OUTLINE = "#FF0000"
_SLIDER_POINTER_ICON_SIZE = 18
_SLIDER_POINTER_FILL = "#CC0000"
_SLIDER_POINTER_OUTLINE = "#990000"
_SLIDER_BUTTON_ICON_FILL = "#000000"
_SLIDER_BUTTON_CHARACTER_WIDTH = 2
_SLIDER_BUTTON_BORDER_PADDING_PIXELS = 6
_SLIDER_BUTTON_PROBE_TEXT = ">"
_STAR_WAYPOINT_ICON_SIZE = 16
_STAR_WAYPOINT_FILL = "#FFD700"
_STAR_WAYPOINT_OUTLINE = "#CC9900"


def create_green_point_icon():
  """Return a PhotoImage green dot slightly wider than the path line."""

  return create_dot_icon(_GREEN_POINT_FILL, _GREEN_POINT_OUTLINE)


def create_orange_interval_icon():
  """Return a PhotoImage orange dot slightly wider than the path line."""

  return create_dot_icon(_ORANGE_INTERVAL_FILL, _ORANGE_INTERVAL_OUTLINE)


def create_red_interval_icon():
  """Return a PhotoImage red dot slightly wider than the path line."""

  return create_dot_icon(_RED_INTERVAL_FILL, _RED_INTERVAL_OUTLINE)


def create_star_waypoint_icon():
  """Return a PhotoImage five-point star for GPX waypoint markers."""

  image = build_star_waypoint_image()
  photo_image = PIL.ImageTk.PhotoImage(image)

  return photo_image


def build_star_waypoint_image():
  """Return a PIL image with a five-point star for GPX waypoint markers."""

  image = PIL.Image.new("RGBA", (_STAR_WAYPOINT_ICON_SIZE, _STAR_WAYPOINT_ICON_SIZE), (0, 0, 0, 0))
  draw = PIL.ImageDraw.Draw(image)
  center_x = _STAR_WAYPOINT_ICON_SIZE / 2.0
  center_y = _STAR_WAYPOINT_ICON_SIZE / 2.0
  outer_radius = (_STAR_WAYPOINT_ICON_SIZE / 2.0) - 1.0
  inner_radius = outer_radius * 0.45
  star_points = []

  # Build alternating outer and inner vertices for a five-point star.
  for point_index in range(10):
    angle_radians = math.radians(-90 + point_index * 36)

    if point_index % 2 == 0:
      radius = outer_radius
    else:
      radius = inner_radius

    point_x = center_x + radius * math.cos(angle_radians)
    point_y = center_y + radius * math.sin(angle_radians)
    star_points.append((point_x, point_y))

  draw.polygon(
    star_points,
    fill=_STAR_WAYPOINT_FILL,
    outline=_STAR_WAYPOINT_OUTLINE,
  )

  return image


def create_red_slider_pointer_icon():
  """Return a larger PhotoImage red dot for the time-slider position."""

  # Draw a larger filled circle so the slider pointer stands out on the track.
  image = PIL.Image.new("RGBA", (_SLIDER_POINTER_ICON_SIZE, _SLIDER_POINTER_ICON_SIZE), (0, 0, 0, 0))
  draw = PIL.ImageDraw.Draw(image)
  draw.ellipse(
    (1, 1, _SLIDER_POINTER_ICON_SIZE - 2, _SLIDER_POINTER_ICON_SIZE - 2),
    fill=_SLIDER_POINTER_FILL,
    outline=_SLIDER_POINTER_OUTLINE,
  )
  photo_image = PIL.ImageTk.PhotoImage(image)

  return photo_image


def create_dot_icon(fill_color, outline_color):
  """Return a transparent PhotoImage with a filled ellipse for map marker icons."""

  image = PIL.Image.new("RGBA", (_DOT_ICON_SIZE, _DOT_ICON_SIZE), (0, 0, 0, 0))
  draw = PIL.ImageDraw.Draw(image)
  draw.ellipse(
    (1, 1, _DOT_ICON_SIZE - 2, _DOT_ICON_SIZE - 2),
    fill=fill_color,
    outline=outline_color,
  )
  photo_image = PIL.ImageTk.PhotoImage(image)

  return photo_image


def measure_slider_button_pixel_size(master):
  """Return the requested pixel width and height of a width=2 slider button."""

  probe_button = tkinter.Button(master, text=_SLIDER_BUTTON_PROBE_TEXT, width=_SLIDER_BUTTON_CHARACTER_WIDTH)
  probe_button.update_idletasks()
  button_width = probe_button.winfo_reqwidth()
  button_height = probe_button.winfo_reqheight()
  probe_button.destroy()

  return button_width, button_height


def compute_slider_button_icon_pixel_size(slider_button_width, slider_button_height):
  """Return icon width and height that fill a slider button after Tk button chrome."""

  icon_width = slider_button_width - _SLIDER_BUTTON_BORDER_PADDING_PIXELS
  icon_height = slider_button_height - _SLIDER_BUTTON_BORDER_PADDING_PIXELS

  if icon_width < 8:
    icon_width = 8

  if icon_height < 8:
    icon_height = 8

  return icon_width, icon_height


def _create_slider_button_photo_image(master, image):
  """Wrap a PIL slider-button image as a PhotoImage bound to master."""

  photo_image = PIL.ImageTk.PhotoImage(image, master=master)

  return photo_image


def build_forward_play_button_image(icon_width, icon_height):
  """Return a PIL image with a single right-pointing play triangle for forward play."""

  image = PIL.Image.new(
    "RGBA",
    (icon_width, icon_height),
    (0, 0, 0, 0),
  )
  draw = PIL.ImageDraw.Draw(image)
  margin = 2
  top_y = margin
  bottom_y = icon_height - margin - 1
  base_x = margin
  apex_x = icon_width - margin - 1

  # Draw a classic right-pointing play triangle that fills the icon canvas.
  draw.polygon(
    (
      (base_x, top_y),
      (base_x, bottom_y),
      (apex_x, (top_y + bottom_y) // 2),
    ),
    fill=_SLIDER_BUTTON_ICON_FILL,
  )

  return image


def build_previous_step_button_image(icon_width, icon_height):
  """Return a PIL image with a left-pointing chevron for single-step back."""

  image = PIL.Image.new(
    "RGBA",
    (icon_width, icon_height),
    (0, 0, 0, 0),
  )
  draw = PIL.ImageDraw.Draw(image)
  margin = 2
  center_y = icon_height // 2
  tip_x = margin
  outer_x = icon_width - margin - 1
  top_y = margin
  bottom_y = icon_height - margin - 1
  inner_x = tip_x + (outer_x - tip_x) // 2
  upper_inner_y = top_y + (center_y - top_y) // 2
  lower_inner_y = bottom_y - (center_y - top_y) // 2

  # Draw a filled < chevron for the previous-point step button.
  draw.polygon(
    (
      (tip_x, center_y),
      (outer_x, top_y),
      (outer_x, upper_inner_y),
      (inner_x, center_y),
      (outer_x, lower_inner_y),
      (outer_x, bottom_y),
    ),
    fill=_SLIDER_BUTTON_ICON_FILL,
  )

  return image


def build_next_step_button_image(icon_width, icon_height):
  """Return a right-pointing chevron flipped from the previous-step icon."""

  previous_image = build_previous_step_button_image(icon_width, icon_height)

  return previous_image.transpose(PIL.Image.FLIP_LEFT_RIGHT)


def build_reverse_play_button_image(icon_width, icon_height):
  """Return a left-pointing play triangle flipped from the forward play icon."""

  forward_image = build_forward_play_button_image(icon_width, icon_height)

  return forward_image.transpose(PIL.Image.FLIP_LEFT_RIGHT)


def create_reverse_play_button_icon(master, icon_width, icon_height):
  """Return a PhotoImage with a left-pointing play triangle for reverse play."""

  image = build_reverse_play_button_image(icon_width, icon_height)

  return _create_slider_button_photo_image(master, image)


def create_forward_play_button_icon(master, icon_width, icon_height):
  """Return a PhotoImage with a right-pointing play triangle for forward play."""

  image = build_forward_play_button_image(icon_width, icon_height)

  return _create_slider_button_photo_image(master, image)


def create_previous_step_button_icon(master, icon_width, icon_height):
  """Return a PhotoImage with a left-pointing chevron for the previous-point step."""

  image = build_previous_step_button_image(icon_width, icon_height)

  return _create_slider_button_photo_image(master, image)


def create_next_step_button_icon(master, icon_width, icon_height):
  """Return a PhotoImage with a right-pointing chevron for the next-point step."""

  image = build_next_step_button_image(icon_width, icon_height)

  return _create_slider_button_photo_image(master, image)
