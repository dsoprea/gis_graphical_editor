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
import gis_graphical_editor.segment_list_panel
import gis_graphical_editor.time_slider_panel
import gis_graphical_editor.track_analysis
import gis_graphical_editor.track_display_options
import gis_graphical_editor.track_metadata_panel

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
    self._main_frame.grid_rowconfigure(0, weight=1)
    self._main_frame.grid_columnconfigure(0, weight=1)
    self._content_paned = None
    self._map_column_frame = None
    self._map_widget = None
    self._file_menu = None
    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None
    self._slider_pointer_icon = None
    self._time_slider_panel = None
    self._segment_list_panel = None
    self._right_sidebar_frame = None
    self._track_metadata_panel = None
    self._last_slider_timestamp = None
    self._right_sidebar_panel_width = None
    self._slider_position_marker = None
    self._loaded_gpx_points = None
    self._loaded_gpx_segments = None

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
      gpx_segments = \
        gis_graphical_editor.gpx_utility.load_track_point_segments_from_gpx(gpx_path)
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

      for segment_points in gpx_segments:
        segment_conversion_result = \
          gis_graphical_editor.gpx_utility.convert_gpx_point_timestamps_to_timezone(
            segment_points,
            self._track_display_options.as_timezone_name)

        if segment_conversion_result[1]:
          encountered_naive_timestamp = True

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

    if not gis_graphical_editor.track_analysis.has_timestamps(gpx_points):
      message = "GPX file has no timestamps, so the time slider cannot be shown."
      tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

    self._loaded_gpx_segments = gpx_segments
    self._display_gpx_points(gpx_points)

  def _ensure_content_paned(self):
    """Create the horizontal split between the map column and right sidebar."""

    if self._content_paned is not None:
      return

    self._content_paned = tkinter.PanedWindow(
      self._main_frame,
      orient=tkinter.HORIZONTAL,
      sashwidth=4,
    )
    self._content_paned.grid(row=0, column=0, sticky="nsew")
    self._content_paned.bind("<Configure>", self._handle_content_paned_configure)

  def _handle_content_paned_configure(self, event):
    """Keep the right sidebar at the computed width when the window is resized."""

    if self._right_sidebar_panel_width is None:
      return

    self._position_content_paned_sash(self._right_sidebar_panel_width)

  def _ensure_map_widget(self):
    """Create the OSM map widget on first use and bind map interactions."""

    if self._map_widget is not None:
      return

    self._ensure_content_paned()
    self._map_column_frame = tkinter.Frame(self._content_paned)
    self._content_paned.add(self._map_column_frame, stretch="always")

    self._map_widget = tkintermapview.TkinterMapView(self._map_column_frame, corner_radius=0)
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

  def _remove_track_metadata_panel(self):
    """Destroy the optional metadata panel when the slider is unavailable."""

    if self._track_metadata_panel is None:
      return

    self._track_metadata_panel.pack_forget()
    self._track_metadata_panel.destroy()
    self._track_metadata_panel = None

  def _remove_segment_list_panel(self):
    """Destroy the optional segment list panel when unloading a track."""

    if self._segment_list_panel is None:
      return

    self._segment_list_panel.pack_forget()
    self._segment_list_panel.destroy()
    self._segment_list_panel = None

  def _remove_right_sidebar(self):
    """Destroy the right sidebar and every panel it contains."""

    self._remove_track_metadata_panel()
    self._remove_segment_list_panel()

    if self._right_sidebar_frame is None:
      return

    if self._content_paned is not None:
      self._content_paned.forget(self._right_sidebar_frame)

    self._right_sidebar_frame.destroy()
    self._right_sidebar_frame = None

  def _remove_time_slider_panel(self):
    """Destroy the optional time slider panel when unloading a track."""

    if self._time_slider_panel is None:
      return

    self._time_slider_panel.pack_forget()
    self._time_slider_panel.destroy()
    self._time_slider_panel = None
    self._remove_track_metadata_panel()

    if self._segment_list_panel is not None:
      self._segment_list_panel.set_highlighted_segment_index(None)

  def _remove_map_widget(self):
    """Tear down the map, slider, cached icons, and loaded point data."""

    if self._map_widget is None:
      return

    self._remove_time_slider_panel()
    self._remove_right_sidebar()

    if self._map_widget is not None:
      self._map_widget.pack_forget()
      self._map_widget.destroy()
      self._map_widget = None

    if self._map_column_frame is not None:
      if self._content_paned is not None:
        self._content_paned.forget(self._map_column_frame)

      self._map_column_frame.destroy()
      self._map_column_frame = None

    if self._content_paned is not None:
      self._content_paned.grid_forget()
      self._content_paned.destroy()
      self._content_paned = None

    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None
    self._slider_pointer_icon = None
    self._slider_position_marker = None
    self._loaded_gpx_points = None
    self._loaded_gpx_segments = None
    self._last_slider_timestamp = None
    self._right_sidebar_panel_width = None
    self._update_file_menu_state()

  def close_loaded_gpx_file(self):
    """Remove the current map view and return to the empty shell state."""

    if self._map_widget is None:
      return

    self._remove_map_widget()

  def _display_gpx_points(self, gpx_points):
    """Store loaded points, mount the segment panel, and draw the visible track."""

    self._ensure_map_widget()
    self._loaded_gpx_points = gpx_points
    self._setup_segment_list_panel()
    self._refresh_track_display()

  def _get_visible_gpx_points(self):
    """Return GPX points for checked segments, applying --no-idle filtering when set."""

    if self._segment_list_panel is not None:
      return self._segment_list_panel.get_selected_gpx_points()

    if self._loaded_gpx_segments is None:
      return self._loaded_gpx_points

    if not self._track_display_options.exclude_idle_segments:
      return self._loaded_gpx_points

    segment_summaries = \
      gis_graphical_editor.track_analysis.build_track_segment_summaries(
        self._loaded_gpx_segments,
        exclude_idle_segments=True,
        use_metric_units=self._track_display_options.use_metric_units,
      )
    visible_gpx_points = []

    for segment_summary in segment_summaries:
      for gpx_point in segment_summary.segment_points:
        visible_gpx_points.append(gpx_point)

    return visible_gpx_points

  def _handle_segment_selection_changed(self):
    """Redraw the map when the user toggles segment checkboxes."""

    self._refresh_track_display()

    if self._last_slider_timestamp is not None:
      self._update_track_metadata_for_slider_timestamp(self._last_slider_timestamp)
      self._update_segment_split_button_state(self._last_slider_timestamp)

  def _rebuild_loaded_gpx_points_from_segments(self):
    """Flatten _loaded_gpx_segments back into _loaded_gpx_points after a segment edit."""

    gpx_points = []

    for segment_points in self._loaded_gpx_segments:
      for gpx_point in segment_points:
        gpx_points.append(gpx_point)

    self._loaded_gpx_points = gpx_points

  def _handle_segment_split_requested(self):
    """Split the highlighted segment at the slider point into head and tail segments."""

    if self._loaded_gpx_segments is None or self._segment_list_panel is None:
      return

    if self._last_slider_timestamp is None:
      return

    visible_gpx_points = self._get_visible_gpx_points()
    nearest_gpx_point = \
      gis_graphical_editor.track_analysis.find_gpx_point_nearest_timestamp(
        visible_gpx_points,
        self._last_slider_timestamp,
      )
    segment_summary = self._segment_list_panel.find_segment_summary_for_gpx_point(
      nearest_gpx_point,
    )

    if segment_summary is None:
      return

    point_index = \
      gis_graphical_editor.track_analysis.find_gpx_point_index_in_segment_points(
        segment_summary.segment_points,
        nearest_gpx_point,
      )
    updated_segment_point_lists = \
      gis_graphical_editor.track_analysis.split_gpx_segment_point_lists_at_point_index(
        self._loaded_gpx_segments,
        segment_summary.segment_points,
        point_index,
      )

    if updated_segment_point_lists is None:
      return

    unchecked_first_points = \
      self._segment_list_panel.collect_unchecked_segment_first_points()
    self._loaded_gpx_segments = updated_segment_point_lists
    self._rebuild_loaded_gpx_points_from_segments()
    self._setup_segment_list_panel()

    if self._segment_list_panel is not None:
      self._segment_list_panel.apply_unchecked_segment_first_points(unchecked_first_points)

    self._refresh_track_display()

  def _update_segment_split_button_state(self, selected_timestamp):
    """Enable Split only when the slider sits on a splittable interior segment point."""

    if self._segment_list_panel is None or self._time_slider_panel is None:
      return

    if selected_timestamp is None:
      self._segment_list_panel.set_split_button_enabled(False)

      return

    visible_gpx_points = self._get_visible_gpx_points()
    nearest_gpx_point = \
      gis_graphical_editor.track_analysis.find_gpx_point_nearest_timestamp(
        visible_gpx_points,
        selected_timestamp,
      )
    segment_summary = self._segment_list_panel.find_segment_summary_for_gpx_point(
      nearest_gpx_point,
    )

    if segment_summary is None:
      self._segment_list_panel.set_split_button_enabled(False)

      return

    point_index = \
      gis_graphical_editor.track_analysis.find_gpx_point_index_in_segment_points(
        segment_summary.segment_points,
        nearest_gpx_point,
      )
    split_allowed = \
      gis_graphical_editor.track_analysis.is_segment_split_allowed_at_point_index(
        point_index,
        segment_summary.point_count,
      )
    self._segment_list_panel.set_split_button_enabled(split_allowed)

  def _refresh_track_display(self):
    """Draw the path, overlays, bounds, and slider for the currently visible points."""

    if self._map_widget is None:
      return

    visible_gpx_points = self._get_visible_gpx_points()

    self._map_widget.delete_all_path()
    self._map_widget.delete_all_marker()
    self._slider_position_marker = None

    if not visible_gpx_points:
      self._setup_time_slider_if_needed(visible_gpx_points)

      return

    track_points = []

    for gpx_point in visible_gpx_points:
      track_points.append((gpx_point.latitude, gpx_point.longitude))

    self._map_widget.set_path(
      track_points,
      color=_PATH_COLOR,
      width=_PATH_WIDTH,
    )

    if self._track_display_options.show_points:
      self._display_recorded_points(visible_gpx_points)

    if self._track_display_options.mark_hours_interval is not None \
        and gis_graphical_editor.track_analysis.has_timestamps(visible_gpx_points):
      hour_interval_markers = gis_graphical_editor.track_analysis.build_hour_interval_markers(
        visible_gpx_points,
        self._track_display_options.mark_hours_interval,
        self._track_display_options.show_dates_in_mark_labels,
        self._track_display_options.use_metric_units,
      )
      self._display_hour_interval_markers(hour_interval_markers)

    if self._track_display_options.mark_distance_interval is not None:
      distance_interval_markers = gis_graphical_editor.track_analysis.build_distance_interval_markers(
        visible_gpx_points,
        self._track_display_options.mark_distance_interval,
        self._track_display_options.show_dates_in_mark_labels,
        self._track_display_options.use_metric_units,
      )
      self._display_distance_interval_markers(distance_interval_markers)

    # Fit the map after the slider and sidebar layout have their final dimensions.
    self._setup_time_slider_if_needed(visible_gpx_points)
    self._schedule_fit_map_to_visible_track()

  def _schedule_fit_map_to_visible_track(self):
    """Defer map fitting until the map widget has its laid-out pixel dimensions."""

    self._root.after_idle(self._try_fit_map_to_visible_track)

  def _try_fit_map_to_visible_track(self):
    """Fit the map to the visible track once the map canvas has a real size."""

    if self._map_widget is None:
      return

    visible_gpx_points = self._get_visible_gpx_points()

    if not visible_gpx_points:
      return

    self._map_widget.update_idletasks()
    map_width = self._map_widget.winfo_width()
    map_height = self._map_widget.winfo_height()

    if map_width <= 1 or map_height <= 1:
      self._root.after(50, self._try_fit_map_to_visible_track)

      return

    # tkintermapview fits using its internal width/height, which update on <Configure>.
    if self._map_widget.width != map_width or self._map_widget.height != map_height:
      self._root.after(50, self._try_fit_map_to_visible_track)

      return

    track_points = []

    for gpx_point in visible_gpx_points:
      track_points.append((gpx_point.latitude, gpx_point.longitude))

    latitudes = [point[0] for point in track_points]
    longitudes = [point[1] for point in track_points]
    position_top_left = (max(latitudes), min(longitudes))
    position_bottom_right = (min(latitudes), max(longitudes))

    self._map_widget.fit_bounding_box(position_top_left, position_bottom_right)

  def _apply_right_sidebar_width(self, panel_width):
    """Keep the sidebar paned pane and child panels at panel_width."""

    self._right_sidebar_panel_width = panel_width

    if self._right_sidebar_frame is not None:
      self._right_sidebar_frame.config(width=panel_width)

    if self._content_paned is not None and self._right_sidebar_frame is not None:
      self._content_paned.paneconfigure(self._right_sidebar_frame, minsize=panel_width)

    if self._segment_list_panel is not None:
      self._segment_list_panel.set_panel_width(panel_width)

    if self._track_metadata_panel is not None:
      self._track_metadata_panel.set_panel_width(panel_width)

    self._schedule_content_paned_sash(panel_width)

  def _schedule_content_paned_sash(self, panel_width):
    """Defer sash placement until Tk has laid out the paned window."""

    self._root.after_idle(
      lambda: self._position_content_paned_sash(panel_width),
    )

  def _position_content_paned_sash(self, panel_width):
    """Pin the sash so the right sidebar is exactly panel_width pixels wide."""

    if self._content_paned is None or self._right_sidebar_frame is None:
      return

    self._content_paned.update_idletasks()
    paned_width = self._content_paned.winfo_width()

    if paned_width <= 1:
      self._root.after(
        50,
        lambda: self._position_content_paned_sash(panel_width),
      )

      return

    sash_position = paned_width - panel_width

    if sash_position < 0:
      sash_position = 0

    try:
      self._content_paned.sash_place(0, sash_position, 0)
    except tkinter.TclError:
      pass

  def _ensure_right_sidebar_frame(self, panel_width):
    """Create or resize the right sidebar container to panel_width."""

    self._ensure_content_paned()

    if self._right_sidebar_frame is not None:
      self._apply_right_sidebar_width(panel_width)

      return

    self._right_sidebar_frame = tkinter.Frame(self._content_paned, width=panel_width)
    self._right_sidebar_frame.pack_propagate(False)
    self._content_paned.add(
      self._right_sidebar_frame,
      stretch="never",
      minsize=panel_width,
    )
    self._apply_right_sidebar_width(panel_width)

  def _setup_segment_list_panel(self):
    """Mount the right-side segment checklist when the loaded GPX has segments."""

    self._remove_right_sidebar()

    if self._loaded_gpx_segments is None:
      return

    segment_summaries = \
      gis_graphical_editor.track_analysis.build_track_segment_summaries(
        self._loaded_gpx_segments,
        self._track_display_options.exclude_idle_segments,
        self._track_display_options.use_metric_units,
      )

    if not segment_summaries:
      return

    segment_labels = []

    for segment_summary in segment_summaries:
      segment_label = \
        gis_graphical_editor.track_analysis.format_track_segment_interval_label(
          segment_summary,
          self._track_display_options.use_metric_units,
          self._track_display_options.exclude_idle_segments,
        )
      segment_labels.append(segment_label)

    panel_width = gis_graphical_editor.segment_list_panel.compute_panel_width(segment_labels)
    self._ensure_right_sidebar_frame(panel_width)
    self._segment_list_panel = gis_graphical_editor.segment_list_panel.SegmentListPanel(
      self._right_sidebar_frame,
      segment_summaries,
      self._handle_segment_selection_changed,
      self._handle_segment_split_requested,
      panel_width,
      self._track_display_options.use_metric_units,
      self._track_display_options.exclude_idle_segments,
    )
    self._segment_list_panel.pack(side=tkinter.BOTTOM, fill=tkinter.Y, expand=True)

  def _setup_track_metadata_panel_if_needed(self, gpx_points):
    """Mount point and segment metadata boxes when the track has a timestamp range."""

    self._remove_track_metadata_panel()

    timestamp_range = gis_graphical_editor.track_analysis.get_timestamp_range(gpx_points)

    if timestamp_range is None:
      return

    if self._right_sidebar_frame is None:
      return

    if self._segment_list_panel is None:
      return

    panel_width = self._right_sidebar_panel_width
    self._track_metadata_panel = \
      gis_graphical_editor.track_metadata_panel.TrackMetadataPanel(
        self._right_sidebar_frame,
        panel_width,
      )
    self._track_metadata_panel.pack(side=tkinter.TOP, fill=tkinter.X)
    self._segment_list_panel.pack_forget()
    self._segment_list_panel.pack(side=tkinter.BOTTOM, fill=tkinter.Y, expand=True)
    self._apply_right_sidebar_width(panel_width)

    if self._last_slider_timestamp is not None:
      self._update_track_metadata_for_slider_timestamp(self._last_slider_timestamp)

  def _setup_time_slider_if_needed(self, gpx_points):
    """Mount or refresh the time slider when timestamps span a usable range."""

    timestamp_range = gis_graphical_editor.track_analysis.get_timestamp_range(gpx_points)

    if timestamp_range is None:
      self._remove_time_slider_panel()

      return

    earliest_timestamp, latest_timestamp = timestamp_range
    timed_gpx_points = \
      gis_graphical_editor.track_analysis.collect_timed_gpx_points(gpx_points)

    if self._time_slider_panel is not None:
      self._time_slider_panel.update_timed_gpx_points(
        timed_gpx_points,
        earliest_timestamp,
        latest_timestamp,
      )
      self._setup_track_metadata_panel_if_needed(gpx_points)

      if self._last_slider_timestamp is not None:
        self._time_slider_panel.set_selected_timestamp(self._last_slider_timestamp)
      else:
        self._update_segment_split_button_state(None)

      return

    self._time_slider_panel = gis_graphical_editor.time_slider_panel.TimeSliderPanel(
      self._map_column_frame,
      earliest_timestamp,
      latest_timestamp,
      timed_gpx_points,
      self._handle_slider_timestamp_changed,
    )
    self._time_slider_panel.pack(side=tkinter.TOP, fill=tkinter.X, before=self._map_widget)
    self._setup_track_metadata_panel_if_needed(gpx_points)

    if self._last_slider_timestamp is not None:
      self._time_slider_panel.set_selected_timestamp(self._last_slider_timestamp)
    else:
      self._update_segment_split_button_state(None)

  def _update_track_metadata_for_slider_timestamp(self, selected_timestamp):
    """Refresh the point and segment metadata boxes for the slider time."""

    if self._track_metadata_panel is None:
      return

    visible_gpx_points = self._get_visible_gpx_points()
    nearest_gpx_point = gis_graphical_editor.track_analysis.find_gpx_point_nearest_timestamp(
      visible_gpx_points,
      selected_timestamp,
    )
    segment_summary = None

    if self._segment_list_panel is not None:
      segment_summary = self._segment_list_panel.find_segment_summary_for_gpx_point(
        nearest_gpx_point,
      )

    point_metadata_lines = gis_graphical_editor.track_analysis.format_gpx_point_metadata_lines(
      nearest_gpx_point,
    )
    segment_metadata_lines = \
      gis_graphical_editor.track_analysis.format_segment_summary_metadata_lines(
        segment_summary,
        self._track_display_options.use_metric_units,
      )

    self._track_metadata_panel.set_point_metadata(point_metadata_lines)
    self._track_metadata_panel.set_segment_metadata(segment_metadata_lines)

  def _update_segment_list_slider_highlight(self, selected_timestamp):
    """Highlight the segment row that contains the slider's current timestamp."""

    if self._segment_list_panel is None:
      return

    segment_summaries = self._segment_list_panel.get_segment_summaries()
    segment_index = \
      gis_graphical_editor.track_analysis.find_track_segment_summary_index_at_timestamp(
        segment_summaries,
        selected_timestamp,
      )
    self._segment_list_panel.set_highlighted_segment_index(segment_index)

  def _handle_slider_timestamp_changed(self, selected_timestamp):
    """Move the slider pointer and keep the selected track point on screen."""

    if self._loaded_gpx_points is None or self._map_widget is None:
      return

    self._last_slider_timestamp = selected_timestamp
    visible_gpx_points = self._get_visible_gpx_points()

    track_position = gis_graphical_editor.track_analysis.find_position_at_timestamp(
      visible_gpx_points,
      selected_timestamp,
    )

    if track_position is None:
      return

    latitude, longitude = track_position
    self._update_slider_position_marker(latitude, longitude)
    self._ensure_map_shows_position(latitude, longitude)
    self._update_track_metadata_for_slider_timestamp(selected_timestamp)
    self._update_segment_list_slider_highlight(selected_timestamp)
    self._update_segment_split_button_state(selected_timestamp)

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
