"""Time slider for selecting a position along a timestamped GPX track."""

import datetime
import tkinter

import gis_graphical_editor.track_analysis


_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIMESTAMP_WITH_DAY_OF_WEEK_FORMAT = "%A %Y-%m-%d %H:%M:%S"
_TIME_ONLY_FORMAT = "%H:%M:%S"
_PREVIOUS_POINT_BUTTON_TEXT = "<"
_NEXT_POINT_BUTTON_TEXT = ">"


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


def format_current_slider_position_label(timestamp, point_index, point_count):
  """Return the centered slider label with a one-based point position suffix."""

  timestamp_text = format_slider_endpoint_timestamp(timestamp)
  position_number = point_index + 1

  return "{timestamp_text} ({position_number} of {point_count})".format(
    timestamp_text=timestamp_text,
    position_number=position_number,
    point_count=point_count,
  )


class TimeSliderPanel(tkinter.Frame):
  """Slider row with earliest/latest labels and a centered current-time label."""

  def __init__(
    self,
    master,
    earliest_timestamp,
    latest_timestamp,
    timed_gpx_points,
    on_timestamp_changed,
  ):
    """Build the slider UI and invoke on_timestamp_changed as the user scrubs."""

    super().__init__(master)

    self._earliest_timestamp = earliest_timestamp
    self._latest_timestamp = latest_timestamp
    self._timed_gpx_points = timed_gpx_points
    self._on_timestamp_changed = on_timestamp_changed
    self._reference_timezone = earliest_timestamp.tzinfo
    self._earliest_seconds = earliest_timestamp.timestamp()
    self._latest_seconds = latest_timestamp.timestamp()
    self._current_point_index = 0

    self._build_widgets()
    self._time_scale.set(self._earliest_seconds)
    self._handle_scale_change(str(self._earliest_seconds))

  def _build_widgets(self):
    """Lay out endpoint labels, step buttons, the scale, and the current-time label."""

    slider_row = tkinter.Frame(self)
    slider_row.pack(fill=tkinter.X, padx=8, pady=(8, 0))

    earliest_label_text = format_slider_endpoint_timestamp(self._earliest_timestamp)
    self._earliest_label = tkinter.Label(slider_row, text=earliest_label_text)
    self._earliest_label.pack(side=tkinter.LEFT)

    self._previous_point_button = tkinter.Button(
      slider_row,
      text=_PREVIOUS_POINT_BUTTON_TEXT,
      width=2,
      command=self._handle_previous_point_step,
    )
    self._previous_point_button.pack(side=tkinter.LEFT, padx=(8, 0))

    self._time_scale = tkinter.Scale(
      slider_row,
      from_=self._earliest_seconds,
      to=self._latest_seconds,
      orient=tkinter.HORIZONTAL,
      showvalue=False,
      command=self._handle_scale_change,
    )
    self._time_scale.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, padx=8)

    self._next_point_button = tkinter.Button(
      slider_row,
      text=_NEXT_POINT_BUTTON_TEXT,
      width=2,
      command=self._handle_next_point_step,
    )
    self._next_point_button.pack(side=tkinter.LEFT)

    latest_label_text = format_slider_endpoint_timestamp(self._latest_timestamp)
    self._latest_label = tkinter.Label(slider_row, text=latest_label_text)
    self._latest_label.pack(side=tkinter.LEFT, padx=(8, 0))

    self._current_time_label = tkinter.Label(self, text="")
    self._current_time_label.pack(pady=(4, 8))

  def _build_selected_timestamp(self, selected_seconds):
    """Convert slider epoch seconds back into a datetime with track timezone."""

    if self._reference_timezone is not None:
      return datetime.datetime.fromtimestamp(selected_seconds, tz=self._reference_timezone)

    return datetime.datetime.fromtimestamp(selected_seconds)

  def _handle_previous_point_step(self):
    """Move the slider to the previous timed GPX point."""

    if self._current_point_index <= 0:
      return

    self._select_point_index(self._current_point_index - 1)

  def _handle_next_point_step(self):
    """Move the slider to the next timed GPX point."""

    last_point_index = len(self._timed_gpx_points) - 1

    if self._current_point_index >= last_point_index:
      return

    self._select_point_index(self._current_point_index + 1)

  def _select_point_index(self, point_index):
    """Set the slider to one timed GPX point by index."""

    selected_gpx_point = self._timed_gpx_points[point_index]
    selected_seconds = selected_gpx_point.timestamp.timestamp()
    self._time_scale.set(selected_seconds)

  def _update_step_button_states(self):
    """Disable step buttons at the first and last timed points."""

    last_point_index = len(self._timed_gpx_points) - 1

    if self._current_point_index <= 0:
      previous_button_state = tkinter.DISABLED
    else:
      previous_button_state = tkinter.NORMAL

    if self._current_point_index >= last_point_index:
      next_button_state = tkinter.DISABLED
    else:
      next_button_state = tkinter.NORMAL

    self._previous_point_button.config(state=previous_button_state)
    self._next_point_button.config(state=next_button_state)

  def _handle_scale_change(self, scale_value):
    """Update the centered label and notify the map of the selected timestamp."""

    selected_seconds = float(scale_value)
    selected_timestamp = self._build_selected_timestamp(selected_seconds)
    point_index = \
      gis_graphical_editor.track_analysis.find_timed_gpx_point_index_nearest_timestamp(
        self._timed_gpx_points,
        selected_timestamp,
      )

    if point_index is None:
      point_index = 0

    self._current_point_index = point_index
    current_label_text = format_current_slider_position_label(
      selected_timestamp,
      point_index,
      len(self._timed_gpx_points),
    )

    self._current_time_label.config(text=current_label_text)
    self._update_step_button_states()
    self._on_timestamp_changed(selected_timestamp)
