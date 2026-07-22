"""Tests for gpx_utility segment-name and waypoint helpers."""

import os

import gpxpy
import gpxpy.gpx

import gis_graphical_editor.gpx_utility


def test_parse_ref_segment_name_dotted_expression_returns_three_components():
  namespace, node, label_attribute = \
    gis_graphical_editor.gpx_utility.parse_ref_segment_name_dotted_expression(
      "autolog.segment.name",
    )

  assert namespace == "autolog"
  assert node == "segment"
  assert label_attribute == "name"


def test_parse_ref_segment_name_dotted_expression_rejects_wrong_component_count():
  raised_value_error = False

  try:
    gis_graphical_editor.gpx_utility.parse_ref_segment_name_dotted_expression("only.two")
  except ValueError:
    raised_value_error = True

  assert raised_value_error is True


def test_load_track_segment_label_texts_from_gpx_reads_circuit_lap_label(tmp_path):
  gpx_path = os.path.join(str(tmp_path), "circuit_lap.gpx")
  gpx_text = """<?xml version="1.0"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1" xmlns:circuit="http://example.com/circuit">
<trk>
<name>Trip 336</name>
<trkseg>
<extensions>
<circuit:lap regionId="1" regionName="The Greens 1" label="The Greens 1"/>
</extensions>
<trkpt lat="26.5756001" lon="-80.1347883">
<ele>-19.600000381469727</ele>
<time>2026-07-22T00:30:38Z</time>
</trkpt>
</trkseg>
</trk>
</gpx>
"""
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  segment_label_texts = \
    gis_graphical_editor.gpx_utility.load_track_segment_label_texts_from_gpx(
      gpx_path,
      "circuit",
      "lap",
      "label",
    )

  assert segment_label_texts == ["The Greens 1"]


def test_load_track_segment_label_texts_from_gpx_resolves_circuit_app_xmlns_prefix(tmp_path):
  gpx_path = os.path.join(str(tmp_path), "circuit_app_lap.gpx")
  gpx_text = """<?xml version="1.0"?>
<gpx version="1.1" creator="Circuit CLI" xmlns="http://www.topografix.com/GPX/1/1" xmlns:circuit="https://circuit.app/ns/gpx">
<trk>
<name>Trip 336</name>
<trkseg>
<extensions>
<circuit:lap regionId="1" regionName="The Greens 1" label="The Greens 1"/>
</extensions>
<trkpt lat="26.5756001" lon="-80.1347883">
<time>2026-07-22T00:30:38Z</time>
</trkpt>
</trkseg>
<trkseg>
<extensions>
<circuit:lap regionId="2" regionName="Lake Nona" label="Lake Nona"/>
</extensions>
<trkpt lat="26.5751269" lon="-80.1310773">
<time>2026-07-22T00:33:19Z</time>
</trkpt>
</trkseg>
</trk>
</gpx>
"""
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  segment_label_texts = \
    gis_graphical_editor.gpx_utility.load_track_segment_label_texts_from_gpx(
      gpx_path,
      "circuit",
      "lap",
      "label",
    )

  assert segment_label_texts == ["The Greens 1", "Lake Nona"]


def test_resolve_gpx_extension_namespace_uri_reads_xmlns_prefix():
  gpx_text = '<gpx xmlns:circuit="https://circuit.app/ns/gpx"></gpx>'

  namespace_uri = gis_graphical_editor.gpx_utility.resolve_gpx_extension_namespace_uri(
    gpx_text,
    "circuit",
  )

  assert namespace_uri == "https://circuit.app/ns/gpx"


def test_collect_nonempty_track_segment_region_names_omits_empty_labels():
  region_names = \
    gis_graphical_editor.gpx_utility.collect_nonempty_track_segment_region_names(
      ["The Greens 1", "", "Bahia Honda"],
    )

  assert region_names == ["The Greens 1", "Bahia Honda"]


def test_load_track_segment_label_texts_from_gpx_reads_extension_attribute(tmp_path):
  gpx_path = os.path.join(str(tmp_path), "segment_labels.gpx")
  gpx_text = """<?xml version="1.0"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1" xmlns:autolog="http://example.com/autolog">
<trk>
<trkseg>
<extensions><autolog:segment name="Key West" category="Misc"/></extensions>
<trkpt lat="40.0" lon="-105.0"><time>2024-06-01T08:00:00Z</time></trkpt>
</trkseg>
<trkseg>
<extensions><autolog:segment name="Bahia Honda" category="Misc"/></extensions>
<trkpt lat="41.0" lon="-106.0"><time>2024-06-01T09:00:00Z</time></trkpt>
</trkseg>
</trk>
</gpx>
"""
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  segment_label_texts = \
    gis_graphical_editor.gpx_utility.load_track_segment_label_texts_from_gpx(
      gpx_path,
      "autolog",
      "segment",
      "name",
    )

  assert segment_label_texts == ["Key West", "Bahia Honda"]


def test_load_gpx_waypoints_from_gpx_returns_waypoints_alongside_tracks(tmp_path):
  gpx_document = gpxpy.gpx.GPX()
  track = gpxpy.gpx.GPXTrack()
  segment = gpxpy.gpx.GPXTrackSegment()
  segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=40.0, longitude=-105.0))
  track.segments.append(segment)
  gpx_document.tracks.append(track)
  gpx_document.waypoints.append(
    gpxpy.gpx.GPXWaypoint(latitude=40.5, longitude=-105.5, name="Start"),
  )

  gpx_path = os.path.join(str(tmp_path), "waypoints.gpx")
  gpx_text = gpx_document.to_xml()
  with open(gpx_path, "w", encoding="utf-8") as gpx_file:
    gpx_file.write(gpx_text)

  waypoint_points = gis_graphical_editor.gpx_utility.load_gpx_waypoints_from_gpx(gpx_path)

  assert len(waypoint_points) == 1
  assert waypoint_points[0].additional_metadata["name"] == "Start"


def test_build_gpx_waypoint_tooltip_text_returns_name_when_present():
  gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(
    40.0,
    -105.0,
    None,
    additional_metadata={"name": "Start: Key West"},
  )

  tooltip_text = gis_graphical_editor.gpx_utility.build_gpx_waypoint_tooltip_text(gpx_point)

  assert tooltip_text == "Start: Key West"


def test_build_gpx_waypoint_tooltip_text_returns_empty_when_name_missing():
  gpx_point = gis_graphical_editor.gpx_utility.GpxPointRecord(40.0, -105.0, None)

  tooltip_text = gis_graphical_editor.gpx_utility.build_gpx_waypoint_tooltip_text(gpx_point)

  assert tooltip_text == ""
