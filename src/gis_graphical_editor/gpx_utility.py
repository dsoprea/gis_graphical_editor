"""Load and write GPX files as point records with coordinates and timestamps."""

import datetime
import zoneinfo

import gpxpy
import gpxpy.gpx

_INTEGER_GPX_METADATA_FIELD_NAMES = frozenset({"satellites", "dgps_id"})
_STRING_GPX_METADATA_FIELD_NAMES = frozenset({
  "name",
  "comment",
  "description",
  "source",
  "symbol",
  "type",
  "type_of_gpx_fix",
  "link",
  "link_text",
})


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


def write_track_point_segments_to_gpx(gpx_path, segment_point_lists):
  """Write segment_point_lists to gpx_path as one GPX track with one segment per list."""

  gpx_document = gpxpy.gpx.GPX()
  track = gpxpy.gpx.GPXTrack()

  # Emit one GPX track segment per non-empty in-memory segment list.
  for segment_points in segment_point_lists:
    if not segment_points:
      continue

    segment = gpxpy.gpx.GPXTrackSegment()

    for gpx_point in segment_points:
      track_point = gpxpy.gpx.GPXTrackPoint(
        latitude=gpx_point.latitude,
        longitude=gpx_point.longitude,
        time=gpx_point.timestamp,
      )
      _apply_additional_metadata_to_gpx_track_point(
        track_point,
        gpx_point.additional_metadata,
      )
      segment.points.append(track_point)

    track.segments.append(segment)

  gpx_document.tracks.append(track)
  gpx_document.version = "1.0"
  gpx_text = gpx_document.to_xml()

  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)


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


def _apply_additional_metadata_to_gpx_track_point(track_point, additional_metadata):
  """Copy string metadata values onto a gpxpy track point when the field exists."""

  metadata_keys = sorted(additional_metadata.keys())

  # Restore each known standard GPX field from the metadata map.
  for metadata_key in metadata_keys:
    if _is_extension_derived_metadata_key(metadata_key):
      continue

    if not hasattr(track_point, metadata_key):
      continue

    metadata_value = additional_metadata[metadata_key]
    coerced_value = _coerce_gpx_metadata_value(metadata_key, metadata_value)
    setattr(track_point, metadata_key, coerced_value)


def _is_extension_derived_metadata_key(metadata_key):
  """Return True when metadata_key came from a GPX extensions XML element."""

  if ":" in metadata_key:
    return True

  if metadata_key.startswith("extension_"):
    return True

  return False


def _coerce_gpx_metadata_value(field_name, metadata_value):
  """Return a gpxpy-typed value for one string metadata entry."""

  if field_name in _STRING_GPX_METADATA_FIELD_NAMES:
    return metadata_value

  if field_name in _INTEGER_GPX_METADATA_FIELD_NAMES:
    return int(float(metadata_value))

  try:
    return float(metadata_value)
  except ValueError:
    return metadata_value
