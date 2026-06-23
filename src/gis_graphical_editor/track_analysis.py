"""Build interval markers and labels along a GPX point sequence."""

import datetime
import math

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.time_slider_panel

_EARTH_RADIUS_MILES = 3958.8
_EARTH_RADIUS_KILOMETERS = 6371.0
_MILES_LABEL = "mi"
_KILOMETERS_LABEL = "km"
_MILES_PER_HOUR_LABEL = "mph"
_KILOMETERS_PER_HOUR_LABEL = "kph"
_HOURS_LABEL = "h"
_IDLE_VELOCITY_MILES_PER_HOUR = 1.0
_IDLE_VELOCITY_KILOMETERS_PER_HOUR = 2.0


class TrackSegmentSummary:
  """Timestamp span and points for one GPX track segment."""

  def __init__(self, segment_points, earliest_timestamp, latest_timestamp):
    """Store segment points and optional earliest and latest timestamps."""

    self.segment_points = segment_points
    self.earliest_timestamp = earliest_timestamp
    self.latest_timestamp = latest_timestamp
    self.point_count = len(segment_points)


class TrackIntervalMarker:
  """Map marker derived from cumulative hours or distance along a GPX path."""

  def __init__(self, latitude, longitude, label):
    """Store map coordinates and the text shown beside the marker."""

    self.latitude = latitude
    self.longitude = longitude
    self.label = label


def build_track_segment_summaries(
  segment_point_lists,
  exclude_idle_segments=False,
  use_metric_units=False,
):
  """Return segment summaries sorted by earliest timestamp when present."""

  segment_summaries = []

  # Derive each segment span, including untimed segments without a timestamp range.
  for segment_points in segment_point_lists:
    timestamp_range = get_timestamp_range(segment_points)

    if timestamp_range is None:
      segment_summaries.append(
        TrackSegmentSummary(
          segment_points,
          None,
          None,
        ),
      )
      continue

    earliest_timestamp, latest_timestamp = timestamp_range
    segment_summaries.append(
      TrackSegmentSummary(
        segment_points,
        earliest_timestamp,
        latest_timestamp,
      ),
    )

  segment_summaries.sort(key=_build_track_segment_summary_sort_key)

  if not exclude_idle_segments:
    return segment_summaries

  active_segment_summaries = []

  # Drop segments whose average velocity falls below the idle threshold.
  for segment_summary in segment_summaries:
    if is_idle_track_segment_summary(segment_summary, use_metric_units):
      continue

    active_segment_summaries.append(segment_summary)

  return active_segment_summaries


def format_elapsed_duration_between_timestamps(first_timestamp, second_timestamp):
  """Return an HH:MM:SS duration string for the elapsed time between two datetimes."""

  elapsed_timedelta = second_timestamp - first_timestamp
  total_seconds = int(elapsed_timedelta.total_seconds())

  if total_seconds < 0:
    total_seconds = abs(total_seconds)

  duration_hours = total_seconds // 3600
  duration_minutes = (total_seconds % 3600) // 60
  duration_seconds = total_seconds % 60

  return "{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}".format(
    duration_hours=duration_hours,
    duration_minutes=duration_minutes,
    duration_seconds=duration_seconds,
  )


def compute_total_path_distance_for_gpx_points(gpx_points, use_metric_units=False):
  """Return cumulative great-circle distance along consecutive GPX points."""

  total_distance = 0.0

  # Sum haversine leg distances between each consecutive point pair.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    segment_distance = compute_distance_between_points(
      previous_point,
      current_point,
      use_metric_units,
    )
    total_distance = total_distance + segment_distance

  return total_distance


def compute_average_velocity_for_segment_summary(segment_summary, use_metric_units=False):
  """Return average path velocity for a segment, or None when it cannot be derived."""

  if segment_summary.earliest_timestamp is None or segment_summary.latest_timestamp is None:
    return None

  elapsed_timedelta = \
    segment_summary.latest_timestamp - segment_summary.earliest_timestamp
  elapsed_seconds = elapsed_timedelta.total_seconds()

  if elapsed_seconds <= 0:
    return None

  total_distance = compute_total_path_distance_for_gpx_points(
    segment_summary.segment_points,
    use_metric_units,
  )
  elapsed_hours = elapsed_seconds / 3600.0

  return total_distance / elapsed_hours


