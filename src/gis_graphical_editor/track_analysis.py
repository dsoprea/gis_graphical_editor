"""Build interval markers and labels along a GPX point sequence."""

import datetime
import math

import gis_graphical_editor.gpx_utility

_EARTH_RADIUS_MILES = 3958.8
_MILES_LABEL = "mi"
_HOURS_LABEL = "h"


class TrackIntervalMarker:
  """Map marker derived from cumulative hours or distance along a GPX path."""

  def __init__(self, latitude, longitude, label):
    self.latitude = latitude
    self.longitude = longitude
    self.label = label


def build_hour_interval_markers(gpx_points, interval_hours):
  """Return orange hour-interval markers with total hours and miles labels."""

  if interval_hours <= 0:
    return []

  interval_markers = []
  cumulative_hours = 0.0
  cumulative_miles = 0.0
  next_target_hours = float(interval_hours)

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
      label = format_hour_interval_marker_label(next_target_hours, marker_miles)

      interval_markers.append(
        TrackIntervalMarker(
          latitude=latitude,
          longitude=longitude,
          label=label,
        ),
      )

      next_target_hours = next_target_hours + interval_hours

  return interval_markers


def build_distance_interval_markers(gpx_points, interval_miles):
  """Return red distance-interval markers with total miles and timestamp labels."""

  if interval_miles <= 0:
    return []

  interval_markers = []
  cumulative_miles = 0.0
  next_target_miles = float(interval_miles)

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
      label = format_distance_interval_marker_label(next_target_miles, marker_timestamp)

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
  elapsed_seconds = (second_timestamp - first_timestamp).total_seconds()

  return elapsed_seconds / 3600.0


def interpolate_timestamp(first_point, second_point, fraction):
  if first_point.timestamp is not None and second_point.timestamp is not None:
    elapsed_seconds = (second_point.timestamp - first_point.timestamp).total_seconds()
    interpolated_seconds = elapsed_seconds * fraction

    return first_point.timestamp + datetime.timedelta(seconds=interpolated_seconds)

  if second_point.timestamp is not None:
    return second_point.timestamp

  if first_point.timestamp is not None:
    return first_point.timestamp

  return None


def format_hour_interval_marker_label(total_hours, total_miles):
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

  return "{hours_text}, {miles_text}".format(
    hours_text=hours_text,
    miles_text=miles_text,
  )


def format_distance_interval_marker_label(total_miles, marker_timestamp):
  miles_display = int(round(total_miles))
  miles_text = "{total_miles} {miles_label}".format(
    total_miles=miles_display,
    miles_label=_MILES_LABEL,
  )

  if marker_timestamp is None:
    return miles_text

  timestamp_text = marker_timestamp.strftime("%Y-%m-%d %H:%M:%S")

  return "{miles_text}, {timestamp_text}".format(
    miles_text=miles_text,
    timestamp_text=timestamp_text,
  )


def has_timestamps(gpx_points):
  for gpx_point in gpx_points:
    if gpx_point.timestamp is not None:
      return True

  return False
