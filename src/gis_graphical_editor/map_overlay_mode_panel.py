"""Overlay mode buttons and status labels on the map column."""

import tkinter

_OVERLAY_BUTTON_X = 20
_OVERLAY_TOGGLE_BUTTON_WIDTH = 12
_OVERLAY_SECONDARY_BUTTON_WIDTH = 14
_OVERLAY_TOGGLE_BUTTON_BACKGROUND = "#0066CC"
_OVERLAY_TOGGLE_BUTTON_FOREGROUND = "#FFFFFF"
_OVERLAY_TOGGLE_BUTTON_ACTIVE_BACKGROUND = "#0052A3"
_OVERLAY_STATUS_LABEL_FONT = ("Tahoma", 16, "bold")
_OVERLAY_STATUS_LABEL_COLOR = "#FF8800"
_OVERLAY_STATUS_LABEL_Y = 10
_OVERLAY_STATUS_LABEL_X_OFFSET = 10
_OVERLAY_SELECTED_LOCATIONS_LABEL_Y_OFFSET = 30
_OVERLAY_TOGGLE_ENTER_LABEL = "Enter\nOverlay Mode"
_OVERLAY_TOGGLE_EXIT_LABEL = "Exit\nOverlay Mode"


def compute_map_top_left_button_stack_gap_pixels(map_widget):
  """Return the vertical gap between stacked top-left map controls."""

  zoom_in_button = map_widget.button_zoom_in
  zoom_out_button = map_widget.button_zoom_out

  return (
    zoom_out_button.canvas_position[1]
    - zoom_in_button.canvas_position[1]
    - zoom_in_button.height
  )


def compute_first_overlay_button_y(map_widget):
  """Return the Y coordinate for the first overlay button below the zoom-out control."""

  zoom_out_button = map_widget.button_zoom_out
  stack_gap_pixels = compute_map_top_left_button_stack_gap_pixels(map_widget)

  return (
    zoom_out_button.canvas_position[1]
    + zoom_out_button.height
    + stack_gap_pixels
  )