def is_idle_track_segment_summary(segment_summary, use_metric_units=False):
  """Return True when a segment's average velocity is below the idle threshold."""

  average_velocity = compute_average_velocity_for_segment_summary(
    segment_summary,
    use_metric_units,
  )

  if average_velocity is None:
    return True

  return is_idle_velocity(average_velocity, use_metric_units)


def is_idle_velocity(velocity, use_metric_units=False):
  """Return True when a velocity is below the idle threshold."""

  if use_metric_units:
    return velocity < _IDLE_VELOCITY_KILOMETERS_PER_HOUR

  return velocity < _IDLE_VELOCITY_MILES_PER_HOUR


def compute_velocity_between_points(previous_point, current_point, use_metric_units=False):
  """Return leg velocity between consecutive timed GPX points, or None when unknown."""

  if previous_point.timestamp is None or current_point.timestamp is None:
    return None

  elapsed_timedelta = current_point.timestamp - previous_point.timestamp
  elapsed_seconds = elapsed_timedelta.total_seconds()

  if elapsed_seconds <= 0:
    return None

  leg_distance = compute_distance_between_points(
    previous_point,
    current_point,
    use_metric_units,
  )
  elapsed_hours = elapsed_seconds / 3600.0

  return leg_distance / elapsed_hours


def collect_leg_velocities_for_gpx_points(
  gpx_points,
  use_metric_units=False,
  exclude_idle_segments=False,
):
  """Return leg velocities along a point sequence, optionally omitting idle legs."""

  leg_velocities = []

  # Derive each consecutive leg velocity and apply the idle filter when requested.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    leg_velocity = compute_velocity_between_points(
      previous_point,
      current_point,
      use_metric_units,
    )

    if leg_velocity is None:
      continue

    if exclude_idle_segments and is_idle_velocity(leg_velocity, use_metric_units):
      continue

    leg_velocities.append(leg_velocity)

  return leg_velocities


def compute_minimum_velocity_for_segment_summary(
  segment_summary,
  use_metric_units=False,
  exclude_idle_segments=False,
):
  """Return the lowest leg velocity in a segment, or None when none qualify."""

  leg_velocities = collect_leg_velocities_for_gpx_points(
    segment_summary.segment_points,
    use_metric_units,
    exclude_idle_segments,
  )

  if not leg_velocities:
    return None

  return min(leg_velocities)


def compute_maximum_velocity_for_segment_summary(
  segment_summary,
  use_metric_units=False,
  exclude_idle_segments=False,
):
  """Return the highest leg velocity in a segment, or None when none qualify."""

  leg_velocities = collect_leg_velocities_for_gpx_points(
    segment_summary.segment_points,
    use_metric_units,
    exclude_idle_segments,
  )

  if not leg_velocities:
    return None

  return max(leg_velocities)


