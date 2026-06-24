"""Time slider for selecting a position along a timestamped GPX track."""

import datetime
import tkinter

import gis_graphical_editor.map_icon_utility
import gis_graphical_editor.track_analysis


_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIMESTAMP_WITH_DAY_OF_WEEK_FORMAT = "%A %Y-%m-%d %H:%M:%S"
_TIME_ONLY_FORMAT = "%H:%M:%S"
_PLAY_STEP_INTERVAL_MILLISECONDS = 250


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


def format_current_slider_position_label(
  timestamp,
  segment_point_index,
  segment_point_count,
  all_point_index,
  all_point_count,
):
  """Return the centered slider label with segment and all-scope position suffixes."""

  timestamp_text = format_slider_endpoint_timestamp(timestamp)
  segment_position_number = segment_point_index + 1
  all_position_number = all_point_index + 1

  return \
    "{timestamp_text}\n" \
    "(Current: {segment_position_number} of {segment_point_count}, " \
    "All: {all_position_number} of {all_point_count})".format(
      timestamp_text=timestamp_text,
      segment_position_number=segment_position_number,
      segment_point_count=segment_point_count,
      all_position_number=all_position_number,
      all_point_count=all_point_count,
    )


def clamp_selected_seconds(selected_seconds, earliest_timestamp, latest_timestamp):
  """Clamp epoch seconds to the inclusive track timestamp span."""

  earliest_seconds = earliest_timestamp.timestamp()
  latest_seconds = latest_timestamp.timestamp()

  if selected_seconds < earliest_seconds:
    return earliest_seconds

  if selected_seconds > latest_seconds:
    return latest_seconds

  return selected_seconds


