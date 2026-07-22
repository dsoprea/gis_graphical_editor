"""Right-side panel listing GPX track segments by timestamp span."""

import tkinter
import tkinter.font

import gis_graphical_editor.track_analysis


_CHECKBUTTON_EXTRA_WIDTH = 30
_INFO_BUTTON_EXTRA_WIDTH = 28
_INFO_CANVAS_SIZE = 22
_INFO_CIRCLE_FILL = "#dcdcdc"
_INFO_CIRCLE_OUTLINE = "#c8c8c8"
_INFO_GLYPH_COLOR = "#333333"
_SEGMENT_ROW_BORDER_COLOR = "#c0c0c0"
_SEGMENT_ROW_BORDER_WIDTH = 1
_SEGMENT_INFORMATION_BUTTON_TEXT = "\u2139"
_SEGMENT_INFORMATION_POPUP_TITLE = "Segment Information"
_SEGMENT_INFORMATION_POPUP_TEXT_WIDTH = 56
_LIST_CONTAINER_HORIZONTAL_PADDING = 16
_LIST_SCROLLBAR_WIDTH = 18
_SEGMENT_ROW_HORIZONTAL_PADDING = 8
_PANEL_HORIZONTAL_PADDING = 24
_MIN_PANEL_WIDTH = 400
_INNER_LIST_BACKGROUND = "#f5f5f5"
_CURRENT_SEGMENT_BACKGROUND = "#c8c8c8"


