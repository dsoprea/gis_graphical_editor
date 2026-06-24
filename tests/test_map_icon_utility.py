"""Tests for map_icon_utility slider button image builders."""

import PIL.Image

import gis_graphical_editor.map_icon_utility


def test_build_forward_play_button_image_uses_requested_dimensions():
  image = gis_graphical_editor.map_icon_utility.build_forward_play_button_image(38, 27)

  assert image.size == (38, 27)


def test_build_reverse_play_button_image_is_horizontally_flipped():
  forward_image = gis_graphical_editor.map_icon_utility.build_forward_play_button_image(38, 27)
  reverse_image = gis_graphical_editor.map_icon_utility.build_reverse_play_button_image(38, 27)
  expected_reverse_image = forward_image.transpose(PIL.Image.FLIP_LEFT_RIGHT)

  assert reverse_image.tobytes() == expected_reverse_image.tobytes()


def test_build_next_step_button_image_is_horizontally_flipped():
  previous_image = gis_graphical_editor.map_icon_utility.build_previous_step_button_image(38, 27)
  next_image = gis_graphical_editor.map_icon_utility.build_next_step_button_image(38, 27)
  expected_next_image = previous_image.transpose(PIL.Image.FLIP_LEFT_RIGHT)

  assert next_image.tobytes() == expected_next_image.tobytes()


def test_compute_slider_button_icon_pixel_size_subtracts_button_chrome():
  icon_width, icon_height = \
    gis_graphical_editor.map_icon_utility.compute_slider_button_icon_pixel_size(44, 33)

  assert icon_width == 38
  assert icon_height == 27
