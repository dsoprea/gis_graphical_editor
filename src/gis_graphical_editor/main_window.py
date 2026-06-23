"""Main application window with an OSM map and GPX loading."""

import logging
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox

import tkintermapview
import tkintermapview.utility_functions

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.map_icon_utility
import gis_graphical_editor.time_slider_panel
import gis_graphical_editor.track_analysis
import gis_graphical_editor.track_display_options

_LOGGER = logging.getLogger(__name__)

_WINDOW_TITLE = "GIS Graphical Editor"
_GPX_FILE_TYPE_LABEL = "GPX files"
_GPX_FILE_TYPE_PATTERN = "*.gpx"
_ALL_FILE_TYPE_LABEL = "All files"
_ALL_FILE_TYPE_PATTERN = "*.*"
_FILE_MENU_CLOSE_INDEX = 1
_PATH_COLOR = "#0066CC"
_PATH_WIDTH = 9
_ORANGE_MARKER_TEXT = "#CC5500"
_RED_MARKER_TEXT = "#990000"
_MAP_VISIBILITY_MARGIN = 0.05


class MainWindow:
  """Tkinter shell that displays GPX tracks on an OpenStreetMap tile layer."""

  def __init__(self, root, track_display_options=None):
    """Wire menus, keyboard shortcuts, and deferred GPX loading into root."""

    self._root = root
    self._root.title(_WINDOW_TITLE)
    self._root.geometry("1024x768")

    if track_display_options is None:
      track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions()

    self._track_display_options = track_display_options
    self._main_frame = tkinter.Frame(self._root)
    self._main_frame.pack(fill=tkinter.BOTH, expand=True)
    self._map_widget = None
    self._file_menu = None
    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None
    self._slider_pointer_icon = None
    self._time_slider_panel = None
    self._slider_position_marker = None
    self._loaded_gpx_points = None

    self._build_menu_bar()
    self._bind_menu_accelerators()
    self._update_file_menu_state()

    self._root.after(0, self._load_initial_gpx_file)

  def _load_initial_gpx_file(self):
    """Open --filepath on startup or prompt for a GPX file when none was given."""

    if self._track_display_options.initial_gpx_filepath is not None:
      self.load_gpx_file(self._track_display_options.initial_gpx_filepath)

      return

    self.prompt_and_load_gpx_file()

  def _build_menu_bar(self):
    """Create the File menu with Load, Close, and Exit actions."""

    menu_bar = tkinter.Menu(self._root)
    self._root.config(menu=menu_bar)

    self._file_menu = tkinter.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=self._file_menu, underline=0)

    self._file_menu.add_command(
      label="Load",
      command=self.prompt_and_load_gpx_file,
      accelerator="Ctrl+O",
      underline=0,
    )
    self._file_menu.add_command(
      label="Close",
      command=self.close_loaded_gpx_file,
      accelerator="Ctrl+W",
      underline=0,
    )
    self._file_menu.add_separator()
    self._file_menu.add_command(
      label="Exit",
      command=self.exit_application,
      accelerator="Ctrl+Q",
      underline=1,
    )

  def _bind_menu_accelerators(self):
    """Bind keyboard shortcuts that mirror File menu accelerators."""

    self._root.bind("<Control-o>", self._handle_load_gpx_shortcut)
    self._root.bind("<Control-O>", self._handle_load_gpx_shortcut)
    self._root.bind("<Control-w>", self._handle_close_gpx_shortcut)
    self._root.bind("<Control-W>", self._handle_close_gpx_shortcut)
    self._root.bind("<Control-q>", self._handle_exit_shortcut)
    self._root.bind("<Control-Q>", self._handle_exit_shortcut)

  def _update_file_menu_state(self):
    """Enable Close only while a map with loaded track data is visible."""

    if self._file_menu is None:
      return

    if self._map_widget is None:
      close_state = tkinter.DISABLED
    else:
      close_state = tkinter.NORMAL

    self._file_menu.entryconfig(_FILE_MENU_CLOSE_INDEX, state=close_state)

  def _handle_load_gpx_shortcut(self, event):
    """Open the GPX file picker from the Ctrl+O shortcut."""

    self.prompt_and_load_gpx_file()

    return "break"

  def _handle_close_gpx_shortcut(self, event):
    """Unload the current track from the Ctrl+W shortcut."""

    self.close_loaded_gpx_file()

    return "break"

  def _handle_exit_shortcut(self, event):
    """Quit the application from the Ctrl+Q shortcut."""

    self.exit_application()

    return "break"

  def prompt_and_load_gpx_file(self):
    """Ask the user to choose a GPX file and load it when selected."""

    gpx_path = tkinter.filedialog.askopenfilename(
      parent=self._root,
      title="Load GPX file",
      filetypes=[
        (_GPX_FILE_TYPE_LABEL, _GPX_FILE_TYPE_PATTERN),
        (_ALL_FILE_TYPE_LABEL, _ALL_FILE_TYPE_PATTERN),
      ],
    )

    if not gpx_path:
      return

    self.load_gpx_file(gpx_path)

  def load_gpx_file(self, gpx_path):
    """Parse gpx_path and render the track with any enabled CLI overlays."""

    if not os.path.isfile(gpx_path):
      message = "File not found: {path}".format(path=gpx_path)
      tkinter.messagebox.showerror("Load GPX", message, parent=self._root)

      return

    try:
      gpx_points = gis_graphical_editor.gpx_utility.load_gpx_points_from_gpx(gpx_path)
    except Exception as error:
      message = "Could not read GPX file:\n{error}".format(error=error)
      _LOGGER.exception(message)
      tkinter.messagebox.showerror("Load GPX", message, parent=self._root)

      return

    if not gpx_points:
      message = "No track points found in {path}".format(path=gpx_path)
      tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

      return

    # Convert timestamps for display when --as-timezone was requested.
    if self._track_display_options.as_timezone_name is not None:
      conversion_result = \
        gis_graphical_editor.gpx_utility.convert_gpx_point_timestamps_to_timezone(
          gpx_points,
          self._track_display_options.as_timezone_name)
      gpx_points = conversion_result[0]
      encountered_naive_timestamp = conversion_result[1]

      if encountered_naive_timestamp:
        message = \
          "This GPX file has timestamps without timezone information. " \
          "They will be interpreted as UTC before converting to {timezone_name}.".format(
            timezone_name=self._track_display_options.as_timezone_name)
        tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

    # Warn when timestamp-dependent CLI options cannot be honored.
    if self._track_display_options.mark_hours_interval is not None:
      if not gis_graphical_editor.track_analysis.has_timestamps(gpx_points):
        message = "GPX file has no timestamps, so --mark-hours markers cannot be drawn."
        tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

    if self._track_display_options.show_time_slider:
      if not gis_graphical_editor.track_analysis.has_timestamps(gpx_points):
        message = "GPX file has no timestamps, so --slider cannot be used."
        tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

    self._display_gpx_points(gpx_points)

  def _ensure_map_widget(self):
    """Create the OSM map widget on first use and bind map interactions."""

    if self._map_widget is not None:
      return

    self._map_widget = tkintermapview.TkinterMapView(self._main_frame, corner_radius=0)
    self._map_widget.pack(fill=tkinter.BOTH, expand=True)
    self._bind_map_widget_events()
    self._update_file_menu_state()

  def _bind_map_widget_events(self):
    """Attach canvas handlers for map-specific mouse gestures."""

    self._map_widget.canvas.bind("<Double-Button-1>", self._handle_map_double_click)

  def _handle_map_double_click(self, event):
    """Zoom in one level centered on the double-clicked map location."""

    relative_mouse_x = event.x / self._map_widget.width
    relative_mouse_y = event.y / self._map_widget.height
    new_zoom = self._map_widget.zoom + 1

    self._map_widget.set_zoom(
      new_zoom,
      relative_pointer_x=relative_mouse_x,
      relative_pointer_y=relative_mouse_y,
    )

  def _remove_time_slider_panel(self):
    """Destroy the optional time slider panel when unloading a track."""

    if self._time_slider_panel is None:
      return

    self._time_slider_panel.pack_forget()
    self._time_slider_panel.destroy()
    self._time_slider_panel = None

  def _remove_map_widget(self):
    """Tear down the map, slider, cached icons, and loaded point data."""

    if self._map_widget is None:
      return

    self._remove_time_slider_panel()
    self._map_widget.pack_forget()
    self._map_widget.destroy()
    self._map_widget = None
    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None
    self._slider_pointer_icon = None
    self._slider_position_marker = None
    self._loaded_gpx_points = None
    self._update_file_menu_state()

  def close_loaded_gpx_file(self):
    """Remove the current map view and return to the empty shell state."""

    if self._map_widget is None:
      return

    self._remove_map_widget()

  def _display_gpx_points(self, gpx_points):
    """Draw the track path, optional overlays, bounds fit, and time slider."""

    self._ensure_map_widget()

    self._map_widget.delete_all_path()
    self._map_widget.delete_all_marker()
    self._slider_position_marker = None
    self._loaded_gpx_points = gpx_points

    track_points = []

    for gpx_point in gpx_points:
      track_points.append((gpx_point.latitude, gpx_point.longitude))

    self._map_widget.set_path(
      track_points,
      color=_PATH_COLOR,
      width=_PATH_WIDTH,
    )

    if self._track_display_options.show_points:
      self._display_recorded_points(gpx_points)

    if self._track_display_options.mark_hours_interval is not None \
        and gis_graphical_editor.track_analysis.has_timestamps(gpx_points):
      hour_interval_markers = gis_graphical_editor.track_analysis.build_hour_interval_markers(
        gpx_points,
        self._track_display_options.mark_hours_interval,
        self._track_display_options.show_dates_in_mark_labels,
      )
      self._display_hour_interval_markers(hour_interval_markers)

    if self._track_display_options.mark_distance_interval is not None:
      distance_interval_markers = gis_graphical_editor.track_analysis.build_distance_interval_markers(
        gpx_points,
        self._track_display_options.mark_distance_interval,
        self._track_display_options.show_dates_in_mark_labels,
      )
      self._display_distance_interval_markers(distance_interval_markers)

    # Fit the map to the full track extent before optional slider setup.
    latitudes = [point[0] for point in track_points]
    longitudes = [point[1] for point in track_points]
    position_top_left = (max(latitudes), min(longitudes))
    position_bottom_right = (min(latitudes), max(longitudes))

    self._map_widget.fit_bounding_box(position_top_left, position_bottom_right)
    self._setup_time_slider_if_needed(gpx_points)

  def _setup_time_slider_if_needed(self, gpx_points):
    """Mount the --slider panel when timestamps span a usable range."""

    self._remove_time_slider_panel()

    if not self._track_display_options.show_time_slider:
      return

    timestamp_range = gis_graphical_editor.track_analysis.get_timestamp_range(gpx_points)

    if timestamp_range is None:
      return

    earliest_timestamp, latest_timestamp = timestamp_range
    self._time_slider_panel = gis_graphical_editor.time_slider_panel.TimeSliderPanel(
      self._main_frame,
      earliest_timestamp,
      latest_timestamp,
      self._handle_slider_timestamp_changed,
    )
    self._time_slider_panel.pack(side=tkinter.TOP, fill=tkinter.X, before=self._map_widget)

  def _handle_slider_timestamp_changed(self, selected_timestamp):
    """Move the slider pointer and keep the selected track point on screen."""

    if self._loaded_gpx_points is None or self._map_widget is None:
      return

    track_position = gis_graphical_editor.track_analysis.find_position_at_timestamp(
      self._loaded_gpx_points,
      selected_timestamp,
    )

    if track_position is None:
      return

    latitude, longitude = track_position
    self._update_slider_position_marker(latitude, longitude)
    self._ensure_map_shows_position(latitude, longitude)

  def _update_slider_position_marker(self, latitude, longitude):
    """Create or reposition the large red dot for the current slider time."""

    if self._slider_pointer_icon is None:
      self._slider_pointer_icon = gis_graphical_editor.map_icon_utility.create_red_slider_pointer_icon()

    if self._slider_position_marker is None:
      self._slider_position_marker = self._map_widget.set_marker(
        latitude,
        longitude,
        icon=self._slider_pointer_icon,
        icon_anchor="center",
      )

      return

    self._slider_position_marker.set_position(latitude, longitude)

  def _ensure_map_shows_position(self, latitude, longitude):
    """Pan the map when the slider pointer would fall outside the visible tiles."""

    map_zoom = round(self._map_widget.zoom)
    top_left_latitude, top_left_longitude = tkintermapview.utility_functions.osm_to_decimal(
      self._map_widget.upper_left_tile_pos[0],
      self._map_widget.upper_left_tile_pos[1],
      map_zoom,
    )
    bottom_right_latitude, bottom_right_longitude = tkintermapview.utility_functions.osm_to_decimal(
      self._map_widget.lower_right_tile_pos[0],
      self._map_widget.lower_right_tile_pos[1],
      map_zoom,
    )
    latitude_span = abs(top_left_latitude - bottom_right_latitude)
    longitude_span = abs(bottom_right_longitude - top_left_longitude)
    latitude_margin = latitude_span * _MAP_VISIBILITY_MARGIN
    longitude_margin = longitude_span * _MAP_VISIBILITY_MARGIN

    minimum_latitude = min(top_left_latitude, bottom_right_latitude) + latitude_margin
    maximum_latitude = max(top_left_latitude, bottom_right_latitude) - latitude_margin
    minimum_longitude = min(top_left_longitude, bottom_right_longitude) + longitude_margin
    maximum_longitude = max(top_left_longitude, bottom_right_longitude) - longitude_margin

    latitude_visible = minimum_latitude <= latitude <= maximum_latitude
    longitude_visible = minimum_longitude <= longitude <= maximum_longitude

    if latitude_visible and longitude_visible:
      return

    self._map_widget.set_position(latitude, longitude)

  def _display_recorded_points(self, gpx_points):
    """Draw --points green dots at every recorded GPX coordinate."""

    if self._green_point_icon is None:
      self._green_point_icon = gis_graphical_editor.map_icon_utility.create_green_point_icon()

    for gpx_point in gpx_points:
      self._map_widget.set_marker(
        gpx_point.latitude,
        gpx_point.longitude,
        icon=self._green_point_icon,
        icon_anchor="center",
      )

  def _display_hour_interval_markers(self, hour_interval_markers):
    """Place orange --mark-hours dots and optional labels along the track."""

    if self._orange_interval_icon is None:
      self._orange_interval_icon = gis_graphical_editor.map_icon_utility.create_orange_interval_icon()

    for hour_interval_marker in hour_interval_markers:
      marker_arguments = {
        "icon": self._orange_interval_icon,
        "icon_anchor": "center",
      }

      if self._track_display_options.show_mark_labels:
        marker_arguments["text"] = hour_interval_marker.label
        marker_arguments["text_color"] = _ORANGE_MARKER_TEXT

      self._map_widget.set_marker(
        hour_interval_marker.latitude,
        hour_interval_marker.longitude,
        **marker_arguments,
      )

  def _display_distance_interval_markers(self, distance_interval_markers):
    """Place red --mark-distance dots and optional labels along the track."""

    if self._red_interval_icon is None:
      self._red_interval_icon = gis_graphical_editor.map_icon_utility.create_red_interval_icon()

    for distance_interval_marker in distance_interval_markers:
      marker_arguments = {
        "icon": self._red_interval_icon,
        "icon_anchor": "center",
      }

      if self._track_display_options.show_mark_labels:
        marker_arguments["text"] = distance_interval_marker.label
        marker_arguments["text_color"] = _RED_MARKER_TEXT

      self._map_widget.set_marker(
        distance_interval_marker.latitude,
        distance_interval_marker.longitude,
        **marker_arguments,
      )

  def exit_application(self):
    """Stop the Tk main loop and close the window."""

    self._root.quit()