class SegmentListPanel(tkinter.Frame):
  """Scrollable checklist of GPX segment timestamp intervals."""

  def __init__(
    self,
    master,
    segment_summaries,
    on_selection_changed,
    on_split_requested,
    on_delete_requested,
    on_undo_requested,
    panel_width,
    use_metric_units=False,
    exclude_idle_segments=False,
  ):
    """Build a width-fitted checklist with every segment selected by default."""

    segment_labels = []

    for segment_summary in segment_summaries:
      segment_label = \
        gis_graphical_editor.track_analysis.format_track_segment_interval_label(
          segment_summary,
          use_metric_units,
          exclude_idle_segments,
        )
      segment_labels.append(segment_label)

    super().__init__(master, width=panel_width)

    self._segment_summaries = segment_summaries
    self._on_selection_changed = on_selection_changed
    self._on_split_requested = on_split_requested
    self._on_delete_requested = on_delete_requested
    self._on_undo_requested = on_undo_requested
    self._selection_variables = []
    self._segment_checkbuttons = []
    self._segment_row_frames = []
    self._segment_info_canvases = []
    self._segment_checkbox_canvas_window = None
    self._panel_width = panel_width
    self._use_metric_units = use_metric_units
    self._exclude_idle_segments = exclude_idle_segments
    self.pack_propagate(False)
    self._build_widgets(segment_labels)
    self._populate_segment_checkbuttons(segment_labels)
    self._refresh_selection_button_states()

  def get_selected_gpx_points(self):
    """Return flattened GPX points for every checked segment."""

    selected_gpx_points = []

    for segment_index, selection_variable in enumerate(self._selection_variables):
      if not selection_variable.get():
        continue

      segment_summary = self._segment_summaries[segment_index]

      for gpx_point in segment_summary.segment_points:
        selected_gpx_points.append(gpx_point)

    return selected_gpx_points

  def get_checked_segment_indices(self):
    """Return zero-based indices for every checked segment in the checklist."""

    checked_segment_indices = []

    for segment_index, selection_variable in enumerate(self._selection_variables):
      if selection_variable.get():
        checked_segment_indices.append(segment_index)

    return checked_segment_indices

  def get_segment_summaries(self):
    """Return the segment summaries backing this checklist."""

    return self._segment_summaries

  def set_panel_width(self, panel_width):
    """Resize the checklist and rewrap segment labels to panel_width."""

    self._panel_width = panel_width
    self.config(width=panel_width)
    self._sync_segment_row_wraplengths()

  def set_highlighted_segment_index(self, segment_index):
    """Paint one row darker gray when the slider is on that segment, else light gray."""

    # Reset every row to the default inner-list background.
    for segment_row_frame in self._segment_row_frames:
      self._apply_segment_row_background(segment_row_frame, _INNER_LIST_BACKGROUND)

    if segment_index is None:
      return

    if segment_index < 0 or segment_index >= len(self._segment_row_frames):
      return

    highlighted_segment_row_frame = self._segment_row_frames[segment_index]
    self._apply_segment_row_background(
      highlighted_segment_row_frame,
      _CURRENT_SEGMENT_BACKGROUND,
    )
    self._scroll_segment_index_into_view(segment_index)

  def find_segment_summary_for_gpx_point(self, gpx_point):
    """Return the segment summary that owns gpx_point, if any."""

    return gis_graphical_editor.track_analysis.find_segment_summary_for_gpx_point(
      self._segment_summaries,
      gpx_point,
    )

  def set_split_button_enabled(self, enabled):
    """Enable or disable the Split button above the segment checklist."""

    if enabled:
      split_button_state = tkinter.NORMAL
    else:
      split_button_state = tkinter.DISABLED

    self._split_button.config(state=split_button_state)

  def set_delete_button_enabled(self, enabled):
    """Enable or disable the Delete button above the segment checklist."""

    if enabled:
      delete_button_state = tkinter.NORMAL
    else:
      delete_button_state = tkinter.DISABLED

    self._delete_button.config(state=delete_button_state)

  def set_undo_button_enabled(self, enabled):
    """Enable or disable the Undo button above the segment checklist."""

    if enabled:
      undo_button_state = tkinter.NORMAL
    else:
      undo_button_state = tkinter.DISABLED

    self._undo_button.config(state=undo_button_state)

  def collect_unchecked_segment_first_points(self):
    """Return the first point of every segment whose checkbox is currently cleared."""

    unchecked_first_points = []

    for segment_index, selection_variable in enumerate(self._selection_variables):
      if selection_variable.get():
        continue

      segment_summary = self._segment_summaries[segment_index]
      unchecked_first_points.append(segment_summary.segment_points[0])

    return unchecked_first_points

  def apply_unchecked_segment_first_points(self, unchecked_first_points):
    """Uncheck segments whose first point matches one of unchecked_first_points."""

    unchecked_first_point_ids = set()

    for first_point in unchecked_first_points:
      unchecked_first_point_ids.add(id(first_point))

    for segment_index, selection_variable in enumerate(self._selection_variables):
      segment_summary = self._segment_summaries[segment_index]
      first_point_id = id(segment_summary.segment_points[0])

      if first_point_id in unchecked_first_point_ids:
        selection_variable.set(False)

    self._refresh_selection_button_states()

  def _build_widgets(self, segment_labels):
    """Lay out a titled scrollable frame of segment checkbuttons."""

    header_row = tkinter.Frame(self)
    header_row.pack(side=tkinter.TOP, fill=tkinter.X, padx=8, pady=(0, 4))

    title_label = tkinter.Label(header_row, text="Segments")
    title_label.pack(side=tkinter.LEFT)

    self._undo_button = tkinter.Button(
      header_row,
      text="Undo",
      command=self._handle_undo_button_clicked,
      state=tkinter.DISABLED,
    )
    self._undo_button.pack(side=tkinter.RIGHT)

    self._delete_button = tkinter.Button(
      header_row,
      text="Delete",
      command=self._handle_delete_button_clicked,
      state=tkinter.DISABLED,
    )
    self._delete_button.pack(side=tkinter.RIGHT)

    self._split_button = tkinter.Button(
      header_row,
      text="Split",
      command=self._handle_split_button_clicked,
      state=tkinter.DISABLED,
    )
    self._split_button.pack(side=tkinter.RIGHT)

    selection_row = tkinter.Frame(self)
    selection_row.pack(side=tkinter.TOP, fill=tkinter.X, padx=8, pady=(0, 4))

    self._select_none_button = tkinter.Button(
      selection_row,
      text="Select None",
      command=self._handle_select_none_button_clicked,
      state=tkinter.DISABLED,
    )
    self._select_none_button.pack(side=tkinter.RIGHT)

    self._select_all_button = tkinter.Button(
      selection_row,
      text="Select All",
      command=self._handle_select_all_button_clicked,
      state=tkinter.DISABLED,
    )
    self._select_all_button.pack(side=tkinter.RIGHT, padx=(0, 4))

    list_container = tkinter.Frame(self)
    list_container.pack(fill=tkinter.BOTH, expand=True, padx=8, pady=(0, 8))

    scrollbar = tkinter.Scrollbar(list_container, orient=tkinter.VERTICAL)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    self._segment_canvas = tkinter.Canvas(
      list_container,
      highlightthickness=0,
      bg=_INNER_LIST_BACKGROUND,
      yscrollcommand=scrollbar.set,
    )
    self._segment_canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
    scrollbar.config(command=self._segment_canvas.yview)

    self._segment_checkbox_frame = tkinter.Frame(self._segment_canvas, bg=_INNER_LIST_BACKGROUND)
    self._segment_checkbox_canvas_window = self._segment_canvas.create_window(
      (0, 0),
      window=self._segment_checkbox_frame,
      anchor=tkinter.NW,
    )

    def _handle_checkbox_frame_configure(event):
      self._segment_canvas.configure(scrollregion=self._segment_canvas.bbox(tkinter.ALL))

    def _handle_canvas_configure(event):
      self._sync_segment_row_wraplengths(list_canvas_width=event.width)

    self._segment_checkbox_frame.bind("<Configure>", _handle_checkbox_frame_configure)
    self._segment_canvas.bind("<Configure>", _handle_canvas_configure)

  def _populate_segment_checkbuttons(self, segment_labels):
    """Create one checked checkbutton and info icon per segment label."""

    label_wraplength = _compute_segment_label_wraplength(self._panel_width)

    for segment_index, segment_label in enumerate(segment_labels):
      selection_variable = tkinter.BooleanVar(value=True)
      self._selection_variables.append(selection_variable)
      segment_row_outer = tkinter.Frame(
        self._segment_checkbox_frame,
        bg=_SEGMENT_ROW_BORDER_COLOR,
        highlightthickness=0,
        bd=0,
      )
      segment_row_outer.pack(fill=tkinter.X, expand=True, anchor=tkinter.W)
      self._segment_row_frames.append(segment_row_outer)
      segment_row_inner = tkinter.Frame(
        segment_row_outer,
        bg=_INNER_LIST_BACKGROUND,
        highlightthickness=0,
        bd=0,
      )
      segment_row_inner.pack(
        fill=tkinter.X,
        expand=True,
        padx=(_SEGMENT_ROW_BORDER_WIDTH, 0),
        pady=(_SEGMENT_ROW_BORDER_WIDTH, _SEGMENT_ROW_BORDER_WIDTH),
      )
      segment_checkbutton = tkinter.Checkbutton(
        segment_row_inner,
        text=segment_label,
        variable=selection_variable,
        anchor=tkinter.W,
        justify=tkinter.LEFT,
        wraplength=label_wraplength,
        bg=_INNER_LIST_BACKGROUND,
        activebackground=_INNER_LIST_BACKGROUND,
        highlightthickness=0,
        bd=0,
        command=self._handle_selection_changed,
      )
      segment_checkbutton.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, anchor=tkinter.W)
      self._segment_checkbuttons.append(segment_checkbutton)
      segment_info_canvas = self._create_segment_information_canvas(
        segment_row_inner,
        segment_index,
        _INNER_LIST_BACKGROUND,
      )
      segment_info_canvas.pack(side=tkinter.RIGHT, anchor=tkinter.E, padx=(4, 2))
      self._segment_info_canvases.append(segment_info_canvas)

    self._sync_segment_row_wraplengths()

  def _create_segment_information_canvas(self, segment_row_frame, segment_index, background_color):
    """Return a canvas with a circular info glyph that opens the segment popup."""

    info_canvas = tkinter.Canvas(
      segment_row_frame,
      width=_INFO_CANVAS_SIZE,
      height=_INFO_CANVAS_SIZE,
      highlightthickness=0,
      bd=0,
      bg=background_color,
      cursor="hand2",
    )
    circle_margin = 2
    info_canvas.create_oval(
      circle_margin,
      circle_margin,
      _INFO_CANVAS_SIZE - circle_margin,
      _INFO_CANVAS_SIZE - circle_margin,
      fill=_INFO_CIRCLE_FILL,
      outline=_INFO_CIRCLE_OUTLINE,
      width=1,
    )
    info_canvas.create_text(
      _INFO_CANVAS_SIZE / 2,
      _INFO_CANVAS_SIZE / 2,
      text=_SEGMENT_INFORMATION_BUTTON_TEXT,
      fill=_INFO_GLYPH_COLOR,
    )
    info_canvas.bind(
      "<Button-1>",
      self._build_segment_information_canvas_click_handler(segment_index),
    )

    return info_canvas

  def _build_segment_information_canvas_click_handler(self, segment_index):
    """Return a canvas click handler that opens the metadata popup for segment_index."""

    def handle_segment_information_canvas_clicked(event):
      self._show_segment_information_popup(segment_index)

    return handle_segment_information_canvas_clicked

  def _show_segment_information_popup(self, segment_index):
    """Display segment summary metadata in a popup for one checklist row."""

    segment_summary = self._segment_summaries[segment_index]
    metadata_lines = \
      gis_graphical_editor.track_analysis.format_segment_summary_metadata_lines(
        segment_summary,
        self._use_metric_units,
      )
    popup_window = tkinter.Toplevel(self.winfo_toplevel())
    popup_window.title(_SEGMENT_INFORMATION_POPUP_TITLE)
    popup_window.transient(self.winfo_toplevel())
    popup_body = "\n".join(metadata_lines)
    metadata_text = tkinter.Text(
      popup_window,
      wrap=tkinter.WORD,
      height=min(len(metadata_lines), 12),
      width=_SEGMENT_INFORMATION_POPUP_TEXT_WIDTH,
    )
    metadata_text.insert(tkinter.END, popup_body)
    metadata_text.config(state=tkinter.DISABLED)
    metadata_text.pack(padx=8, pady=8)
    close_button = tkinter.Button(
      popup_window,
      text="Close",
      command=popup_window.destroy,
      default=tkinter.ACTIVE,
    )
    close_button.pack(pady=(0, 8))
    popup_window.bind("<Return>", lambda event: popup_window.destroy())
    popup_window.bind("<Escape>", lambda event: popup_window.destroy())

    def focus_close_button():
      popup_window.lift()
      popup_window.grab_set()
      popup_window.focus_force()
      close_button.focus_set()
      close_button.focus_force()

    popup_window.update_idletasks()
    popup_window.wait_visibility()
    popup_window.after_idle(focus_close_button)

  def _apply_segment_row_background(self, segment_row_outer, background_color):
    """Set one segment row inner fill and its child widgets to background_color."""

    for child_widget in segment_row_outer.winfo_children():
      widget_class_name = child_widget.winfo_class()

      if widget_class_name != "Frame":
        continue

      child_widget.config(bg=background_color)

      for nested_widget in child_widget.winfo_children():
        nested_widget_class_name = nested_widget.winfo_class()

        if nested_widget_class_name == "Checkbutton":
          nested_widget.config(
            bg=background_color,
            activebackground=background_color,
          )
        elif nested_widget_class_name == "Canvas":
          nested_widget.config(bg=background_color)

  def _sync_segment_row_wraplengths(self, list_canvas_width=None):
    """Resize the embedded list frame and rewrap labels to the canvas width."""

    if list_canvas_width is None:
      list_canvas_width = self._segment_canvas.winfo_width()

    if list_canvas_width <= 1:
      list_canvas_width = _compute_fallback_list_canvas_width(self._panel_width)

    if self._segment_checkbox_canvas_window is not None:
      self._segment_canvas.itemconfigure(
        self._segment_checkbox_canvas_window,
        width=list_canvas_width,
      )

    label_wraplength = _compute_segment_label_wraplength_for_list_canvas_width(list_canvas_width)

    for segment_checkbutton in self._segment_checkbuttons:
      segment_checkbutton.config(wraplength=label_wraplength)

  def _handle_selection_changed(self):
    """Notify the main window when the visible segment set changes."""

    self._refresh_selection_button_states()
    self._on_selection_changed()

  def _handle_select_all_button_clicked(self):
    """Check every segment checkbox and refresh the visible track."""

    for selection_variable in self._selection_variables:
      selection_variable.set(True)

    self._refresh_selection_button_states()
    self._on_selection_changed()

  def _handle_select_none_button_clicked(self):
    """Clear every segment checkbox and refresh the visible track."""

    for selection_variable in self._selection_variables:
      selection_variable.set(False)

    self._refresh_selection_button_states()
    self._on_selection_changed()

  def _refresh_selection_button_states(self):
    """Enable Select All only when some segments are unchecked, and the reverse."""

    has_checked_segment = False
    has_unchecked_segment = False

    for selection_variable in self._selection_variables:
      if selection_variable.get():
        has_checked_segment = True
      else:
        has_unchecked_segment = True

    if has_unchecked_segment:
      select_all_button_state = tkinter.NORMAL
    else:
      select_all_button_state = tkinter.DISABLED

    if has_checked_segment:
      select_none_button_state = tkinter.NORMAL
    else:
      select_none_button_state = tkinter.DISABLED

    self._select_all_button.config(state=select_all_button_state)
    self._select_none_button.config(state=select_none_button_state)

  def _handle_split_button_clicked(self):
    """Notify the main window when the user requests a segment split."""

    self._on_split_requested()

  def _handle_delete_button_clicked(self):
    """Notify the main window when the user requests a segment delete."""

    self._on_delete_requested()

  def _handle_undo_button_clicked(self):
    """Notify the main window when the user requests a segment edit undo."""

    self._on_undo_requested()

  def _scroll_segment_index_into_view(self, segment_index):
    """Scroll the checklist canvas so the highlighted segment row is visible."""

    highlighted_segment_row_frame = self._segment_row_frames[segment_index]
    self._segment_checkbox_frame.update_idletasks()
    row_top = highlighted_segment_row_frame.winfo_y()
    row_bottom = row_top + highlighted_segment_row_frame.winfo_height()
    frame_height = self._segment_checkbox_frame.winfo_height()
    canvas_height = self._segment_canvas.winfo_height()

    if frame_height <= 0 or canvas_height <= 0:
      return

    # Compare the row against the canvas viewport using yview scroll fractions.
    top_scroll_fraction, bottom_scroll_fraction = self._segment_canvas.yview()
    visible_top = top_scroll_fraction * frame_height
    visible_bottom = bottom_scroll_fraction * frame_height

    if row_top >= visible_top and row_bottom <= visible_bottom:
      return

    scroll_fraction = row_top / frame_height

    if scroll_fraction < 0:
      scroll_fraction = 0

    if scroll_fraction > 1:
      scroll_fraction = 1

    self._segment_canvas.yview_moveto(scroll_fraction)


