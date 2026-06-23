"""Display options for GPX track rendering on the map."""


class TrackDisplayOptions:
  """CLI-driven track decoration and startup settings for the map view."""

  def __init__(
    self,
    mark_hours_interval=None,
    mark_distance_interval=None,
    show_points=False,
    show_mark_labels=True,
    initial_gpx_filepath=None,
    as_timezone_name=None,
    show_dates_in_mark_labels=False,
    use_metric_units=False,
    exclude_idle_segments=False,
  ):
    """Capture display flags parsed from the gge command line."""

    self.mark_hours_interval = mark_hours_interval
    self.mark_distance_interval = mark_distance_interval
    self.show_points = show_points
    self.show_mark_labels = show_mark_labels
    self.initial_gpx_filepath = initial_gpx_filepath
    self.as_timezone_name = as_timezone_name
    self.show_dates_in_mark_labels = show_dates_in_mark_labels
    self.use_metric_units = use_metric_units
    self.exclude_idle_segments = exclude_idle_segments
