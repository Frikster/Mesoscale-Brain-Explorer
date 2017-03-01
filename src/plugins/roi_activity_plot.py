#!/usr/bin/env python3

import csv
import os
import uuid
from itertools import cycle

import numpy as np
import pyqtgraph as pg
import qtutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pyqtgraph.dockarea import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mse_ui_elements import RoiList
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

UUID_SIZE = len(str(uuid.uuid4()))

class Color:
  def __init__(self, name, rgb):
    self.name = name
    self.rgb = rgb

brewer_colors = [
 Color('light_blue',(166,206,227)),
 Color('dark_blue',(31,120,180)),
 Color('light_green',(178,223,138)),
 Color('dark_green',(51,160,44)),
 Color('light_red',(251,154,153)),
 Color('dark_red',(227,26,28)),
 Color('light_orange',(253,191,111)),
 Color('dark_orange',(255,127,0)),
 Color('light_purple',(202,178,214)),
 Color('dark_purple',(106,61,154)),
 Color('yellow',(255,255,153)),
 Color('brown',(177,89,40))
]

kelly_colors = [
  Color('vivid_yellow', (255, 179, 0)),
  Color('strong_purple', (128, 62, 117)),
  Color('vivid_red', (193, 0, 32)),
  Color('vivid_green', (0, 125, 52)),
  Color('strong_purplish_pink', (246, 118, 142)),
  Color('strong_blue', (0, 83, 138)),
  Color('strong_yellowish_pink', (255, 122, 92)),
  Color('strong_violet', (83, 55, 122)),
  Color('vivid_orange_yellow', (255, 142, 0)),
  Color('strong_purplish_red', (179, 40, 81)),
  Color('vivid_greenish_yellow', (244, 200, 0)),
  Color('strong_reddish_brown', (127, 24, 13)),
  Color('vivid_yellowish_green', (147, 170, 0)),
  Color('deep_yellowish_brown', (89, 51, 21)),
  Color('vivid_reddish_orange', (241, 58, 19)),
  Color('dark_olive_green', (35, 44, 22))
]


