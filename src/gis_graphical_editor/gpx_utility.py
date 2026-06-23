"""Parse GPX files into point records with coordinates and timestamps."""

import datetime
import zoneinfo

import gpxpy


class GpxPointRecord:
  """One GPX point with decimal coordinates and an optional timestamp."""

  def __init__(self, latitude, longitude, timestamp):
    """Store latitude, longitude, and an optional aware or naive timestamp."""

    self.latitude = latitude
    self.longitude = longitude
    self.timestamp = timestamp


def load_gpx_points_from_gpx(gpx_path):
  """Return ordered GpxPointRecord values from tracks, routes, and waypoints."""

  with open(gpx_path, "r", encoding="utf-8") as gpx_file:
    gpx_text = gpx_file.read()

  gpx_document = gpxpy.parse(gpx_text)
  gpx_points = []

  # Collect track segment points in file order.
  for track in gpx_document.tracks:
    for segment in track.segments:
      for point in segment.points:
        gpx_points.append(_build_gpx_point_record(point))

  if gpx_points:
    return gpx_points

  # Fall back to route points when the file has no track segments.
  for route in gpx_document.routes:
    for point in route.points:
      gpx_points.append(_build_gpx_point_record(point))

  if gpx_points:
    return gpx_points

  # Fall back to standalone waypoints when tracks and routes are absent.
  for waypoint in gpx_document.waypoints:
    gpx_points.append(_build_gpx_point_record(waypoint))

  return gpx_points


def load_track_points_from_gpx(gpx_path):
  """Return ordered (latitude, longitude) tuples from tracks, routes, and waypoints."""

  gpx_points = load_gpx_points_from_gpx(gpx_path)
  track_points = []

  # Project each record down to coordinate pairs for path rendering.
  for gpx_point in gpx_points:
    track_points.append((gpx_point.latitude, gpx_point.longitude))

  return track_points


def convert_gpx_point_timestamps_to_timezone(gpx_points, timezone_name):
  """Rewrite each point timestamp into timezone_name; return naive-encountered flag."""

  target_zone = zoneinfo.ZoneInfo(timezone_name)
  encountered_naive_timestamp = False

  # Shift every timed point into the display timezone.
  for gpx_point in gpx_points:
    if gpx_point.timestamp is None:
      continue

    if gpx_point.timestamp.tzinfo is None:
      encountered_naive_timestamp = True
      utc_timestamp = gpx_point.timestamp.replace(tzinfo=datetime.timezone.utc)
      gpx_point.timestamp = utc_timestamp.astimezone(target_zone)
      continue

    gpx_point.timestamp = gpx_point.timestamp.astimezone(target_zone)

  return gpx_points, encountered_naive_timestamp


def _build_gpx_point_record(gpx_point):
  """Convert a gpxpy point into a GpxPointRecord preserving timezone when present."""

  timestamp = gpx_point.time

  return GpxPointRecord(
    latitude=gpx_point.latitude,
    longitude=gpx_point.longitude,
    timestamp=timestamp,
  )
