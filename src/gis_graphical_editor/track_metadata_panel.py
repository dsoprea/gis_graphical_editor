"""Read-only point and segment metadata boxes for the right sidebar."""

import tkinter

_METADATA_BOX_HEIGHT = 8


class TrackMetadataPanel(tkinter.Frame):
  """Stacked point and segment metadata readouts above the segment checklist."""

  def __init__(self, master, panel_width):
    """Build scrollable point and segment metadata boxes at panel_width."""

    super().__init__(master)

    self._build_widgets()

  def set_point_metadata(self, metadata_lines):
    """Replace the point metadata text with metadata_lines joined by newlines."""

    self._set_metadata_text(self._point_metadata_text, metadata_lines)

  def set_segment_metadata(self, metadata_lines):
    """Replace the segment metadata text with metadata_lines joined by newlines."""

    self._set_metadata_text(self._segment_metadata_text, metadata_lines)

  def clear(self):
    """Empty both metadata boxes."""

    self.set_point_metadata([])
    self.set_segment_metadata([])

  def _build_widgets(self):
    """Lay out titled scrollable text boxes for point and segment metadata."""

    point_metadata_frame = tkinter.LabelFrame(self, text="Current Point")
    point_metadata_frame.pack(side=tkinter.TOP, fill=tkinter.X, padx=8, pady=(8, 4))
    self._point_metadata_text = self._build_metadata_text_box(point_metadata_frame)

    segment_metadata_frame = tkinter.LabelFrame(self, text="Current Segment")
    segment_metadata_frame.pack(side=tkinter.TOP, fill=tkinter.X, padx=8, pady=(0, 8))
    self._segment_metadata_text = self._build_metadata_text_box(segment_metadata_frame)

  def _build_metadata_text_box(self, parent_frame):
    """Return a read-only text widget with a vertical scrollbar inside parent_frame."""

    text_container = tkinter.Frame(parent_frame)
    text_container.pack(fill=tkinter.BOTH, expand=True, padx=4, pady=4)

    scrollbar = tkinter.Scrollbar(text_container, orient=tkinter.VERTICAL)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    metadata_text = tkinter.Text(
      text_container,
      height=_METADATA_BOX_HEIGHT,
      wrap=tkinter.WORD,
      yscrollcommand=scrollbar.set,
      state=tkinter.DISABLED,
    )
    metadata_text.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
    scrollbar.config(command=metadata_text.yview)

    return metadata_text

  def _set_metadata_text(self, metadata_text_widget, metadata_lines):
    """Write metadata_lines into one read-only metadata text widget."""

    metadata_text_widget.config(state=tkinter.NORMAL)
    metadata_text_widget.delete("1.0", tkinter.END)

    if metadata_lines:
      metadata_body = "\n".join(metadata_lines)
      metadata_text_widget.insert(tkinter.END, metadata_body)

    metadata_text_widget.config(state=tkinter.DISABLED)