def compute_panel_width(segment_labels):
  """Return a panel width wide enough for the longest segment label."""

  label_font = tkinter.font.Font()
  widest_label_width = 0

  for segment_label in segment_labels:
    label_lines = segment_label.split("\n")

    for label_line in label_lines:
      label_width = label_font.measure(label_line)

      if label_width > widest_label_width:
        widest_label_width = label_width

  panel_width = \
    widest_label_width \
    + _CHECKBUTTON_EXTRA_WIDTH \
    + _INFO_BUTTON_EXTRA_WIDTH \
    + _SEGMENT_ROW_BORDER_WIDTH \
    + _SEGMENT_ROW_HORIZONTAL_PADDING \
    + _LIST_CONTAINER_HORIZONTAL_PADDING \
    + _LIST_SCROLLBAR_WIDTH \
    + _PANEL_HORIZONTAL_PADDING

  if panel_width < _MIN_PANEL_WIDTH:
    panel_width = _MIN_PANEL_WIDTH

  return panel_width


def _compute_fallback_list_canvas_width(panel_width):
  """Return the list canvas width implied by panel_width before the canvas is mapped."""

  list_canvas_width = \
    panel_width \
    - _LIST_CONTAINER_HORIZONTAL_PADDING \
    - _LIST_SCROLLBAR_WIDTH

  if list_canvas_width < 80:
    list_canvas_width = 80

  return list_canvas_width


def _compute_segment_label_wraplength_for_list_canvas_width(list_canvas_width):
  """Return a Checkbutton wraplength that fits list_canvas_width."""

  label_wraplength = \
    list_canvas_width \
    - _CHECKBUTTON_EXTRA_WIDTH \
    - _INFO_BUTTON_EXTRA_WIDTH \
    - _SEGMENT_ROW_BORDER_WIDTH \
    - _SEGMENT_ROW_HORIZONTAL_PADDING

  if label_wraplength < 80:
    label_wraplength = 80

  return label_wraplength


def _compute_segment_label_wraplength(panel_width):
  """Return a Checkbutton wraplength that fits panel_width."""

  list_canvas_width = _compute_fallback_list_canvas_width(panel_width)

  return _compute_segment_label_wraplength_for_list_canvas_width(list_canvas_width)
