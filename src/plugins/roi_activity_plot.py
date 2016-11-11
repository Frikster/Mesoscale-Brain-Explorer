#!/usr/bin/env python3

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader
import pyqtgraph as pg
from .util import project_functions as pfs

import numpy as np

class Color:
  def __init__(self, name, rgb):
    self.name = name
    self.rgb = rgb

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

def plot_roi_activities(video_path, rois, image, progress_callback):
  win = pg.GraphicsWindow(title="Activity across frames")
  win.resize(1000, 600)
  win.setWindowTitle('Activity across frames')
  plot = win.addPlot(title="Activity across frames")
  plot.addLegend()

  pg.setConfigOptions(antialias=True)

  frames = fileloader.load_file(video_path)
  #frames = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)

  for i, roi in enumerate(rois):
    progress_callback(i / len(rois))
    mask = roi.getROIMask(frames, image, axes=(1, 2))
    size = np.count_nonzero(mask)
    roi_frames = frames * mask[np.newaxis, :, :]
    roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
    p = roi_frames / size
    color = kelly_colors[i].rgb
    plot.plot(p, pen=color, name=roi.name)
  progress_callback(1)

  return win

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return
    self.project = project

    # Define UI components and global data
    self.view = MyGraphicsView(self.project)
    self.video_list = QListView()
    self.roi_list = QListView()
    self.left = QFrame()
    self.right = QFrame()

    self.setup_ui()

    self.open_dialogs = []

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_video_changed)
    self.video_list.doubleClicked.connect(self.video_triggered)

    self.roi_list.setModel(QStandardItemModel())
    self.roi_list.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_roi_changed)

    for f in project.files:
      if f['type'] == 'video':
        self.video_list.model().appendRow(QStandardItem(f['name']))
      elif f['type'] == 'roi':
        item = QStandardItem(f['name'])
        item.setData(f['path'], Qt.UserRole)
        self.roi_list.model().appendRow(item)

    self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
    self.roi_list.setCurrentIndex(self.roi_list.model().index(0, 0))

  def video_triggered(self, index):
      pfs.video_triggered(self, index)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.crosshair_visible = False
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    list_of_manips = pfs.get_list_of_project_manips(self.project)
    self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    vbox.addWidget(self.toolbutton)
    vbox.addWidget(QLabel('Select video:'))
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    vbox.addWidget(self.video_list)
    vbox.addWidget(QLabel('Select ROI:'))
    self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    vbox.addWidget(self.roi_list)
    pb = QPushButton('Plot &activity')
    pb.clicked.connect(self.plot_triggered)
    vbox.addWidget(pb)
    self.right.setLayout(vbox)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)

    # hbox.addLayout(vbox)
    # hbox.setStretch(0, 1)
    # hbox.setStretch(1, 0)
    # self.setLayout(hbox)

  def refresh_video_list_via_combo_box(self, trigger_item=None):
      pfs.refresh_video_list_via_combo_box(self, trigger_item)

  def selected_video_changed(self, selected, deselected):
      pfs.selected_video_changed_multi(self, selected, deselected)

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(os.path.join(self.project.path,
                                   selection.indexes()[0].data(Qt.DisplayRole))
                          + '.npy')
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)

  def selected_roi_changed(self, selected, deselected):
    for index in deselected.indexes():
      roiname = str(index.data(Qt.DisplayRole))
      self.view.vb.removeRoi(roiname)
    for index in selected.indexes():
      roiname = str(index.data(Qt.DisplayRole))
      roipath = str(index.data(Qt.UserRole))
      self.view.vb.addRoi(roipath, roiname)

  def plot_triggered(self):
    progress = QProgressDialog('Generating Activity Plots of Selected ROIs', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)
    def callback(x):
        progress.setValue(x * 100)
        QApplication.processEvents()
    callback(0.01)
    indexes = self.roi_list.selectionModel().selectedIndexes()
    roinames = [index.data(Qt.DisplayRole) for index in indexes]
    rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
    win = plot_roi_activities(self.video_path, rois, self.view.vb.img, callback)
    self.open_dialogs.append(win)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Plot ROI activity'
    self.widget = Widget(project)
  
  def run(self):
    pass
