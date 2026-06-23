"""Time slider for selecting a position along a timestamped GPX track."""

import datetime
import tkinter


_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIMESTAMP_WITH_DAY_OF_WEEK_FORMAT = "%A %Y-%m-%d %H:%M:%S"
_TIME_ONLY_FORMAT = "%H:%M:%S"


def format_timezone_label(timestamp):
  """Return a short timezone label for slider endpoint timestamps."""

  if timestamp.tzinfo is None:
    return ""

  timezone_name = timestamp.tzname()

  if timezone_name is not None and timezone_name != "":
    return timezone_name

  utc_offset = timestamp.utcoffset()

  if utc_offset is None:
    return ""

  # Format fixed offsets as UTC±HH:MM when tzname is unavailable.
  total_seconds = int(utc_offset.total_seconds())
  offset_sign = "+"

  if total_seconds < 0:
    offset_sign = "-"
    total_seconds = abs(total_seconds)

  offset_hours = total_seconds // 3600
  offset_minutes = (total_seconds % 3600) // 60

  return "UTC{offset_sign}{offset_hours:02d}:{offset_minutes:02d}".format(
    offset_sign=offset_sign,
    offset_hours=offset_hours,
    offset_minutes=offset_minutes,
  )


def format_display_timestamp(timestamp, include_date=False, include_day_of_week=False):
  """Return a wall-clock string with optional date for interval marker labels."""

  if include_day_of_week:
    timestamp_format = _TIMESTAMP_WITH_DAY_OF_WEEK_FORMAT
  elif include_date:
    timestamp_format = _TIMESTAMP_FORMAT
  else:
    timestamp_format = _TIME_ONLY_FORMAT

  return timestamp.strftime(timestamp_format)


def format_slider_endpoint_timestamp(timestamp):
  """Return a wall-clock string with timezone for the slider edge labels."""

  timestamp_text = format_display_timestamp(timestamp, include_date=True)
  timezone_label = format_timezone_label(timestamp)

  if timezone_label == "":
    return timestamp_text

  return "{timestamp_text} {timezone_label}".format(
    timestamp_text=timestamp_text,
    timezone_label=timezone_label,
  )


class TimeSliderPanel(tkinter.Frame):
  """Slider row with earliest/latest labels and a centered current-time label."""

  def __init__(self, master, earliest_timestamp, latest_timestamp, on_timestamp_changed):
    """Build the slider UI and invoke on_timestamp_changed as the user scrubs."""

    super().__init__(master)

    self._earliest_timestamp = earliest_timestamp
    self._latest_timestamp = latest_timestamp
    self._on_timestamp_changed = on_timestamp_changed
    self._reference_timezone = earliest_timestamp.tzinfo
    self._earliest_seconds = earliest_timestamp.timestamp()
    self._latest_seconds = latest_timestamp.timestamp()

    self._build_widgets()
    self._time_scale.set(self._earliest_seconds)
    self._handle_scale_change(str(self._earliest_seconds))

  def _build_widgets(self):
    """Lay out endpoint labels, the scale control, and the current-time label."""

    slider_row = tkinter.Frame(self)
    slider_row.pack(fill=tkinter.X, padx=8, pady=(8, 0))

    earliest_label_text = format_slider_endpoint_timestamp(self._earliest_timestamp)
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

    latest_label_text = format_slider_endpoint_timestamp(self._latest_timestamp)
    self._latest_label = tkinter.Label(slider_row, text=latest_label_text)
    self._latest_label.pack(side=tkinter.LEFT)

    self._current_time_label = tkinter.Label(self, text="")
    self._current_time_label.pack(pady=(4, 8))

  def _build_selected_timestamp(self, selected_seconds):
    """Convert slider epoch seconds back into a datetime with track timezone."""

    if self._reference_timezone is not None:
      return datetime.datetime.fromtimestamp(selected_seconds, tz=self._reference_timezone)

    return datetime.datetime.fromtimestamp(selected_seconds)

  def _handle_scale_change(self, scale_value):
    """Update the centered label and notify the map of the selected timestamp."""

    selected_seconds = float(scale_value)
    selected_timestamp = self._build_selected_timestamp(selected_seconds)
    current_label_text = format_slider_endpoint_timestamp(selected_timestamp)

    self._current_time_label.config(text=current_label_text)
    self._on_timestamp_changed(selected_timestamp)
