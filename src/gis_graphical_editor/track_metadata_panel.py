"""Read-only point metadata box for the right sidebar."""

import tkinter
import tkinter.font

_METADATA_BOX_HEIGHT = 8


class TrackMetadataPanel(tkinter.Frame):
  """Point metadata readout above the segment checklist."""

  def __init__(self, master, panel_width):
    """Build a scrollable point metadata box at panel_width."""

    super().__init__(master, width=panel_width)

    # Match the right sidebar frame instead of default white Text backgrounds.
    self._background_color = master.cget("bg")
    self.config(bg=self._background_color)
    self._section_title_font = tkinter.font.Font(self, weight="bold")

    self._build_widgets(panel_width)

  def set_point_metadata(self, metadata_lines):
    """Replace the point metadata text with metadata_lines joined by newlines."""

    self._set_metadata_text(self._point_metadata_text, metadata_lines)

  def clear(self):
    """Empty the point metadata box."""

    self.set_point_metadata([])

  def set_panel_width(self, panel_width):
    """Resize the metadata panel and its text box to panel_width."""

    self.config(width=panel_width)
    metadata_text_width = _compute_metadata_text_width(panel_width)
    self._point_metadata_text.config(width=metadata_text_width)

  def _build_widgets(self, panel_width):
    """Lay out a titled scrollable text box for point metadata."""

    metadata_text_width = _compute_metadata_text_width(panel_width)

    self._point_metadata_text = \
      self._build_metadata_section(
        "Current Point",
        metadata_text_width,
        top_padding=(8, 0),
      )

  def _build_metadata_section(self, section_title, metadata_text_width, top_padding):
    """Return a read-only metadata text widget under a bold section title."""

    section_frame = tkinter.Frame(self, bg=self._background_color, bd=0, relief=tkinter.FLAT)
    section_frame.pack(side=tkinter.TOP, fill=tkinter.X, padx=8, pady=top_padding)

    title_label = tkinter.Label(
      section_frame,
      text=section_title,
      bg=self._background_color,
      font=self._section_title_font,
      anchor=tkinter.W,
    )
    title_label.pack(side=tkinter.TOP, fill=tkinter.X, anchor=tkinter.W)

    return self._build_metadata_text_box(section_frame, metadata_text_width)

  def _build_metadata_text_box(self, parent_frame, metadata_text_width):
    """Return a read-only text widget with a vertical scrollbar inside parent_frame."""

    text_container = tkinter.Frame(
      parent_frame,
      bg=self._background_color,
      bd=0,
      relief=tkinter.FLAT,
    )
    text_container.pack(fill=tkinter.BOTH, expand=True, padx=4, pady=0)

    scrollbar = tkinter.Scrollbar(
      text_container,
      orient=tkinter.VERTICAL,
      bg=self._background_color,
      bd=0,
      highlightthickness=0,
      relief=tkinter.FLAT,
    )
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

    metadata_text = tkinter.Text(
      text_container,
      width=metadata_text_width,
      height=1,
      wrap=tkinter.WORD,
      yscrollcommand=scrollbar.set,
      state=tkinter.DISABLED,
      bg=self._background_color,
      bd=0,
      relief=tkinter.FLAT,
      highlightthickness=0,
      spacing1=0,
      spacing2=0,
      spacing3=0,
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
      line_count = len(metadata_lines)
    else:
      line_count = 1

    if line_count > _METADATA_BOX_HEIGHT:
      display_height = _METADATA_BOX_HEIGHT
    else:
      display_height = line_count

    metadata_text_widget.config(height=display_height, state=tkinter.DISABLED)


def _compute_metadata_text_width(panel_width):
  """Return a Text widget width in characters that fits panel_width."""

  label_font = tkinter.font.Font()
  character_width = label_font.measure("0")

  if character_width <= 0:
    return 20

  # Reserve space for sidebar padding, label frames, scrollbar, and text margins.
  horizontal_padding = 56
  usable_width = panel_width - horizontal_padding
  metadata_text_width = usable_width // character_width

  if metadata_text_width < 10:
    metadata_text_width = 10

  return metadata_text_width
