"""Captured map overlay records and GPX export for overlay mode."""

import copy
import datetime
import re
import xml.etree.ElementTree

import gpxpy
import gpxpy.gpx

import gis_graphical_editor.gpx_utility

_OVERLAY_EXTENSION_NAMESPACE = "https://gis-graphical-editor.local/ns/overlay"
_OVERLAY_ID_EXTENSION_TAG = "{namespace}:id".format(namespace=_OVERLAY_EXTENSION_NAMESPACE)
_OVERLAY_DESCRIPTION_EXTENSION_TAG = "{namespace}:description".format(
  namespace=_OVERLAY_EXTENSION_NAMESPACE,
)
_FILENAME_INCOMPATIBLE_CHARACTER_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class CapturedOverlay:
  """One pushed overlay with an id, description, and ordered captured locations."""

  def __init__(self, overlay_id, overlay_description, location_records):
    """Store overlay metadata and a list of GpxPointRecord captured locations."""

    self.overlay_id = overlay_id
    self.overlay_description = overlay_description
    self.location_records = list(location_records)


def copy_gpx_point_record(gpx_point_record):
  """Return a shallow copy of one GpxPointRecord including metadata."""

  additional_metadata = copy.copy(gpx_point_record.additional_metadata)

  return gis_graphical_editor.gpx_utility.GpxPointRecord(
    gpx_point_record.latitude,
    gpx_point_record.longitude,
    gpx_point_record.timestamp,
    additional_metadata,
  )


def build_suggested_overlay_gpx_filename(description, export_timestamp=None):
  """Return TIMESTAMP_DESCRIPTION.gpx with unsafe filename characters underscored."""

  if export_timestamp is None:
    export_timestamp = datetime.datetime.now()

  timestamp_text = export_timestamp.strftime("%Y%m%d-%H%M%S")
  safe_description_text = _FILENAME_INCOMPATIBLE_CHARACTER_PATTERN.sub("_", description)

  if safe_description_text == "":
    safe_description_text = "overlay"

  return "{timestamp_text}_{safe_description_text}.gpx".format(
    timestamp_text=timestamp_text,
    safe_description_text=safe_description_text,
  )


def write_captured_overlays_to_gpx(gpx_filepath, gpx_description, captured_overlays):
  """Write each captured overlay as one GPX trkseg with extension metadata."""

  gpx_document = gpxpy.gpx.GPX()
  gpx_document.name = gpx_description
  gpx_document.description = gpx_description
  track = gpxpy.gpx.GPXTrack()
  track.name = gpx_description

  # Emit one track segment per pushed overlay.
  for captured_overlay in captured_overlays:
    segment = gpxpy.gpx.GPXTrackSegment()
    segment.extensions.extend(
      _build_overlay_extension_elements(
        captured_overlay.overlay_id,
        captured_overlay.overlay_description,
      ),
    )

    for location_record in captured_overlay.location_records:
      track_point = gpxpy.gpx.GPXTrackPoint(
        latitude=location_record.latitude,
        longitude=location_record.longitude,
        time=location_record.timestamp,
      )
      gis_graphical_editor.gpx_utility._apply_additional_metadata_to_gpx_track_point(
        track_point,
        location_record.additional_metadata,
      )
      _apply_extension_metadata_to_gpx_track_point(
        track_point,
        location_record.additional_metadata,
      )
      segment.points.append(track_point)

    track.segments.append(segment)

  gpx_document.tracks.append(track)
  gpx_document.version = "1.0"
  gpx_text = gpx_document.to_xml()

  with open(gpx_filepath, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)


def _build_overlay_extension_elements(overlay_id, overlay_description):
  """Return GPX extension elements describing overlay id and description."""

  overlay_id_element = xml.etree.ElementTree.Element(_OVERLAY_ID_EXTENSION_TAG)
  overlay_id_element.text = overlay_id
  overlay_description_element = xml.etree.ElementTree.Element(_OVERLAY_DESCRIPTION_EXTENSION_TAG)
  overlay_description_element.text = overlay_description

  return [overlay_id_element, overlay_description_element]


def _apply_extension_metadata_to_gpx_track_point(track_point, additional_metadata):
  """Copy extension-derived metadata keys onto one GPX track point."""

  extension_children = []

  # Serialize colon-prefixed metadata keys as simple extension elements.
  for metadata_key in sorted(additional_metadata.keys()):
    if not gis_graphical_editor.gpx_utility._is_extension_derived_metadata_key(metadata_key):
      continue

    metadata_value = additional_metadata[metadata_key]

    if metadata_value == "":
      continue

    extension_tag = metadata_key

    if ":" not in metadata_key:
      extension_tag = "{namespace}:{metadata_key}".format(
        namespace=_OVERLAY_EXTENSION_NAMESPACE,
        metadata_key=metadata_key,
      )

    extension_element = xml.etree.ElementTree.Element(extension_tag)
    extension_element.text = metadata_value
    extension_children.append(extension_element)

  if not extension_children:
    return

  track_point.extensions.extend(extension_children)