class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    pass

  class Defaults(WidgetDefault.Defaults):
    roi_list_types_displayed = ['auto_roi', 'roi']
    manip = "plot"

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)

    if not project or not isinstance(plugin_position, int):
        return
    self.project = project

    # Define UI components and global data
    self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed)
    self.save_pb = QPushButton("&Save plot windows")
    self.load_pb = QPushButton("&Load project plot windows")
    self.plot_pb = QPushButton('Plot &activity')
    self.open_dialogs_data_dict = []
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    self.vbox.addWidget(self.roi_list)
    self.vbox.addWidget(self.save_pb)
    self.vbox.addWidget(self.load_pb)
    self.vbox.addWidget(self.plot_pb)

  def setup_signals(self):
      super().setup_signals()
      self.plot_pb.clicked.connect(self.plot_triggered)
      self.save_pb.clicked.connect(self.save_dock_windows)
      self.load_pb.clicked.connect(self.load_dock_windows)

  def setup_params(self, reset=False):
      super().setup_params(reset)
      self.roi_list.setup_params()

  def setup_param_signals(self):
      super().setup_param_signals()
      self.roi_list.setup_param_signals()

  def get_video_path_to_plots_dict(self):
      '''Collect ROI activities for each selected vid'''
      indexes = self.roi_list.selectionModel().selectedIndexes()
      roinames = [index.data(Qt.DisplayRole) for index in indexes]
      rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
      video_paths = self.selected_videos
      image = self.view.vb.img
      if not rois:
          qtutil.critical("No ROI selected.")
          return
      if not video_paths:
          qtutil.critical("No image stack selected")
          return

      progress_load = QProgressDialog('Loading files and collecting ROI data. This may take a while '
                                      'for large files.', 'Abort', 0, 100)
      progress_load.setAutoClose(True)
      progress_load.setMinimumDuration(0)
      def callback_load(x):
          progress_load.setValue(x * 100)
          QApplication.processEvents()

      video_path_to_plots_dict = {}
      for i, video_path in enumerate(video_paths):
          callback_load(i / len(video_paths))
          if progress_load.wasCanceled():
              return
          frames = fileloader.load_file(video_path)
          roi_activity_dict = {}
          for j, roi in enumerate(rois):
              mask = roi.getROIMask(frames, image, axes=(1, 2))
              size = np.count_nonzero(mask)
              if size <= 0:
                  qtutil.critical("No ROI selected. If you do have ROIs selected then the most likely cause is that "
                                  "you have modified the unit per pixel and not updated the size of the ROIs which "
                                  "don't adjust automatically. So for example any ROI with length 1 might now be less "
                                  "than 1 pixel after you changed the unit per pixel. To update the ROIs against your "
                                  "new unit per pixel, go to the import ROI plugin and press the 'Update Table' button")
                  return
              roi_frames = frames * mask[np.newaxis, :, :]
              roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
              p = roi_frames / size
              roi_activity_dict[roi.name] = p
          video_path_to_plots_dict[video_path] = roi_activity_dict
      callback_load(1)
      return video_path_to_plots_dict


  def plot_to_docks(self, video_path_to_plots_dict, area):
      if not video_path_to_plots_dict:
          return
      roi_names = list(list(video_path_to_plots_dict.values())[0].keys())
      video_paths = list(video_path_to_plots_dict.keys())

      # regroup ROIs of same type together and add to Docks dynamically
      plot_docks = [0, 1, 2, 3]
      plot_docs_cycle = cycle(plot_docks)
      for roi_name in roi_names:
          warning_issued = False
          plots_for_roi = []
          source_names = []
          for video_path in video_path_to_plots_dict.keys():
              root, ext = os.path.splitext(video_path)
              source_name = os.path.basename(root)
              source_names = source_names + [source_name]
              plots_for_roi = plots_for_roi + [video_path_to_plots_dict[video_path][roi_name]]

          # put all plots from one ROI on a single plot and place on one of the 4 docs
          next_dock = next(plot_docs_cycle)
          d = Dock(roi_name, size=(500, 200), closable=True)
          if next_dock == 0:
              area.addDock(d, 'above', area.docks['d1'])
          if next_dock == 1:
              area.addDock(d, 'above', area.docks['d2'])
          if next_dock == 2:
              area.addDock(d, 'above', area.docks['d3'])
          if next_dock == 3:
              area.addDock(d, 'above', area.docks['d4'])

          doc_window = pg.GraphicsWindow(title="Dock plot")
          plot = doc_window.addPlot(title=roi_name)
          plot.setLabel('bottom', "Image Frames")
          plot.setLabel('left', "Activity")
          plot.addLegend()
          assert (len(plots_for_roi) == len(source_names))
          for i, (p, source_name) in enumerate(zip(plots_for_roi, source_names)):
              if i < len(brewer_colors):
                  color = brewer_colors[i].rgb
              else:
                  if not warning_issued:
                      qtutil.warning('Perceptual distinctiveness limit (12) reached. Resorting to Kelly colours. '
                                     'Please be careful with how you interpret your data')
                      warning_issued = True
                  if i < len(brewer_colors) + len(kelly_colors):
                      color = kelly_colors[i - len(brewer_colors)].rgb
                  else:
                      qtutil.critical(
                          'Colour limit reached. Please plot your data over multiple plots or output solely to csv')
                      return doc_window
              plot.plot(p, pen=color, name=source_name)
          d.addWidget(doc_window)

          # Save plot to file (backup)
          ps = [list(p) for p in plots_for_roi]
          ps_rows = list(zip(*ps))
          plot_out = os.path.join(os.path.dirname(video_paths[0]), roi_name + '_plots_backup.csv')
          with open(plot_out, 'w', newline='') as csvfile:
              writer = csv.writer(csvfile, delimiter=',',
                                  quotechar='|', quoting=csv.QUOTE_MINIMAL)
              writer.writerow(source_names)
              for i, row in enumerate(ps_rows):
                  writer.writerow([str(p) for p in row])

      # close placeholder docks
      area.docks['d1'].close()
      area.docks['d2'].close()
      area.docks['d3'].close()
      area.docks['d4'].close()



  def setup_docks(self):
      area = DockArea()
      d1 = Dock("d1", size=(500, 200), closable=True)
      d2 = Dock("d2", size=(500, 200), closable=True)
      d3 = Dock("d3", size=(500, 200), closable=True)
      d4 = Dock("d4", size=(500, 200), closable=True)
      area.addDock(d1)
      area.addDock(d2, 'bottom', d1)
      area.addDock(d3, 'right', d2)
      area.addDock(d4, 'top', d3)
      area.moveDock(d4, 'right', d1)
      return area

  def plot_triggered(self):
    main_window = QMainWindow()
    area = self.setup_docks()
    main_window.setCentralWidget(area)
    main_window.resize(2000, 900)
    main_window.setWindowTitle("Window ID - " + str(uuid.uuid4()) +
                               ". Click Shift+F1 for help")
    main_window.setWhatsThis("Use View All to reset a view\n"
                             "\n"
                             "The blue tabs have the name of the ROI for a particular plot. These tabs can be dragged "
                             "around to highlighted regions to the side of other tabs to split the dock or on top of "
                             "other plots to place the tab in that dock. \n"
                             "\n"
                             "right click any plot to see more options. One important one is mouse mode. In Mouse "
                             "mode 3 you can hold the left mouse button to pan and "
                             "In mouse mode 1 you can zoom in on a particular region by creating cropping it with the "
                             "left mouse button. In either mode the right mouse button can be used to adjust the shape "
                             "of the plot and the mouse wheel for zoom \n"
                             "\n"
                             "Use Export to save a particular plot's data to csv or save as an image after you are "
                             "satisfied with how graphical elements (see 'plot options') are arranged. "
                             "Note that backups csv's of all plots are made automatically and can be found in your "
                             "project directory")
    video_path_to_plots_dict = self.get_video_path_to_plots_dict()
    self.plot_to_docks(video_path_to_plots_dict, area)
    main_window.show()
    self.open_dialogs.append(main_window)
    self.open_dialogs_data_dict.append((main_window, video_path_to_plots_dict))

  def filedialog(self, name, filters):
    path = self.project.path
    dialog = QFileDialog(self)
    dialog.setWindowTitle('Export to')
    dialog.setDirectory(str(path))
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setOption(QFileDialog.DontUseNativeDialog)
    dialog.selectFile(name)
    dialog.setFilter(';;'.join(filters.values()))
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    if not dialog.exec_():
      return None
    filename = str(dialog.selectedFiles()[0])
    QSettings().setValue('export_path', os.path.dirname(filename))
    filter_ = str(dialog.selectedNameFilter())
    ext = [f for f in filters if filters[f] == filter_][0]
    if not filename.endswith(ext):
      filename = filename + ext
    return filename

  def save_dock_windows(self):
      pfs.save_dock_windows(self, 'plot_window')

  def load_dock_windows(self):
      pfs.load_dock_windows(self, 'plot_window')

  def setup_whats_this(self):
      super().setup_whats_this()
      self.roi_list.setWhatsThis("Choose ROIs where the average activity per frame is plotted for each. "
                                 "Ensure your pixel width is correct and that its units agree with the units of the "
                                 "coordinates of these ROIs.")
      self.save_pb.setWhatsThis("Saves the data from all open plot windows to file and the project. Each window can "
                                "receive a custom name allowing for sets of analysis to occur on different windows "
                                "with different data plotted.")
      self.load_pb.setWhatsThis("Loads all plot windows associated with this plugin that have been saved. Click "
                                "'Manage Data' to find each window associated with this project. Individual windows "
                                "can be deleted from there. ")
      self.plot_pb.setWhatsThis("Create plots of activity across frames for each image stack selected and each ROI "
                                "selected")

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Plot ROI activity'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def run(self):
    pass