def format_track_segment_interval_label(
  segment_summary,
  use_metric_units=False,
  exclude_idle_segments=False,
):
  """Return a segment label with point count, duration, and path distance."""

  total_distance = compute_total_path_distance_for_gpx_points(
    segment_summary.segment_points,
    use_metric_units,
  )
  distance_text = format_distance_display(total_distance, use_metric_units)

  if segment_summary.earliest_timestamp is None or segment_summary.latest_timestamp is None:
    return \
      "Points: {point_count}\n" \
      "Distance: {distance_text}\n" \
      "no timestamps".format(
        point_count=segment_summary.point_count,
        distance_text=distance_text,
      )

  earliest_text = \
    gis_graphical_editor.time_slider_panel.format_display_timestamp(
      segment_summary.earliest_timestamp,
      include_date=True,
      include_day_of_week=True,
    )
  latest_text = \
    gis_graphical_editor.time_slider_panel.format_display_timestamp(
      segment_summary.latest_timestamp,
      include_date=True,
      include_day_of_week=True,
    )
  duration_text = format_elapsed_duration_between_timestamps(
    segment_summary.earliest_timestamp,
    segment_summary.latest_timestamp,
  )
  average_velocity = compute_average_velocity_for_segment_summary(
    segment_summary,
    use_metric_units,
  )
  minimum_velocity = compute_minimum_velocity_for_segment_summary(
    segment_summary,
    use_metric_units,
    exclude_idle_segments,
  )
  maximum_velocity = compute_maximum_velocity_for_segment_summary(
    segment_summary,
    use_metric_units,
    exclude_idle_segments,
  )
  average_velocity_text = format_velocity_display(average_velocity, use_metric_units)
  minimum_velocity_text = format_velocity_display(minimum_velocity, use_metric_units)
  maximum_velocity_text = format_velocity_display(maximum_velocity, use_metric_units)
  velocity_summary_text = \
    "AVG {average_velocity_text}, MIN {minimum_velocity_text}, MAX {maximum_velocity_text}".format(
      average_velocity_text=average_velocity_text,
      minimum_velocity_text=minimum_velocity_text,
      maximum_velocity_text=maximum_velocity_text,
    )

  return \
    "Start Timestamp: {earliest_text}\n" \
    "End Timestamp: {latest_text}\n" \
    "Points: {point_count}\n" \
    "Interval: {duration_text}\n" \
    "Distance: {distance_text}\n" \
    "Velocity: {velocity_summary_text}".format(
      earliest_text=earliest_text,
      latest_text=latest_text,
      point_count=segment_summary.point_count,
      duration_text=duration_text,
      distance_text=distance_text,
      velocity_summary_text=velocity_summary_text,
    )


def _build_track_segment_summary_sort_key(segment_summary):
  """Sort timed segments by earliest timestamp and untimed segments last."""

  if segment_summary.earliest_timestamp is None:
    return (1, datetime.datetime.max.replace(tzinfo=datetime.timezone.utc))

  return (0, segment_summary.earliest_timestamp)


def build_hour_interval_markers(gpx_points, interval_hours, show_dates=False, use_metric_units=False):
  """Return orange hour-interval markers with total hours and distance labels."""

  if interval_hours <= 0:
    return []

  interval_markers = []
  cumulative_hours = 0.0
  cumulative_distance = 0.0
  next_target_hours = float(interval_hours)

  # Walk each segment and emit markers whenever a target hour boundary is crossed.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    segment_distance = compute_distance_between_points(
      previous_point,
      current_point,
      use_metric_units,
    )
    segment_start_hours = cumulative_hours
    segment_start_distance = cumulative_distance

    cumulative_distance = cumulative_distance + segment_distance

    if previous_point.timestamp is None or current_point.timestamp is None:
      continue

    segment_hours = compute_hours_between_timestamps(
      previous_point.timestamp,
      current_point.timestamp,
    )

    if segment_hours <= 0:
      continue

    cumulative_hours = cumulative_hours + segment_hours

    while next_target_hours <= cumulative_hours + 1e-9:
      fraction = (next_target_hours - segment_start_hours) / segment_hours
      latitude = previous_point.latitude + fraction * (current_point.latitude - previous_point.latitude)
      longitude = previous_point.longitude + fraction * (current_point.longitude - previous_point.longitude)
      marker_distance = segment_start_distance + fraction * segment_distance
      marker_timestamp = interpolate_timestamp(previous_point, current_point, fraction)
      label = format_hour_interval_marker_label(
        next_target_hours,
        marker_distance,
        marker_timestamp,
        show_dates,
        use_metric_units,
      )

      interval_markers.append(
        TrackIntervalMarker(
          latitude=latitude,
          longitude=longitude,
          label=label,
        ),
      )

      next_target_hours = next_target_hours + interval_hours

  return interval_markers


