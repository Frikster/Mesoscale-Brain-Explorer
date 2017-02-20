#!/usr/bin/env python3

import os

import csv
import uuid
import numpy as np
import pyqtgraph as pg
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qtutil

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.plugin import WidgetDefault
from .util.plugin import PluginDefault
from pyqtgraph.dockarea import *

from .util.mse_ui_elements import RoiList
from itertools import cycle


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

def plot_roi_activities(video_path, rois, image, plot_title, win_title, progress_callback):
  frames = fileloader.load_file(video_path)
  #frames = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)
  # plot_out = os.path.join(os.path.dirname(video_path), plot_title + str(uuid.uuid4()))
  plot_out = os.path.join(os.path.dirname(video_path), plot_title + '.csv')

  roi_names = []
  ps = []
  for i, roi in enumerate(rois):
    progress_callback(i / len(rois))
    mask = roi.getROIMask(frames, image, axes=(1, 2))
    size = np.count_nonzero(mask)
    roi_frames = frames * mask[np.newaxis, :, :]
    roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
    p = roi_frames / size
    ps = ps + [p]
    roi_names = roi_names + [roi.name]

  ps = [list(p) for p in ps]
  ps_rows = list(zip(*ps))
  plot_out = os.path.join(os.path.dirname(video_path), plot_title + '.csv')
  with open(plot_out, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(roi_names)
    for i, row in enumerate(ps_rows):
        #progress_callback(i / len(rois))
        writer.writerow([str(p) for p in row])
  progress_callback(1)

  win = pg.GraphicsWindow(title=win_title)
  win.resize(1000, 600)
  # win.setWindowTitle('Activity across frames')
  plot = win.addPlot(title=plot_title)
  plot.setLabel('bottom', "Image Frames")
  plot.setLabel('left', "Activity")
  plot.addLegend()

  pg.setConfigOptions(antialias=True)

  warning_issued = False
  for i, roi in enumerate(rois):
    # progress_callback(i / len(rois))
    mask = roi.getROIMask(frames, image, axes=(1, 2))
    size = np.count_nonzero(mask)
    roi_frames = frames * mask[np.newaxis, :, :]
    roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
    p = roi_frames / size
    if i < len(brewer_colors):
        color = brewer_colors[i].rgb
    else:
        if not warning_issued:
            qtutil.warning('Perceptual distinctiveness limit (12) reached. Resorting to Kelly colours. '
                           'Please be careful with how you interpret your data')
            warning_issued = True
        if i < len(brewer_colors) + len(kelly_colors):
            color = kelly_colors[i-len(brewer_colors)].rgb
        else:
            qtutil.critical('Colour limit reached. Please plot your data over multiple plots or output solely to csv')
            return win
    plot.plot(p, pen=color, name=roi.name)
  return win

def plot_rois_same_axis(video_paths, rois, image, progress_callback=None):
      if not video_paths:
          qtutil.critical("No video selected.")
          return

      win = QMainWindow()
      area = DockArea()
      win.setCentralWidget(area)
      win.resize(1000, 600)
      win.setWindowTitle("Test")

      d1 = Dock("Save/Load", size=(1, 1))  ## give this dock the minimum possible size
      d2 = Dock("Dock2", size=(500, 200), closable=True)
      d3 = Dock("Dock3", size=(500, 200))
      d4 = Dock("Dock4", size=(500, 200))
      d5 = Dock("Dock5", size=(500, 200))
      area.addDock(d1, 'top')
      area.addDock(d2, 'bottom', d1)
      area.addDock(d3, 'bottom', d2)
      area.addDock(d4, 'right', d3)
      area.addDock(d5, 'top', d4)

      ## first dock gets save/restore buttons
      w1 = pg.LayoutWidget()
      label = QLabel("""
      This window has 4 Dock widgets in it. Each dock can be dragged
      by its title bar to occupy a different space within the window
      but note that one dock has its title bar hidden). Additionally,
      the borders between docks may be dragged to resize. Docks that are dragged on top
      of one another are stacked in a tabbed layout. Double-click a dock title
      bar to place it in its own window.
      """)
      saveBtn = QPushButton('Save dock state')
      restoreBtn = QPushButton('Restore dock state')
      restoreBtn.setEnabled(False)
      w1.addWidget(label, row=0, col=0)
      w1.addWidget(saveBtn, row=1, col=0)
      w1.addWidget(restoreBtn, row=2, col=0)
      d1.addWidget(w1)
      dock_state = None

      def save():
          global dock_state
          dock_state = area.saveState()
          restoreBtn.setEnabled(True)
      def load():
          global dock_state
          area.restoreState(dock_state)

      saveBtn.clicked.connect(save)
      restoreBtn.clicked.connect(load)

      # Collect ROI activities for each selected vid
      progress_load = QProgressDialog('Loading files and collecting ROI data', 'Abort', 0, 100)
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
          # roi_names = []
          # ps = []
          for j, roi in enumerate(rois):
              mask = roi.getROIMask(frames, image, axes=(1, 2))
              size = np.count_nonzero(mask)
              if size <= 0:
                  qtutil.critical("No ROI selected.")
                  return
              roi_frames = frames * mask[np.newaxis, :, :]
              roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
              p = roi_frames / size
              roi_activity_dict[roi.name] = p
              # ps = ps + [p]
              # roi_names = roi_names + [roi.name]
          video_path_to_plots_dict[video_path] = roi_activity_dict
      callback_load(1)

      # regroup ROIs of same type together and add to docs
      plot_docs = [d2, d3, d4, d5]
      plot_docs_cycle = cycle(plot_docs)
      for roi in rois:
        warning_issued = False
        plots_for_roi = []
        source_names = []
        for video_path in video_path_to_plots_dict.keys():
            root, ext = os.path.splitext(video_path)
            source_names = source_names + [root]
            plots_for_roi = plots_for_roi + [video_path_to_plots_dict[video_path][roi.name]]

        # put all plots from one ROI on a single plot and place on one of the 4 docs
        w = pg.PlotWidget(title="Dock plot")
        w.setLabel('bottom', "Image Frames")
        w.setLabel('left', "Activity")
        w.addLegend()
        for p, source_name in plots_for_roi, source_names:
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
                    return win
            w.plot(p, pen=color, name=source_name)
            next_doc = plot_docs_cycle.next()
            next_doc.addWidget(w)

        # Save plot to file
        ps = [list(p) for p in plots_for_roi]
        ps_rows = list(zip(*ps))
        plot_out = os.path.join(os.path.dirname(video_paths[0]), roi.name + '_plots.csv')
        with open(plot_out, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(source_names)
            for i, row in enumerate(ps_rows):
                # progress_callback(i / len(rois))
                writer.writerow([str(p) for p in row])
      return win

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
    # self.view = MyGraphicsView(self.project)
    # self.video_list = QListView()
    self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed)
    self.plot_pb = QPushButton('Plot &activity')
    WidgetDefault.__init__(self, project, plugin_position)

    # self.left = QFrame()
    # self.right = QFrame()

    # self.setup_ui()
    #
    # self.open_dialogs = []
    # self.selected_videos = []
    #
    # self.video_list.setModel(QStandardItemModel())
    # self.video_list.selectionModel().selectionChanged[QItemSelection,
    #   QItemSelection].connect(self.selected_video_changed)
    # self.video_list.doubleClicked.connect(self.video_triggered)
    #
    # self.roi_list.setModel(QStandardItemModel())
    # self.roi_list.selectionModel().selectionChanged[QItemSelection,
    #   QItemSelection].connect(self.selected_roi_changed)

    # for f in project.files:
    #   if f['type'] == 'video':
    #     self.video_list.model().appendRow(QStandardItem(f['name']))
    #   elif f['type'] == 'roi' or f['type'] == 'auto_roi':
    #     item = QStandardItem(f['name'])
    #     item.setData(f['path'], Qt.UserRole)
    #     self.roi_list.model().appendRow(item)
    #
    # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
    # self.roi_list.setCurrentIndex(self.roi_list.model().index(0, 0))

  # def video_triggered(self, index):
  #     pfs.video_triggered(self, index)

  def setup_ui(self):
    super().setup_ui()
    # vbox_view = QVBoxLayout()
    # vbox_view.addWidget(self.view)
    # self.view.vb.crosshair_visible = False
    # self.left.setLayout(vbox_view)
    #
    # vbox = QVBoxLayout()
    # list_of_manips = pfs.get_list_of_project_manips(self.project)
    # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    # vbox.addWidget(self.toolbutton)
    # vbox.addWidget(QLabel('Select video:'))
    # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # vbox.addWidget(self.video_list)
    # vbox.addWidget(QLabel('Select ROI:'))
    # self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.vbox.addWidget(self.roi_list)
    self.vbox.addWidget(self.plot_pb)
    # self.right.setLayout(vbox)

    # splitter = QSplitter(Qt.Horizontal)
    # splitter.setHandleWidth(3)
    # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    # splitter.addWidget(self.left)
    # splitter.addWidget(self.right)
    # hbox_global = QHBoxLayout()
    # hbox_global.addWidget(splitter)
    # self.setLayout(hbox_global)

    # hbox.addLayout(vbox)
    # hbox.setStretch(0, 1)
    # hbox.setStretch(1, 0)
    # self.setLayout(hbox)

  def setup_signals(self):
      super().setup_signals()
      self.plot_pb.clicked.connect(self.plot_triggered)

  def setup_params(self, reset=False):
      super().setup_params()
      self.roi_list.setup_params()

  def setup_param_signals(self):
      super().setup_param_signals()
      self.roi_list.setup_param_signals()

  # def refresh_video_list_via_combo_box(self, trigger_item=None):
  #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
  #
  # def selected_video_changed(self, selected, deselected):
  #     pfs.selected_video_changed_multi(self, selected, deselected)

  # def selected_video_changed(self, selection):
  #   if not selection.indexes():
  #     return
  #   self.video_path = str(os.path.join(self.project.path,
  #                                  selection.indexes()[0].data(Qt.DisplayRole))
  #                         + '.npy')
  #   frame = fileloader.load_reference_frame(self.video_path)
  #   self.view.show(frame)

  # def selected_roi_changed(self, selected, deselected):
  #   for index in deselected.indexes():
  #     roiname = str(index.data(Qt.DisplayRole))
  #     self.view.vb.removeRoi(roiname)
  #   for index in selected.indexes():
  #     roiname = str(index.data(Qt.DisplayRole))
  #     roipath = str(index.data(Qt.UserRole))
  #     self.view.vb.addRoi(roipath, roiname)

  def plot_triggered(self):
    global_progress = QProgressDialog('Generating Activity Plots of Selected ROIs', 'Abort', 0, 100, self)
    global_progress.setAutoClose(True)
    global_progress.setMinimumDuration(0)
    def global_callback(x):
        global_progress.setValue(x * 100)
        QApplication.processEvents()

    total = len(self.selected_videos)

    indexes = self.roi_list.selectionModel().selectedIndexes()
    roinames = [index.data(Qt.DisplayRole) for index in indexes]
    rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
    win = plot_rois_same_axis(self.selected_videos, rois, self.view.vb.img)
    self.open_dialogs.append(win)

    for selected_vid_no, video_path in enumerate(self.selected_videos):
      global_callback(selected_vid_no / total)
      progress = QProgressDialog('Generating Activity Plot for ' + video_path, 'Abort', 0, 100, self)
      progress.setAutoClose(True)
      progress.setMinimumDuration(0)
      def callback(x):
          progress.setValue(x * 100)
          QApplication.processEvents()
      callback(0.01)
      indexes = self.roi_list.selectionModel().selectedIndexes()
      roinames = [index.data(Qt.DisplayRole) for index in indexes]
      rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
      plot_title = 'Activity Across Frames for ' + os.path.basename(video_path)
      win_title = self.project.name
      win = plot_roi_activities(video_path, rois, self.view.vb.img, plot_title, win_title, callback)
      self.open_dialogs.append(win)
    global_callback(1)

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Plot ROI activity'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def run(self):
    pass
