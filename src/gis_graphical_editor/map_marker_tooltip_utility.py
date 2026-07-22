"""Hover tooltips for tkintermapview canvas markers."""

import tkinter


class MapMarkerTooltip:
  """Floating label shown while the pointer rests over a map marker."""

  def __init__(self, master):
    """Create a hidden tooltip window bound to master for lifetime."""

    self._master = master
    self._tooltip_window = None
    self._tooltip_label = None

  def show(self, tooltip_text, screen_x, screen_y):
    """Display tooltip_text near the given screen coordinates."""

    if tooltip_text == "":
      return

    if self._tooltip_window is None:
      self._tooltip_window = tkinter.Toplevel(self._master)
      self._tooltip_window.wm_overrideredirect(True)
      self._tooltip_label = tkinter.Label(
        self._tooltip_window,
        text=tooltip_text,
        background="#ffffe0",
        relief=tkinter.SOLID,
        borderwidth=1,
        padx=4,
        pady=2,
      )
      self._tooltip_label.pack()

    self._tooltip_label.config(text=tooltip_text)
    offset_x = 12
    offset_y = 12
    self._tooltip_window.wm_geometry(
      "+{screen_x}+{screen_y}".format(
        screen_x=screen_x + offset_x,
        screen_y=screen_y + offset_y,
      ),
    )
    self._tooltip_window.deiconify()

  def hide(self):
    """Hide the tooltip window when the pointer leaves the marker."""

    if self._tooltip_window is not None:
      self._tooltip_window.withdraw()


def schedule_bind_map_marker_tooltip(root, map_marker, tooltip_text):
  """Attach hover tooltip bindings after tkintermapview draws the marker canvas items."""

  if tooltip_text == "":
    return

  map_marker_tooltip = MapMarkerTooltip(root)

  def try_bind():
    if map_marker.deleted:
      return

    canvas_item_ids = _collect_map_marker_canvas_item_ids(map_marker)

    if not canvas_item_ids:
      root.after(50, try_bind)

      return

    canvas = map_marker.map_widget.canvas

    def show_tooltip(event):
      map_marker_tooltip.show(tooltip_text, event.x_root, event.y_root)

    def hide_tooltip(event):
      map_marker_tooltip.hide()

    for canvas_item_id in canvas_item_ids:
      canvas.tag_bind(canvas_item_id, "<Enter>", show_tooltip)
      canvas.tag_bind(canvas_item_id, "<Leave>", hide_tooltip)

  root.after_idle(try_bind)


def _collect_map_marker_canvas_item_ids(map_marker):
  """Return drawable canvas item ids for one tkintermapview position marker."""

  canvas_item_ids = []

  if map_marker.canvas_icon is not None:
    canvas_item_ids.append(map_marker.canvas_icon)

  if map_marker.canvas_text is not None:
    canvas_item_ids.append(map_marker.canvas_text)

  if map_marker.polygon is not None:
    canvas_item_ids.append(map_marker.polygon)

  if map_marker.big_circle is not None:
    canvas_item_ids.append(map_marker.big_circle)

  return canvas_item_ids