def build_distance_interval_markers(
  gpx_points,
  interval_distance,
  show_dates=False,
  use_metric_units=False,
):
  """Return red distance-interval markers with total distance and timestamp labels."""

  if interval_distance <= 0:
    return []

  interval_markers = []
  cumulative_distance = 0.0
  next_target_distance = float(interval_distance)

  # Walk each segment and emit markers whenever a target distance boundary is crossed.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    segment_distance = compute_distance_between_points(
      previous_point,
      current_point,
      use_metric_units,
    )
    segment_start_distance = cumulative_distance

    cumulative_distance = cumulative_distance + segment_distance

    if segment_distance <= 0:
      continue

    while next_target_distance <= cumulative_distance + 1e-9:
      fraction = (next_target_distance - segment_start_distance) / segment_distance
      latitude = previous_point.latitude + fraction * (current_point.latitude - previous_point.latitude)
      longitude = previous_point.longitude + fraction * (current_point.longitude - previous_point.longitude)
      marker_timestamp = interpolate_timestamp(previous_point, current_point, fraction)
      label = format_distance_interval_marker_label(
        next_target_distance,
        marker_timestamp,
        show_dates,
        use_metric_units,
      )

      interval_markers.append(
        TrackIntervalMarker(
          latitude=latitude,
          longitude=longitude,
          label=label,
        ),
      )

      next_target_distance = next_target_distance + interval_distance

  return interval_markers


def compute_distance_between_points(first_point, second_point, use_metric_units=False):
  """Return great-circle distance in miles or kilometers between two GPX points."""

  central_angle_radians = _compute_haversine_central_angle_radians(first_point, second_point)

  if use_metric_units:
    return _EARTH_RADIUS_KILOMETERS * central_angle_radians

  return _EARTH_RADIUS_MILES * central_angle_radians


def compute_miles_between_points(first_point, second_point):
  """Return great-circle miles between two GpxPointRecord coordinates."""

  return compute_distance_between_points(first_point, second_point, use_metric_units=False)


def _compute_haversine_central_angle_radians(first_point, second_point):
  """Return the haversine central angle in radians between two GPX coordinates."""

  latitude_delta_radians = math.radians(second_point.latitude - first_point.latitude)
  longitude_delta_radians = math.radians(second_point.longitude - first_point.longitude)
  first_latitude_radians = math.radians(first_point.latitude)
  second_latitude_radians = math.radians(second_point.latitude)

  haversine_value = \
    math.sin(latitude_delta_radians / 2) ** 2 \
    + math.cos(first_latitude_radians) \
    * math.cos(second_latitude_radians) \
    * math.sin(longitude_delta_radians / 2) ** 2

  return 2 * math.asin(math.sqrt(haversine_value))


def compute_hours_between_timestamps(first_timestamp, second_timestamp):
  """Return elapsed hours between two datetimes."""

  elapsed_seconds = (second_timestamp - first_timestamp).total_seconds()

  return elapsed_seconds / 3600.0


def interpolate_timestamp(first_point, second_point, fraction):
  """Linearly interpolate a timestamp along a segment when both ends are timed."""

  if first_point.timestamp is not None and second_point.timestamp is not None:
    elapsed_seconds = (second_point.timestamp - first_point.timestamp).total_seconds()
    interpolated_seconds = elapsed_seconds * fraction

    return first_point.timestamp + datetime.timedelta(seconds=interpolated_seconds)

  if second_point.timestamp is not None:
    return second_point.timestamp

  if first_point.timestamp is not None:
    return first_point.timestamp

  return None


def format_hour_interval_marker_label(
  total_hours,
  total_distance,
  marker_timestamp=None,
  show_dates=False,
  use_metric_units=False,
):
  """Format the --mark-hours marker label with hours, distance, and optional timestamp."""

  hours_display = int(round(total_hours))
  distance_text = format_distance_display(total_distance, use_metric_units)
  hours_text = "{total_hours} {hours_label}".format(
    total_hours=hours_display,
    hours_label=_HOURS_LABEL,
  )

  label_text = "{hours_text}, {distance_text}".format(
    hours_text=hours_text,
    distance_text=distance_text,
  )

  if marker_timestamp is None:
    return label_text

  timestamp_text = \
    gis_graphical_editor.time_slider_panel.format_display_timestamp(
      marker_timestamp,
      include_date=show_dates,
    )

  return "{label_text}, {timestamp_text}".format(
    label_text=label_text,
    timestamp_text=timestamp_text,
  )


def format_distance_interval_marker_label(
  total_distance,
  marker_timestamp,
  show_dates=False,
  use_metric_units=False,
):
  """Format the --mark-distance marker label with integer distance and a timestamp."""

  distance_text = format_distance_display(total_distance, use_metric_units)

  if marker_timestamp is None:
    return distance_text

  timestamp_text = \
    gis_graphical_editor.time_slider_panel.format_display_timestamp(
      marker_timestamp,
      include_date=show_dates,
    )

  return "{distance_text}, {timestamp_text}".format(
    distance_text=distance_text,
    timestamp_text=timestamp_text,
  )


