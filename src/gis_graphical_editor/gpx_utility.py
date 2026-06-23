"""Parse GPX files into point records with coordinates and timestamps."""

import datetime
import zoneinfo

import gpxpy


class GpxPointRecord:
  """One GPX point with decimal coordinates and an optional timestamp."""

  def __init__(self, latitude, longitude, timestamp, additional_metadata=None):
    """Store latitude, longitude, timestamp, and optional extra GPX field values."""

    self.latitude = latitude
    self.longitude = longitude
    self.timestamp = timestamp

    if additional_metadata is None:
      self.additional_metadata = {}
    else:
      self.additional_metadata = additional_metadata


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


def load_track_point_segments_from_gpx(gpx_path):
  """Return ordered segment point lists from tracks, routes, or waypoints."""

  with open(gpx_path, "r", encoding="utf-8") as gpx_file:
    gpx_text = gpx_file.read()

  gpx_document = gpxpy.parse(gpx_text)
  segment_point_lists = []

  # Collect each track segment as its own point list.
  for track in gpx_document.tracks:
    for segment in track.segments:
      segment_points = []

      for point in segment.points:
        segment_points.append(_build_gpx_point_record(point))

      if segment_points:
        segment_point_lists.append(segment_points)

  if segment_point_lists:
    return segment_point_lists

  # Fall back to one segment per route when the file has no track segments.
  for route in gpx_document.routes:
    route_points = []

    for point in route.points:
      route_points.append(_build_gpx_point_record(point))

    if route_points:
      segment_point_lists.append(route_points)

  if segment_point_lists:
    return segment_point_lists

  # Fall back to a single waypoint segment when tracks and routes are absent.
  waypoint_points = []

  for waypoint in gpx_document.waypoints:
    waypoint_points.append(_build_gpx_point_record(waypoint))

  if waypoint_points:
    segment_point_lists.append(waypoint_points)

  return segment_point_lists


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
  additional_metadata = _build_additional_metadata_from_gpx_point(gpx_point)

  return GpxPointRecord(
    latitude=gpx_point.latitude,
    longitude=gpx_point.longitude,
    timestamp=timestamp,
    additional_metadata=additional_metadata,
  )


def _build_additional_metadata_from_gpx_point(gpx_point):
  """Return string metadata for every populated gpxpy point field except lat/lon/time."""

  additional_metadata = {}
  core_field_names = {"latitude", "longitude", "time"}
  gpx_fields = gpx_point.gpx_10_fields + gpx_point.gpx_11_fields

  # Copy each populated standard GPX field into the metadata map.
  for gpx_field in gpx_fields:
    if not hasattr(gpx_field, "name"):
      continue

    field_name = gpx_field.name

    if field_name in core_field_names:
      continue

    field_value = getattr(gpx_point, field_name, None)

    if _is_empty_gpx_metadata_value(field_value):
      continue

    additional_metadata[field_name] = _stringify_gpx_metadata_value(field_value)

  # Serialize extension XML children when the point carries custom tags.
  for extension_index, extension_element in enumerate(gpx_point.extensions):
    extension_key = _build_extension_metadata_key(extension_element, extension_index)
    extension_text = _stringify_gpx_metadata_value(extension_element.text)

    if extension_text != "":
      additional_metadata[extension_key] = extension_text

    for child_element in extension_element:
      child_key = _build_extension_metadata_key(child_element, extension_index)
      child_text = _stringify_gpx_metadata_value(child_element.text)

      if child_text != "":
        additional_metadata[child_key] = child_text

  return additional_metadata


def _is_empty_gpx_metadata_value(field_value):
  """Return True when a GPX metadata value should be omitted from display."""

  if field_value is None:
    return True

  if isinstance(field_value, str) and field_value == "":
    return True

  if isinstance(field_value, (list, dict, tuple, set)) and len(field_value) == 0:
    return True

  return False


def _stringify_gpx_metadata_value(field_value):
  """Return a display string for one GPX metadata value."""

  if field_value is None:
    return ""

  if isinstance(field_value, datetime.datetime):
    return field_value.isoformat()

  return str(field_value)


def _build_extension_metadata_key(extension_element, extension_index):
  """Return a stable metadata key for one GPX extension XML element."""

  element_tag = extension_element.tag

  if "}" in element_tag:
    namespace_uri, local_name = element_tag.split("}", 1)
    namespace_prefix = namespace_uri.lstrip("{")

    return "{namespace_prefix}:{local_name}".format(
      namespace_prefix=namespace_prefix,
      local_name=local_name,
    )

  if element_tag != "":
    return element_tag

  return "extension_{extension_index}".format(extension_index=extension_index)
