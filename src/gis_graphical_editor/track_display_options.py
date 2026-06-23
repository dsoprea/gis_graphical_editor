"""Display options for GPX track rendering on the map."""


class TrackDisplayOptions:
  """CLI-driven track decoration settings for the map view."""

  def __init__(
    self,
    mark_hours_interval=None,
    mark_distance_interval=None,
    show_points=False,
    show_mark_labels=True,
  ):
    self.mark_hours_interval = mark_hours_interval
    self.mark_distance_interval = mark_distance_interval
    self.show_points = show_points
    self.show_mark_labels = show_mark_labels