def format_distance_display(total_distance, use_metric_units=False):
  """Return a rounded distance value with the miles or kilometers unit label."""

  distance_display = int(round(total_distance))

  if use_metric_units:
    distance_label = _KILOMETERS_LABEL
  else:
    distance_label = _MILES_LABEL

  return "{distance_display} {distance_label}".format(
    distance_display=distance_display,
    distance_label=distance_label,
  )


def format_velocity_display(average_velocity, use_metric_units=False):
  """Return a one-decimal velocity value with the mph or kph unit label."""

  if average_velocity is None:
    return "n/a"

  velocity_display = "{average_velocity:.1f}".format(average_velocity=average_velocity)

  if use_metric_units:
    velocity_label = _KILOMETERS_PER_HOUR_LABEL
  else:
    velocity_label = _MILES_PER_HOUR_LABEL

  return "{velocity_display} {velocity_label}".format(
    velocity_display=velocity_display,
    velocity_label=velocity_label,
  )


def has_timestamps(gpx_points):
  """Return True when at least one GPX point carries a timestamp."""

  for gpx_point in gpx_points:
    if gpx_point.timestamp is not None:
      return True

  return False


def get_timestamp_range(gpx_points):
  """Return earliest and latest timestamps present in the point list."""

  earliest_timestamp = None
  latest_timestamp = None

  for gpx_point in gpx_points:
    if gpx_point.timestamp is None:
      continue

    if earliest_timestamp is None or gpx_point.timestamp < earliest_timestamp:
      earliest_timestamp = gpx_point.timestamp

    if latest_timestamp is None or gpx_point.timestamp > latest_timestamp:
      latest_timestamp = gpx_point.timestamp

  if earliest_timestamp is None or latest_timestamp is None:
    return None

  return earliest_timestamp, latest_timestamp


def find_position_at_timestamp(gpx_points, target_timestamp):
  """Return (latitude, longitude) for target_timestamp along the GPX path."""

  if not gpx_points:
    return None

  first_timestamped_point = None
  last_timestamped_point = None

  # Resolve track endpoints that bound the searchable timestamp range.
  for gpx_point in gpx_points:
    if gpx_point.timestamp is not None:
      first_timestamped_point = gpx_point

      break

  for gpx_point in reversed(gpx_points):
    if gpx_point.timestamp is not None:
      last_timestamped_point = gpx_point

      break

  if first_timestamped_point is None or last_timestamped_point is None:
    return None

  if target_timestamp <= first_timestamped_point.timestamp:
    return first_timestamped_point.latitude, first_timestamped_point.longitude

  if target_timestamp >= last_timestamped_point.timestamp:
    return last_timestamped_point.latitude, last_timestamped_point.longitude

  # Interpolate within the segment that contains the target timestamp.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]

    if previous_point.timestamp is None or current_point.timestamp is None:
      continue

    if previous_point.timestamp <= target_timestamp <= current_point.timestamp:
      elapsed_seconds = (current_point.timestamp - previous_point.timestamp).total_seconds()

      if elapsed_seconds <= 0:
        return current_point.latitude, current_point.longitude

      target_elapsed_seconds = (target_timestamp - previous_point.timestamp).total_seconds()
      fraction = target_elapsed_seconds / elapsed_seconds
      latitude = previous_point.latitude + fraction * (current_point.latitude - previous_point.latitude)
      longitude = previous_point.longitude + fraction * (current_point.longitude - previous_point.longitude)

      return latitude, longitude

  return last_timestamped_point.latitude, last_timestamped_point.longitude


def find_gpx_point_nearest_timestamp(gpx_points, target_timestamp):
  """Return the timed GPX point closest to target_timestamp."""

  nearest_gpx_point = None
  smallest_timestamp_delta = None

  # Scan visible points and keep the one with the smallest timestamp distance.
  for gpx_point in gpx_points:
    if gpx_point.timestamp is None:
      continue

    timestamp_delta = abs((gpx_point.timestamp - target_timestamp).total_seconds())

    if smallest_timestamp_delta is None or timestamp_delta < smallest_timestamp_delta:
      smallest_timestamp_delta = timestamp_delta
      nearest_gpx_point = gpx_point

  return nearest_gpx_point


