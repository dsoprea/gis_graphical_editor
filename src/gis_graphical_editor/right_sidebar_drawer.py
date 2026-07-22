"""Right sidebar drawer with a collapse handle inside the panel or on the left edge."""

import tkinter

import gis_graphical_editor.icon_utility


_HANDLE_MARGIN = 4
_HANDLE_ICON_PIXEL_SIZE = 24
_HANDLE_WIDTH = _HANDLE_ICON_PIXEL_SIZE + (2 * _HANDLE_MARGIN) + 4
_MIN_CONTENT_WIDTH = 200
_MAX_CONTENT_WIDTH = 1200
_HANDLE_BACKGROUND = "#d8d8d8"
_HANDLE_ACTIVE_BACKGROUND = "#c0c0c0"
_HANDLE_BORDER_COLOR = "#a0a0a0"


class RightSidebarDrawer(tkinter.Frame):
  """Right-side drawer hosting metadata and segment panels with a collapse handle."""

  def __init__(self, master):
    """Build the handle controls and an empty content frame at the default content width."""

    super().__init__(master)
    self._content_width = _MIN_CONTENT_WIDTH
    self._collapsed = False
    self._collapse_handle_icon = None
    self._expand_handle_icon = None
    self._collapse_handle_button = None
    self.pack_propagate(False)
    self._build_widgets()
    self.mount_collapse_handle_on_content_header()
    self._sync_drawer_geometry()

  def is_collapsed(self):
    """Return True when only the left handle strip is visible."""

    return self._collapsed

  def get_content_width(self):
    """Return the content area width in pixels when the drawer is expanded."""

    return self._content_width

  def set_content_width(self, content_width):
    """Resize the content area to content_width and expand when currently collapsed."""

    self._content_width = _clamp_content_width(content_width)

    if self._collapsed:
      return

    self._sync_drawer_geometry()

  def collapse(self):
    """Hide the content area and show only the left-edge expand handle."""

    if self._collapsed:
      return

    self._collapsed = True
    self._content_outer_frame.grid_remove()
    self._collapsed_handle_frame.grid(row=0, column=0, sticky="ns")
    self._sync_drawer_geometry()

  def expand(self):
    """Show the content area at the last content width."""

    if not self._collapsed:
      return

    self._expand_drawer()

  def toggle_collapsed(self):
    """Collapse the drawer when expanded, or expand it when collapsed."""

    if self._collapsed:
      self.expand()
    else:
      self.collapse()

  def mount_collapse_handle(self, parent_frame):
    """Place the expanded-state collapse handle on the right of parent_frame."""

    if self._content_header_frame is not None:
      self._content_header_frame.pack_forget()

    if self._collapse_handle_button is not None:
      self._collapse_handle_button.destroy()

    self._collapse_handle_button = self._build_handle_button(
      parent_frame,
      self._collapse_handle_icon,
    )
    self._collapse_handle_button.pack(
      side=tkinter.RIGHT,
      padx=_HANDLE_MARGIN,
      pady=0,
    )

  def mount_collapse_handle_on_content_header(self):
    """Place the collapse handle on the drawer content header when metadata is absent."""

    self._content_header_frame.pack(side=tkinter.TOP, fill=tkinter.X)
    self.mount_collapse_handle(self._content_header_frame)

  def _expand_drawer(self):
    """Reveal the content frame and hide the left-edge expand handle."""

    self._collapsed = False
    self._collapsed_handle_frame.grid_remove()
    self._content_outer_frame.grid(row=0, column=0, sticky="ns")
    self._sync_drawer_geometry()

  def _build_widgets(self):
    """Lay out the collapsed-edge handle and the expandable content area."""

    self.grid_columnconfigure(0, weight=0)
    self.grid_rowconfigure(0, weight=1)
    self._collapse_handle_icon = \
      gis_graphical_editor.icon_utility.create_drawer_hide_handle_icon(
        self,
        icon_pixel_size=_HANDLE_ICON_PIXEL_SIZE,
      )
    self._expand_handle_icon = \
      gis_graphical_editor.icon_utility.create_drawer_show_handle_icon(
        self,
        icon_pixel_size=_HANDLE_ICON_PIXEL_SIZE,
      )
    self._collapsed_handle_frame = tkinter.Frame(
      self,
      width=_HANDLE_WIDTH,
      bg=_HANDLE_BACKGROUND,
      highlightthickness=1,
      highlightbackground=_HANDLE_BORDER_COLOR,
    )
    self._collapsed_handle_frame.grid_propagate(False)
    self._expand_handle_button = self._build_handle_button(
      self._collapsed_handle_frame,
      self._expand_handle_icon,
    )
    self._expand_handle_button.pack(
      side=tkinter.TOP,
      padx=_HANDLE_MARGIN,
      pady=_HANDLE_MARGIN,
    )
    self._collapsed_handle_frame.grid_remove()
    self._content_outer_frame = tkinter.Frame(self)
    self._content_outer_frame.grid(row=0, column=0, sticky="ns")
    self._content_outer_frame.grid_propagate(False)
    self.content_frame = tkinter.Frame(self._content_outer_frame)
    self.content_frame.pack(fill=tkinter.BOTH, expand=True)
    self._content_header_frame = tkinter.Frame(self.content_frame)

  def _build_handle_button(self, parent_frame, handle_icon):
    """Return a compact image button wired to toggle_collapsed."""

    handle_button = tkinter.Button(
      parent_frame,
      image=handle_icon,
      relief=tkinter.RAISED,
      bd=1,
      highlightthickness=0,
      bg=_HANDLE_BACKGROUND,
      activebackground=_HANDLE_ACTIVE_BACKGROUND,
      cursor="hand2",
      command=self.toggle_collapsed,
    )
    handle_button.image = handle_icon

    return handle_button

  def _sync_drawer_geometry(self):
    """Apply the current collapsed state and content width to child widgets."""

    if self._collapsed:
      drawer_width = _HANDLE_WIDTH
    else:
      drawer_width = self._content_width
      self._content_outer_frame.config(width=self._content_width)
      self.content_frame.config(width=self._content_width)

    self.config(width=drawer_width)


def _clamp_content_width(content_width):
  """Return content_width limited to the drawer minimum and maximum."""

  if content_width < _MIN_CONTENT_WIDTH:
    return _MIN_CONTENT_WIDTH

  if content_width > _MAX_CONTENT_WIDTH:
    return _MAX_CONTENT_WIDTH

  return content_width