class TimeSliderPanel(tkinter.Frame):
  """Slider row with earliest/latest labels and a centered current-time label."""

  def __init__(
    self,
    master,
    earliest_timestamp,
    latest_timestamp,
    timed_gpx_points,
    on_timestamp_changed,
    segment_summaries=None,
  ):
    """Build the slider UI and invoke on_timestamp_changed as the user scrubs."""

    super().__init__(master)

    self._earliest_timestamp = earliest_timestamp
    self._latest_timestamp = latest_timestamp
    self._timed_gpx_points = timed_gpx_points
    self._segment_summaries = segment_summaries
    self._on_timestamp_changed = on_timestamp_changed
    self._reference_timezone = earliest_timestamp.tzinfo
    self._earliest_seconds = earliest_timestamp.timestamp()
    self._latest_seconds = latest_timestamp.timestamp()
    self._current_point_index = 0
    self._applying_selected_seconds = False
    self._play_direction = None
    self._play_after_job = None

    self._build_widgets()
    self._apply_selected_seconds(self._earliest_seconds)

  def _create_slider_button_icons(self, slider_row):
    """Build play and step icons from map_icon_utility at a shared slider button size."""

    slider_button_width, slider_button_height = \
      gis_graphical_editor.map_icon_utility.measure_slider_button_pixel_size(slider_row)
    icon_width, icon_height = \
      gis_graphical_editor.map_icon_utility.compute_slider_button_icon_pixel_size(
        slider_button_width,
        slider_button_height,
      )
    self._rewind_play_icon = \
      gis_graphical_editor.map_icon_utility.create_rewind_play_button_icon(
        self,
        icon_width,
        icon_height,
      )
    self._previous_point_icon = \
      gis_graphical_editor.map_icon_utility.create_previous_step_button_icon(
        self,
        icon_width,
        icon_height,
      )
    self._next_point_icon = \
      gis_graphical_editor.map_icon_utility.create_next_step_button_icon(
        self,
        icon_width,
        icon_height,
      )
    self._fast_forward_play_icon = \
      gis_graphical_editor.map_icon_utility.create_fast_forward_play_button_icon(
        self,
        icon_width,
        icon_height,
      )

  def _build_slider_image_button(self, parent, icon, command):
    """Return an image button that keeps a reference to icon."""

    slider_button = tkinter.Button(parent, image=icon, command=command)
    slider_button.image = icon

    return slider_button

  def _build_widgets(self):
    """Lay out endpoint labels, step buttons, the scale, and the current-time label."""

    slider_row = tkinter.Frame(self)
    slider_row.pack(fill=tkinter.X, padx=8, pady=(8, 0))

    earliest_label_text = format_slider_endpoint_timestamp(self._earliest_timestamp)
    self._earliest_label = tkinter.Label(slider_row, text=earliest_label_text)
    self._earliest_label.pack(side=tkinter.LEFT)

    self._create_slider_button_icons(slider_row)

    self._rewind_play_button = self._build_slider_image_button(
      slider_row,
      self._rewind_play_icon,
      self._handle_rewind_play_click,
    )
    self._rewind_play_button.pack(side=tkinter.LEFT, padx=(8, 0))

    self._previous_point_button = self._build_slider_image_button(
      slider_row,
      self._previous_point_icon,
      self._handle_previous_point_step,
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
    self._time_scale.bind("<ButtonPress-1>", self._handle_scale_press)

    self._next_point_button = self._build_slider_image_button(
      slider_row,
      self._next_point_icon,
      self._handle_next_point_step,
    )
    self._next_point_button.pack(side=tkinter.LEFT)

    self._fast_forward_play_button = self._build_slider_image_button(
      slider_row,
      self._fast_forward_play_icon,
      self._handle_fast_forward_play_click,
    )
    self._fast_forward_play_button.pack(side=tkinter.LEFT, padx=(8, 0))

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

  def _apply_selected_seconds(self, selected_seconds, selected_point_index=None):
    """Clamp, move the slider, refresh the label, and notify the map callback."""

    if self._applying_selected_seconds:
      return

    self._applying_selected_seconds = True

    # Clamp to the track timestamp span represented by the slider endpoints.
    clamped_seconds = clamp_selected_seconds(
      selected_seconds,
      self._earliest_timestamp,
      self._latest_timestamp,
    )

    self._time_scale.set(clamped_seconds)
    selected_timestamp = self._build_selected_timestamp(clamped_seconds)

    if selected_point_index is not None:
      point_index = selected_point_index
    else:
      point_index = \
        gis_graphical_editor.track_analysis.find_timed_gpx_point_index_nearest_timestamp(
          self._timed_gpx_points,
          selected_timestamp,
        )

    if point_index is None:
      point_index = 0

    self._current_point_index = point_index
    position_counts = \
      gis_graphical_editor.track_analysis.resolve_slider_position_counts(
        self._segment_summaries,
        self._timed_gpx_points,
        point_index,
      )
    segment_point_index = position_counts[0]
    segment_point_count = position_counts[1]
    all_point_index = position_counts[2]
    all_point_count = position_counts[3]
    current_label_text = format_current_slider_position_label(
      selected_timestamp,
      segment_point_index,
      segment_point_count,
      all_point_index,
      all_point_count,
    )

    self._current_time_label.config(text=current_label_text)
    self._update_step_button_states()
    self._on_timestamp_changed(selected_timestamp)
    self._applying_selected_seconds = False

  def destroy(self):
    """Cancel any active play stepping before tearing down the panel widgets."""

    self._stop_play_stepping()

    super().destroy()

  def _stop_play_stepping(self):
    """Cancel scheduled play ticks and clear the active play direction."""

    if self._play_after_job is not None:
      self.after_cancel(self._play_after_job)
      self._play_after_job = None

    self._play_direction = None

  def _handle_rewind_play_click(self):
    """Step backward on an interval until the first point, or stop if already playing."""

    if self._play_direction == "backward":
      self._stop_play_stepping()

      return

    self._stop_play_stepping()

    if self._current_point_index <= 0:
      return

    self._play_direction = "backward"
    self._handle_play_step_tick()

  def _handle_fast_forward_play_click(self):
    """Step forward on an interval until the last point, or stop if already playing."""

    if self._play_direction == "forward":
      self._stop_play_stepping()

      return

    self._stop_play_stepping()

    last_point_index = len(self._timed_gpx_points) - 1

    if self._current_point_index >= last_point_index:
      return

    self._play_direction = "forward"
    self._handle_play_step_tick()

  def _schedule_play_step(self):
    """Queue the next automatic point step while play mode remains active."""

    if self._play_direction is None:
      return

    self._play_after_job = self.after(
      _PLAY_STEP_INTERVAL_MILLISECONDS,
      self._handle_play_step_tick,
    )

  def _handle_play_step_tick(self):
    """Advance one timed point in the active play direction, then reschedule or stop."""

    self._play_after_job = None

    if self._play_direction == "backward":
      if self._current_point_index <= 0:
        self._stop_play_stepping()

        return

      self._step_to_previous_point()

      if self._current_point_index <= 0:
        self._stop_play_stepping()

        return

    elif self._play_direction == "forward":
      last_point_index = len(self._timed_gpx_points) - 1

      if self._current_point_index >= last_point_index:
        self._stop_play_stepping()

        return

      self._step_to_next_point()

      if self._current_point_index >= last_point_index:
        self._stop_play_stepping()

        return

    self._schedule_play_step()

  def _step_to_previous_point(self):
    """Move the slider to the previous timed GPX point without altering play state."""

    if self._current_point_index <= 0:
      return

    self._select_point_index(self._current_point_index - 1)

  def _step_to_next_point(self):
    """Move the slider to the next timed GPX point without altering play state."""

    last_point_index = len(self._timed_gpx_points) - 1

    if self._current_point_index >= last_point_index:
      return

    self._select_point_index(self._current_point_index + 1)

  def _handle_previous_point_step(self):
    """Move the slider to the previous timed GPX point."""

    self._stop_play_stepping()
    self._step_to_previous_point()

  def _handle_next_point_step(self):
    """Move the slider to the next timed GPX point."""

    self._stop_play_stepping()
    self._step_to_next_point()

  def _select_point_index(self, point_index):
    """Set the slider to one timed GPX point by index."""

    selected_gpx_point = self._timed_gpx_points[point_index]
    selected_seconds = selected_gpx_point.timestamp.timestamp()
    self._apply_selected_seconds(selected_seconds, selected_point_index=point_index)

  def _handle_scale_press(self, event):
    """Stop auto-play when the user begins dragging the slider."""

    self._stop_play_stepping()

  def _update_step_button_states(self):
    """Disable step and play buttons at the first and last timed points."""

    last_point_index = len(self._timed_gpx_points) - 1

    if self._current_point_index <= 0:
      previous_button_state = tkinter.DISABLED
      rewind_play_button_state = tkinter.DISABLED
    else:
      previous_button_state = tkinter.NORMAL
      rewind_play_button_state = tkinter.NORMAL

    if self._current_point_index >= last_point_index:
      next_button_state = tkinter.DISABLED
      fast_forward_play_button_state = tkinter.DISABLED
    else:
      next_button_state = tkinter.NORMAL
      fast_forward_play_button_state = tkinter.NORMAL

    self._previous_point_button.config(state=previous_button_state)
    self._next_point_button.config(state=next_button_state)
    self._rewind_play_button.config(state=rewind_play_button_state)
    self._fast_forward_play_button.config(state=fast_forward_play_button_state)

  def _handle_scale_change(self, scale_value):
    """Update the centered label and notify the map of the selected timestamp."""

    if self._applying_selected_seconds:
      return

    self._apply_selected_seconds(float(scale_value))

  def set_selected_timestamp(self, selected_timestamp):
    """Move the slider to selected_timestamp and refresh dependent UI."""

    self._stop_play_stepping()
    self._apply_selected_seconds(selected_timestamp.timestamp())

  def update_timed_gpx_points(
    self,
    timed_gpx_points,
    earliest_timestamp,
    latest_timestamp,
    segment_summaries=None,
  ):
    """Replace timed points and slider endpoints without destroying the panel."""

    self._stop_play_stepping()
    self._timed_gpx_points = timed_gpx_points
    self._segment_summaries = segment_summaries
    self._earliest_timestamp = earliest_timestamp
    self._latest_timestamp = latest_timestamp
    self._reference_timezone = earliest_timestamp.tzinfo
    self._earliest_seconds = earliest_timestamp.timestamp()
    self._latest_seconds = latest_timestamp.timestamp()
    self._time_scale.config(from_=self._earliest_seconds, to=self._latest_seconds)
    self._earliest_label.config(text=format_slider_endpoint_timestamp(self._earliest_timestamp))
    self._latest_label.config(text=format_slider_endpoint_timestamp(self._latest_timestamp))
    self._apply_selected_seconds(self._time_scale.get())
