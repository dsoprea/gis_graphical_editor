"""Tests for the right sidebar drawer."""

import tkinter

import gis_graphical_editor.right_sidebar_drawer


def _build_right_sidebar_drawer():
  """Return a withdrawn root and a drawer for unit tests."""

  root = tkinter.Tk()
  root.withdraw()
  drawer = gis_graphical_editor.right_sidebar_drawer.RightSidebarDrawer(root)
  drawer.pack(side=tkinter.RIGHT, fill=tkinter.Y)
  root.update_idletasks()

  return root, drawer


def test_right_sidebar_drawer_starts_expanded_at_minimum_content_width():
  root, drawer = _build_right_sidebar_drawer()
  root.destroy()

  assert not drawer.is_collapsed()
  assert drawer.get_content_width() == gis_graphical_editor.right_sidebar_drawer._MIN_CONTENT_WIDTH


def test_right_sidebar_drawer_clamps_content_width():
  root, drawer = _build_right_sidebar_drawer()
  drawer.set_content_width(50)
  clamped_width = drawer.get_content_width()
  drawer.set_content_width(5000)
  maximum_width = drawer.get_content_width()
  root.destroy()

  assert clamped_width == gis_graphical_editor.right_sidebar_drawer._MIN_CONTENT_WIDTH
  assert maximum_width == gis_graphical_editor.right_sidebar_drawer._MAX_CONTENT_WIDTH


def test_right_sidebar_drawer_click_handles_toggle_collapsed():
  root, drawer = _build_right_sidebar_drawer()
  drawer.set_content_width(420)
  drawer._collapse_handle_button.invoke()
  collapsed_after_first_click = drawer.is_collapsed()
  drawer._expand_handle_button.invoke()
  collapsed_after_second_click = drawer.is_collapsed()
  root.destroy()

  assert collapsed_after_first_click
  assert not collapsed_after_second_click


def test_right_sidebar_drawer_places_handles_by_expanded_state():
  root, drawer = _build_right_sidebar_drawer()
  drawer.set_content_width(400)
  drawer.mount_collapse_handle_on_content_header()
  root.update_idletasks()
  expanded_collapse_pack_info = drawer._collapse_handle_button.pack_info()
  expanded_collapse_image = drawer._collapse_handle_button.cget("image")
  drawer._collapse_handle_button.invoke()
  root.update_idletasks()
  collapsed_expand_pack_info = drawer._expand_handle_button.pack_info()
  collapsed_expand_image = drawer._expand_handle_button.cget("image")
  root.destroy()

  assert expanded_collapse_pack_info["side"] == "right"
  assert expanded_collapse_pack_info["in"] is drawer._content_header_frame
  assert collapsed_expand_pack_info["side"] == "top"
  assert collapsed_expand_pack_info["in"] is drawer._collapsed_handle_frame
  assert expanded_collapse_image != collapsed_expand_image


def test_right_sidebar_drawer_mounts_collapse_handle_on_supplied_title_row():
  root, drawer = _build_right_sidebar_drawer()
  title_row = tkinter.Frame(root)
  drawer.mount_collapse_handle(title_row)
  collapse_handle_pack_info = drawer._collapse_handle_button.pack_info()
  root.destroy()

  assert collapse_handle_pack_info["side"] == "right"
  assert collapse_handle_pack_info["in"] is title_row
