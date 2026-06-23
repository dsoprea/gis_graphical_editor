"""Right-side panel listing GPX track segments by timestamp span."""

import tkinter
import tkinter.font

import gis_graphical_editor.track_analysis


_CHECKBUTTON_EXTRA_WIDTH = 30
_PANEL_HORIZONTAL_PADDING = 24
_MIN_PANEL_WIDTH = 400


class SegmentListPanel(tkinter.Frame):
  """Scrollable checklist of GPX segment timestamp intervals."""

  def __init__(
    self,
    master,
    segment_summaries,
    on_selection_changed,
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

    panel_width = compute_panel_width(segment_labels)

    super().__init__(master, width=panel_width)

    self._segment_summaries = segment_summaries
    self._on_selection_changed = on_selection_changed
    self._selection_variables = []
    self.pack_propagate(False)
    self._build_widgets(segment_labels)
    self._populate_segment_checkbuttons(segment_labels)

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

  def find_segment_summary_for_gpx_point(self, gpx_point):
    """Return the segment summary that owns gpx_point, if any."""

    return gis_graphical_editor.track_analysis.find_segment_summary_for_gpx_point(
      self._segment_summaries,
      gpx_point,
    )

  def _build_widgets(self, segment_labels):
    """Lay out a titled scrollable frame of segment checkbuttons."""

    title_label = tkinter.Label(self, text="Segments")
    title_label.pack(side=tkinter.TOP, anchor=tkinter.W, padx=8, pady=(8, 4))

    list_container = tkinter.Frame(self)
    list_container.pack(fill=tkinter.BOTH, expand=True, padx=8, pady=(0, 8))

    scrollbar = tkinter.Scrollbar(list_container, orient=tkinter.VERTICAL)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    self._segment_canvas = tkinter.Canvas(
      list_container,
      highlightthickness=0,
      yscrollcommand=scrollbar.set,
    )
    self._segment_canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
    scrollbar.config(command=self._segment_canvas.yview)

    self._segment_checkbox_frame = tkinter.Frame(self._segment_canvas)
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

    for segment_label in segment_labels:
      selection_variable = tkinter.BooleanVar(value=True)
      self._selection_variables.append(selection_variable)
      segment_checkbutton = tkinter.Checkbutton(
        self._segment_checkbox_frame,
        text=segment_label,
        variable=selection_variable,
        anchor=tkinter.W,
        justify=tkinter.LEFT,
        command=self._handle_selection_changed,
      )
      segment_checkbutton.pack(fill=tkinter.X, anchor=tkinter.W)

  def _handle_selection_changed(self):
    """Notify the main window when the visible segment set changes."""

    self._on_selection_changed()


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

  return panel_width
