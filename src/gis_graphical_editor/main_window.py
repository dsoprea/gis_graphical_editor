"""Main application window with an OSM map and GPX loading."""

import logging
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox

import tkintermapview

import gis_graphical_editor.gpx_utility
import gis_graphical_editor.map_icon_utility
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


class MainWindow:
  """Tkinter shell that displays GPX tracks on an OpenStreetMap tile layer."""

  def __init__(self, root, track_display_options=None):
    self._root = root
    self._root.title(_WINDOW_TITLE)
    self._root.geometry("1024x768")

    if track_display_options is None:
      track_display_options = gis_graphical_editor.track_display_options.TrackDisplayOptions()

    self._track_display_options = track_display_options
    self._map_widget = None
    self._file_menu = None
    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None

    self._build_menu_bar()
    self._bind_menu_accelerators()
    self._update_file_menu_state()

    self._root.after(0, self.prompt_and_load_gpx_file)

  def _build_menu_bar(self):
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
    self._root.bind("<Control-o>", self._handle_load_gpx_shortcut)
    self._root.bind("<Control-O>", self._handle_load_gpx_shortcut)
    self._root.bind("<Control-w>", self._handle_close_gpx_shortcut)
    self._root.bind("<Control-W>", self._handle_close_gpx_shortcut)
    self._root.bind("<Control-q>", self._handle_exit_shortcut)
    self._root.bind("<Control-Q>", self._handle_exit_shortcut)

  def _update_file_menu_state(self):
    if self._file_menu is None:
      return

    if self._map_widget is None:
      close_state = tkinter.DISABLED
    else:
      close_state = tkinter.NORMAL

    self._file_menu.entryconfig(_FILE_MENU_CLOSE_INDEX, state=close_state)

  def _handle_load_gpx_shortcut(self, event):
    self.prompt_and_load_gpx_file()

    return "break"

  def _handle_close_gpx_shortcut(self, event):
    self.close_loaded_gpx_file()

    return "break"

  def _handle_exit_shortcut(self, event):
    self.exit_application()

    return "break"

  def prompt_and_load_gpx_file(self):
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

    if self._track_display_options.mark_hours_interval is not None:
      if not gis_graphical_editor.track_analysis.has_timestamps(gpx_points):
        message = "GPX file has no timestamps, so --mark-hours markers cannot be drawn."
        tkinter.messagebox.showwarning("Load GPX", message, parent=self._root)

    self._display_gpx_points(gpx_points)

  def _ensure_map_widget(self):
    if self._map_widget is not None:
      return

    self._map_widget = tkintermapview.TkinterMapView(self._root, corner_radius=0)
    self._map_widget.pack(fill=tkinter.BOTH, expand=True)
    self._bind_map_widget_events()
    self._update_file_menu_state()

  def _bind_map_widget_events(self):
    self._map_widget.canvas.bind("<Double-Button-1>", self._handle_map_double_click)

  def _handle_map_double_click(self, event):
    relative_mouse_x = event.x / self._map_widget.width
    relative_mouse_y = event.y / self._map_widget.height
    new_zoom = self._map_widget.zoom + 1

    self._map_widget.set_zoom(
      new_zoom,
      relative_pointer_x=relative_mouse_x,
      relative_pointer_y=relative_mouse_y,
    )

  def _remove_map_widget(self):
    if self._map_widget is None:
      return

    self._map_widget.pack_forget()
    self._map_widget.destroy()
    self._map_widget = None
    self._green_point_icon = None
    self._orange_interval_icon = None
    self._red_interval_icon = None
    self._update_file_menu_state()

  def close_loaded_gpx_file(self):
    if self._map_widget is None:
      return

    self._remove_map_widget()

  def _display_gpx_points(self, gpx_points):
    self._ensure_map_widget()

    self._map_widget.delete_all_path()
    self._map_widget.delete_all_marker()

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
      )
      self._display_hour_interval_markers(hour_interval_markers)

    if self._track_display_options.mark_distance_interval is not None:
      distance_interval_markers = gis_graphical_editor.track_analysis.build_distance_interval_markers(
        gpx_points,
        self._track_display_options.mark_distance_interval,
      )
      self._display_distance_interval_markers(distance_interval_markers)

    latitudes = [point[0] for point in track_points]
    longitudes = [point[1] for point in track_points]
    position_top_left = (max(latitudes), min(longitudes))
    position_bottom_right = (min(latitudes), max(longitudes))

    self._map_widget.fit_bounding_box(position_top_left, position_bottom_right)

  def _display_recorded_points(self, gpx_points):
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
    self._root.quit()
