"""Build interval markers and labels along a GPX point sequence."""

import datetime
import math

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.time_slider_panel

_EARTH_RADIUS_MILES = 3958.8
_MILES_LABEL = "mi"
_HOURS_LABEL = "h"


class TrackIntervalMarker:
  """Map marker derived from cumulative hours or distance along a GPX path."""

  def __init__(self, latitude, longitude, label):
    """Store map coordinates and the text shown beside the marker."""

    self.latitude = latitude
    self.longitude = longitude
    self.label = label


def build_hour_interval_markers(gpx_points, interval_hours, show_dates=False):
  """Return orange hour-interval markers with total hours and miles labels."""

  if interval_hours <= 0:
    return []

  interval_markers = []
  cumulative_hours = 0.0
  cumulative_miles = 0.0
  next_target_hours = float(interval_hours)

  # Walk each segment and emit markers whenever a target hour boundary is crossed.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    segment_miles = compute_miles_between_points(previous_point, current_point)
    segment_start_hours = cumulative_hours
    segment_start_miles = cumulative_miles

    cumulative_miles = cumulative_miles + segment_miles

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
      marker_miles = segment_start_miles + fraction * segment_miles
      marker_timestamp = interpolate_timestamp(previous_point, current_point, fraction)
      label = format_hour_interval_marker_label(
        next_target_hours,
        marker_miles,
        marker_timestamp,
        show_dates,
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


def build_distance_interval_markers(gpx_points, interval_miles, show_dates=False):
  """Return red distance-interval markers with total miles and timestamp labels."""

  if interval_miles <= 0:
    return []

  interval_markers = []
  cumulative_miles = 0.0
  next_target_miles = float(interval_miles)

  # Walk each segment and emit markers whenever a target mile boundary is crossed.
  for point_index in range(1, len(gpx_points)):
    previous_point = gpx_points[point_index - 1]
    current_point = gpx_points[point_index]
    segment_miles = compute_miles_between_points(previous_point, current_point)
    segment_start_miles = cumulative_miles

    cumulative_miles = cumulative_miles + segment_miles

    if segment_miles <= 0:
      continue

    while next_target_miles <= cumulative_miles + 1e-9:
      fraction = (next_target_miles - segment_start_miles) / segment_miles
      latitude = previous_point.latitude + fraction * (current_point.latitude - previous_point.latitude)
      longitude = previous_point.longitude + fraction * (current_point.longitude - previous_point.longitude)
      marker_timestamp = interpolate_timestamp(previous_point, current_point, fraction)
      label = format_distance_interval_marker_label(
        next_target_miles,
        marker_timestamp,
        show_dates,
      )

      interval_markers.append(
        TrackIntervalMarker(
          latitude=latitude,
          longitude=longitude,
          label=label,
        ),
      )

      next_target_miles = next_target_miles + interval_miles

  return interval_markers


def compute_miles_between_points(first_point, second_point):
  """Return great-circle miles between two GpxPointRecord coordinates."""

  latitude_delta_radians = math.radians(second_point.latitude - first_point.latitude)
  longitude_delta_radians = math.radians(second_point.longitude - first_point.longitude)
  first_latitude_radians = math.radians(first_point.latitude)
  second_latitude_radians = math.radians(second_point.latitude)

  haversine_value = \
    math.sin(latitude_delta_radians / 2) ** 2 \
    + math.cos(first_latitude_radians) \
    * math.cos(second_latitude_radians) \
    * math.sin(longitude_delta_radians / 2) ** 2
  central_angle_radians = 2 * math.asin(math.sqrt(haversine_value))

  return _EARTH_RADIUS_MILES * central_angle_radians


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


def format_hour_interval_marker_label(total_hours, total_miles, marker_timestamp=None, show_dates=False):
  """Format the --mark-hours marker label with hours, miles, and optional timestamp."""

  hours_display = int(round(total_hours))
  miles_display = int(round(total_miles))
  hours_text = "{total_hours} {hours_label}".format(
    total_hours=hours_display,
    hours_label=_HOURS_LABEL,
  )
  miles_text = "{total_miles} {miles_label}".format(
    total_miles=miles_display,
    miles_label=_MILES_LABEL,
  )

  label_text = "{hours_text}, {miles_text}".format(
    hours_text=hours_text,
    miles_text=miles_text,
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


def format_distance_interval_marker_label(total_miles, marker_timestamp, show_dates=False):
  """Format the --mark-distance marker label with integer miles and a timestamp."""

  miles_display = int(round(total_miles))
  miles_text = "{total_miles} {miles_label}".format(
    total_miles=miles_display,
    miles_label=_MILES_LABEL,
  )

  if marker_timestamp is None:
    return miles_text

  timestamp_text = \
    gis_graphical_editor.time_slider_panel.format_display_timestamp(
      marker_timestamp,
      include_date=show_dates,
    )

  return "{miles_text}, {timestamp_text}".format(
    miles_text=miles_text,
    timestamp_text=timestamp_text,
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