def find_track_segment_summary_index_at_timestamp(segment_summaries, target_timestamp):
  """Return the index of the summary whose timestamp span contains target_timestamp."""

  # Match the first timed segment whose closed interval includes the slider time.
  for segment_index, segment_summary in enumerate(segment_summaries):
    if segment_summary.earliest_timestamp is None or segment_summary.latest_timestamp is None:
      continue

    if segment_summary.earliest_timestamp <= target_timestamp <= segment_summary.latest_timestamp:
      return segment_index

  return None


def find_segment_summary_for_gpx_point(segment_summaries, gpx_point):
  """Return the segment summary whose point list contains gpx_point by identity."""

  if gpx_point is None:
    return None

  # Match the owning segment by object identity in its point list.
  for segment_summary in segment_summaries:
    for segment_point in segment_summary.segment_points:
      if segment_point is gpx_point:
        return segment_summary

  return None


def format_gpx_point_metadata_lines(gpx_point):
  """Return label lines for one GPX point and its additional metadata fields."""

  if gpx_point is None:
    return []

  metadata_lines = [
    "latitude: {latitude}".format(latitude=gpx_point.latitude),
    "longitude: {longitude}".format(longitude=gpx_point.longitude),
  ]

  if gpx_point.timestamp is None:
    metadata_lines.append("timestamp: n/a")
  else:
    timestamp_text = \
      gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(
        gpx_point.timestamp,
      )
    metadata_lines.append("timestamp: {timestamp_text}".format(timestamp_text=timestamp_text))

  metadata_keys = sorted(gpx_point.additional_metadata.keys())

  for metadata_key in metadata_keys:
    metadata_value = gpx_point.additional_metadata[metadata_key]
    metadata_lines.append(
      "{metadata_key}: {metadata_value}".format(
        metadata_key=metadata_key,
        metadata_value=metadata_value,
      ),
    )

  return metadata_lines


def format_segment_summary_metadata_lines(segment_summary, use_metric_units=False):
  """Return label lines for one segment summary and its derived statistics."""

  if segment_summary is None:
    return []

  metadata_lines = [
    "point_count: {point_count}".format(point_count=segment_summary.point_count),
  ]
  total_distance = compute_total_path_distance_for_gpx_points(
    segment_summary.segment_points,
    use_metric_units,
  )
  distance_text = format_distance_display(total_distance, use_metric_units)
  metadata_lines.append("distance: {distance_text}".format(distance_text=distance_text))

  if segment_summary.earliest_timestamp is None or segment_summary.latest_timestamp is None:
    metadata_lines.append("earliest_timestamp: n/a")
    metadata_lines.append("latest_timestamp: n/a")
    metadata_lines.append("interval: n/a")
    metadata_lines.append("average_velocity: n/a")
    metadata_lines.append("idle: n/a")

    return metadata_lines

  earliest_text = \
    gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(
      segment_summary.earliest_timestamp,
    )
  latest_text = \
    gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(
      segment_summary.latest_timestamp,
    )
  duration_text = format_elapsed_duration_between_timestamps(
    segment_summary.earliest_timestamp,
    segment_summary.latest_timestamp,
  )
  average_velocity = compute_average_velocity_for_segment_summary(
    segment_summary,
    use_metric_units,
  )
  average_velocity_text = format_velocity_display(average_velocity, use_metric_units)
  idle_segment = is_idle_track_segment_summary(segment_summary, use_metric_units)

  metadata_lines.append(
    "earliest_timestamp: {earliest_text}".format(earliest_text=earliest_text),
  )
  metadata_lines.append(
    "latest_timestamp: {latest_text}".format(latest_text=latest_text),
  )
  metadata_lines.append("interval: {duration_text}".format(duration_text=duration_text))
  metadata_lines.append(
    "average_velocity: {average_velocity_text}".format(
      average_velocity_text=average_velocity_text,
    ),
  )
  metadata_lines.append("idle: {idle_segment}".format(idle_segment=idle_segment))

  return metadata_lines
