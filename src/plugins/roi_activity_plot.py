#!/usr/bin/env python3

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader
import pyqtgraph as pg

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

def plot_roi_activities(video_path, rois, image):
  win = pg.GraphicsWindow(title="Activity across frames")
  win.resize(1000, 600)
  win.setWindowTitle('Activity across frames')
  plot = win.addPlot(title="Activity across frames")
  plot.addLegend()

  pg.setConfigOptions(antialias=True)

  frames = fileloader.load_file(video_path)
  #frames = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)

  for i, roi in enumerate(rois):
    mask = roi.getROIMask(frames, image, axes=(1, 2))
    size = np.count_nonzero(mask)
    roi_frames = frames * mask[np.newaxis, :, :]
    roi_frames = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
    p = roi_frames / size
    color = kelly_colors[i].rgb
    plot.plot(p, pen=color, name=roi.name)

  return win

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return
    self.project = project
    self.setup_ui()

    self.open_dialogs = []

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_video_changed)

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

  def setup_ui(self):
    hbox = QHBoxLayout()
  
    self.view = MyGraphicsView(self.project)
    self.view.vb.crosshair_visible = False
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Select video:'))
    self.video_list = QListView()
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.video_list)

    vbox.addWidget(QLabel('Select ROI:'))
    self.roi_list = QListView()
    self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    vbox.addWidget(self.roi_list)

    pb = QPushButton('Plot &activity')
    pb.clicked.connect(self.plot_triggered)
    vbox.addWidget(pb)

    hbox.addLayout(vbox)
    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)
    self.setLayout(hbox) 

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
    indexes = self.roi_list.selectionModel().selectedIndexes()
    roinames = [index.data(Qt.DisplayRole) for index in indexes]
    rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
    win = plot_roi_activities(self.video_path, rois, self.view.vb.img)
    self.open_dialogs.append(win)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Plot ROI activity'
    self.widget = Widget(project)
  
  def run(self):
    pass