class MapOverlayModePanel:
  """Overlay mode controls placed over the map widget below the zoom buttons."""

  def __init__(
    self,
    map_widget,
    on_toggle_overlay_mode,
    on_push_overlay,
    on_clear_overlays,
  ):
    """Create overlay buttons and status labels with the supplied callbacks."""

    self._map_widget = map_widget
    self._on_toggle_overlay_mode = on_toggle_overlay_mode
    self._on_push_overlay = on_push_overlay
    self._on_clear_overlays = on_clear_overlays
    self._overlay_mode_active = False
    self._map_top_left_button_stack_gap_pixels = \
      compute_map_top_left_button_stack_gap_pixels(map_widget)
    self._overlay_toggle_button_y = compute_first_overlay_button_y(map_widget)
    self._toggle_overlay_mode_button = tkinter.Button(
      map_widget,
      text=_OVERLAY_TOGGLE_ENTER_LABEL,
      width=_OVERLAY_TOGGLE_BUTTON_WIDTH,
      justify=tkinter.CENTER,
      padx=2,
      command=self._on_toggle_overlay_mode,
      bg=_OVERLAY_TOGGLE_BUTTON_BACKGROUND,
      fg=_OVERLAY_TOGGLE_BUTTON_FOREGROUND,
      activebackground=_OVERLAY_TOGGLE_BUTTON_ACTIVE_BACKGROUND,
      activeforeground=_OVERLAY_TOGGLE_BUTTON_FOREGROUND,
      relief=tkinter.FLAT,
      overrelief=tkinter.FLAT,
      borderwidth=0,
      highlightthickness=0,
    )
    self._toggle_overlay_mode_button.place(
      x=_OVERLAY_BUTTON_X,
      y=self._overlay_toggle_button_y,
    )
    self._push_overlay_button = tkinter.Button(
      map_widget,
      text="Push Overlay",
      width=_OVERLAY_SECONDARY_BUTTON_WIDTH,
      command=self._on_push_overlay,
      state=tkinter.DISABLED,
    )
    self._clear_overlays_button = tkinter.Button(
      map_widget,
      text="Clear Overlays",
      width=_OVERLAY_SECONDARY_BUTTON_WIDTH,
      command=self._on_clear_overlays,
    )
    self._captured_overlays_count_label = tkinter.Label(
      map_widget,
      text="",
      font=_OVERLAY_STATUS_LABEL_FONT,
      fg=_OVERLAY_STATUS_LABEL_COLOR,
      bg=map_widget.cget("bg"),
    )
    self._selected_locations_count_label = tkinter.Label(
      map_widget,
      text="",
      font=_OVERLAY_STATUS_LABEL_FONT,
      fg=_OVERLAY_STATUS_LABEL_COLOR,
      bg=map_widget.cget("bg"),
    )
    map_widget.update_idletasks()
    self._overlay_button_stack_step_pixels = (
      self._toggle_overlay_mode_button.winfo_reqheight()
      + self._map_top_left_button_stack_gap_pixels
    )
    self._refresh_control_visibility()

  def set_overlay_mode_active(self, overlay_mode_active):
    """Remember whether overlay mode is active and refresh button labels."""

    self._overlay_mode_active = overlay_mode_active
    self._refresh_control_visibility()

  def set_pushed_overlay_count(self, pushed_overlay_count):
    """Update the captured-overlays status label when overlay mode is active."""

    if self._overlay_mode_active and pushed_overlay_count >= 0:
      self._captured_overlays_count_label.configure(
        text="{count} Captured Overlays".format(count=pushed_overlay_count),
      )
    else:
      self._captured_overlays_count_label.configure(text="")

    self._refresh_status_label_visibility()

  def set_pending_location_count(self, pending_location_count):
    """Update the selected-locations status label when locations are captured."""

    if self._overlay_mode_active and pending_location_count > 0:
      self._selected_locations_count_label.configure(
        text="{count} Selected Locations".format(count=pending_location_count),
      )
    else:
      self._selected_locations_count_label.configure(text="")

    self._refresh_status_label_visibility()

  def set_push_overlay_enabled(self, push_overlay_enabled):
    """Enable or disable the Push Overlay button."""

    if push_overlay_enabled:
      self._push_overlay_button.configure(state=tkinter.NORMAL)
    else:
      self._push_overlay_button.configure(state=tkinter.DISABLED)

  def set_clear_overlays_visible(self, clear_overlays_visible):
    """Show or hide the Clear Overlays button when overlays remain on the map."""

    if clear_overlays_visible:
      self._clear_overlays_button.place(
        x=_OVERLAY_BUTTON_X,
        y=self._overlay_toggle_button_y + self._overlay_button_stack_step_pixels,
      )
    else:
      self._clear_overlays_button.place_forget()

  def _refresh_control_visibility(self):
    """Place overlay-mode buttons and update the enter/exit toggle label."""

    if self._overlay_mode_active:
      self._toggle_overlay_mode_button.configure(text=_OVERLAY_TOGGLE_EXIT_LABEL)
      self._push_overlay_button.place(
        x=_OVERLAY_BUTTON_X,
        y=self._overlay_toggle_button_y + self._overlay_button_stack_step_pixels,
      )
    else:
      self._toggle_overlay_mode_button.configure(text=_OVERLAY_TOGGLE_ENTER_LABEL)
      self._push_overlay_button.place_forget()
      self._push_overlay_button.configure(state=tkinter.DISABLED)

    self._refresh_status_label_visibility()

  def _refresh_status_label_visibility(self):
    """Show orange status labels only while overlay mode is active."""

    if self._overlay_mode_active:
      self._captured_overlays_count_label.place(
        relx=1.0,
        x=-_OVERLAY_STATUS_LABEL_X_OFFSET,
        y=_OVERLAY_STATUS_LABEL_Y,
        anchor=tkinter.NE,
      )

      if self._selected_locations_count_label.cget("text"):
        self._selected_locations_count_label.place(
          relx=1.0,
          x=-_OVERLAY_STATUS_LABEL_X_OFFSET,
          y=_OVERLAY_STATUS_LABEL_Y + _OVERLAY_SELECTED_LOCATIONS_LABEL_Y_OFFSET,
          anchor=tkinter.NE,
        )
      else:
        self._selected_locations_count_label.place_forget()
    else:
      self._captured_overlays_count_label.place_forget()
      self._selected_locations_count_label.place_forget()
