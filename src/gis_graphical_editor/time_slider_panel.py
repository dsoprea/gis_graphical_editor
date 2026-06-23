"""Time slider for selecting a position along a timestamped GPX track."""

import datetime
import tkinter


_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class TimeSliderPanel(tkinter.Frame):
  """Slider row with earliest/latest labels and a centered current-time label."""

  def __init__(self, master, earliest_timestamp, latest_timestamp, on_timestamp_changed):
    super().__init__(master)

    self._earliest_timestamp = earliest_timestamp
    self._latest_timestamp = latest_timestamp
    self._on_timestamp_changed = on_timestamp_changed
    self._earliest_seconds = earliest_timestamp.timestamp()
    self._latest_seconds = latest_timestamp.timestamp()

    self._build_widgets()
    self._time_scale.set(self._earliest_seconds)
    self._handle_scale_change(str(self._earliest_seconds))

  def _build_widgets(self):
    slider_row = tkinter.Frame(self)
    slider_row.pack(fill=tkinter.X, padx=8, pady=(8, 0))

    earliest_label_text = self._format_timestamp(self._earliest_timestamp)
    self._earliest_label = tkinter.Label(slider_row, text=earliest_label_text)
    self._earliest_label.pack(side=tkinter.LEFT)

    self._time_scale = tkinter.Scale(
      slider_row,
      from_=self._earliest_seconds,
      to=self._latest_seconds,
      orient=tkinter.HORIZONTAL,
      showvalue=False,
      command=self._handle_scale_change,
    )
    self._time_scale.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, padx=8)

    latest_label_text = self._format_timestamp(self._latest_timestamp)
    self._latest_label = tkinter.Label(slider_row, text=latest_label_text)
    self._latest_label.pack(side=tkinter.LEFT)

    self._current_time_label = tkinter.Label(self, text="")
    self._current_time_label.pack(pady=(4, 8))

  def _handle_scale_change(self, scale_value):
    selected_seconds = float(scale_value)
    selected_timestamp = datetime.datetime.fromtimestamp(selected_seconds)
    current_label_text = self._format_timestamp(selected_timestamp)

    self._current_time_label.config(text=current_label_text)
    self._on_timestamp_changed(selected_timestamp)

  def _format_timestamp(self, timestamp):
    return timestamp.strftime(_TIMESTAMP_FORMAT)
