import datetime

import gis_graphical_editor.time_slider_panel


def test_format_slider_endpoint_timestamp_includes_timezone_name():
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
  label_text = gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(timestamp)

  assert label_text == "2024-06-01 08:00:00 UTC"


def test_format_slider_endpoint_timestamp_includes_numeric_offset():
  mountain_timezone = datetime.timezone(datetime.timedelta(hours=-6))
  timestamp = datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=mountain_timezone)
  label_text = gis_graphical_editor.time_slider_panel.format_slider_endpoint_timestamp(timestamp)

  assert label_text == "2024-06-01 08:00:00 UTC-06:00"
