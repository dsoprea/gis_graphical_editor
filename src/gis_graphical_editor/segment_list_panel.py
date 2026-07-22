"""Right-side panel listing GPX track segments by timestamp span."""

import tkinter
import tkinter.font

import gis_graphical_editor.track_analysis


_CHECKBUTTON_EXTRA_WIDTH = 30
_PANEL_HORIZONTAL_PADDING = 24
_MIN_PANEL_WIDTH = 400
_PANEL_WIDTH_FRACTION = 0.9
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
    self._panel_width = panel_width
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
    label_wraplength = _compute_segment_label_wraplength(panel_width)

    for segment_checkbutton in self._segment_checkbuttons:
      segment_checkbutton.config(wraplength=label_wraplength)

  def set_highlighted_segment_index(self, segment_index):
    """Paint one row darker gray when the slider is on that segment, else light gray."""

    # Reset every row to the default inner-list background.
    for segment_checkbutton in self._segment_checkbuttons:
      segment_checkbutton.config(
        bg=_INNER_LIST_BACKGROUND,
        activebackground=_INNER_LIST_BACKGROUND,
      )

    if segment_index is None:
      return

    if segment_index < 0 or segment_index >= len(self._segment_checkbuttons):
      return

    highlighted_checkbutton = self._segment_checkbuttons[segment_index]
    highlighted_checkbutton.config(
      bg=_CURRENT_SEGMENT_BACKGROUND,
      activebackground=_CURRENT_SEGMENT_BACKGROUND,
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
    canvas_window = self._segment_canvas.create_window(
      (0, 0),
      window=self._segment_checkbox_frame,
      anchor=tkinter.NW,
    )

    def _handle_checkbox_frame_configure(event):
      self._segment_canvas.configure(scrollregion=self._segment_canvas.bbox(tkinter.ALL))

    def _handle_canvas_configure(event):
      self._segment_canvas.itemconfigure(canvas_window, width=event.width)

    self._segment_checkbox_frame.bind("<Configure>", _handle_checkbox_frame_configure)
    self._segment_canvas.bind("<Configure>", _handle_canvas_configure)

  def _populate_segment_checkbuttons(self, segment_labels):
    """Create one checked checkbutton per segment label."""

    label_wraplength = _compute_segment_label_wraplength(self._panel_width)

    for segment_label in segment_labels:
      selection_variable = tkinter.BooleanVar(value=True)
      self._selection_variables.append(selection_variable)
      segment_checkbutton = tkinter.Checkbutton(
        self._segment_checkbox_frame,
        text=segment_label,
        variable=selection_variable,
        anchor=tkinter.W,
        justify=tkinter.LEFT,
        wraplength=label_wraplength,
        bg=_INNER_LIST_BACKGROUND,
        activebackground=_INNER_LIST_BACKGROUND,
        command=self._handle_selection_changed,
      )
      segment_checkbutton.pack(fill=tkinter.X, anchor=tkinter.W)
      self._segment_checkbuttons.append(segment_checkbutton)

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

    highlighted_checkbutton = self._segment_checkbuttons[segment_index]
    self._segment_checkbox_frame.update_idletasks()
    checkbutton_top = highlighted_checkbutton.winfo_y()
    checkbutton_bottom = checkbutton_top + highlighted_checkbutton.winfo_height()
    frame_height = self._segment_checkbox_frame.winfo_height()
    canvas_height = self._segment_canvas.winfo_height()

    if frame_height <= 0 or canvas_height <= 0:
      return

    # Compare the row against the canvas viewport using yview scroll fractions.
    top_scroll_fraction, bottom_scroll_fraction = self._segment_canvas.yview()
    visible_top = top_scroll_fraction * frame_height
    visible_bottom = bottom_scroll_fraction * frame_height

    if checkbutton_top >= visible_top and checkbutton_bottom <= visible_bottom:
      return

    scroll_fraction = checkbutton_top / frame_height

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

  panel_width = widest_label_width + _CHECKBUTTON_EXTRA_WIDTH + _PANEL_HORIZONTAL_PADDING

  if panel_width < _MIN_PANEL_WIDTH:
    panel_width = _MIN_PANEL_WIDTH

  panel_width = int(panel_width * _PANEL_WIDTH_FRACTION)

  return panel_width


def _compute_segment_label_wraplength(panel_width):
  """Return a Checkbutton wraplength that fits panel_width."""

  label_wraplength = panel_width - _CHECKBUTTON_EXTRA_WIDTH - 16

  if label_wraplength < 80:
    label_wraplength = 80

  return label_wraplength
