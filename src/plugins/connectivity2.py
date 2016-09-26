#!/usr/bin/env python
from __future__ import print_function

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader

sys.path.append('..')
import qtutil

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def calc_avg(roi, frames, image):
  mask = roi.getROIMask(frames, image, axes=(1, 2))
  masksize = np.count_nonzero(mask)
  roiframes = frames * mask[np.newaxis, :, :]
  roiframes = np.ndarray.sum(np.ndarray.sum(roiframes, axis=1), axis=1)
  return roiframes / masksize

def calc_connectivity(video_path, image, rois):
  frames = fileloader.load_file(video_path)
  avgs = [calc_avg(roi, frames, image) for roi in rois]
  pearson = lambda x, y: stats.pearsonr(x, y)[0]
  return [[pearson(x, y) for x in avgs] for y in avgs]

# todo: explain why all the classes
class ConnectivityModel(QAbstractTableModel):
  def __init__(self, video_path, image, rois, parent=None):
    super(ConnectivityModel, self).__init__(parent)
    self.rois = rois
    self._data = calc_connectivity(video_path, image, rois)

  def rowCount(self, parent):
    return len(self._data)
  
  def columnCount(self, parent):
    return len(self._data)

  def data(self, index, role):
    if role == Qt.DisplayRole:
      return str(round(self._data[index.row()][index.column()], 2))
    elif role == Qt.BackgroundRole:
      value = float(self._data[index.row()][index.column()])
      color = plt.cm.jet(value)
      color = [x * 255 for x in color]
      return QColor(*color)
    elif role == Qt.TextAlignmentRole:
      return Qt.AlignCenter
    return

  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole:
      return self.rois[section].name
    return

class ConnectivityTable(QTableView):
  def __init__(self, parent=None):
    super(ConnectivityTable, self).__init__(parent)
    self.setSelectionMode(QAbstractItemView.NoSelection)
    self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    self.verticalHeader().setMaximumWidth(100)
    self.verticalHeader().setResizeMode(QHeaderView.Stretch)
    self.setMinimumSize(400, 300)

class ConnectivityDialog(QDialog):
  def __init__(self, video_path, image, rois, parent=None):
    super(ConnectivityDialog, self).__init__(parent)
    self.setWindowTitle('Connectivity Diagram')
    self.setup_ui()

    self.table.setModel(ConnectivityModel(video_path, image, rois))

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.table = ConnectivityTable() 
    vbox.addWidget(self.table)
    self.setLayout(vbox)

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
        self.video_list.model().appendRow(QStandardItem(f['path']))
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

    pb = QPushButton('Connectivity &Diagram')
    pb.clicked.connect(self.connectivity_triggered)
    vbox.addWidget(pb)

    hbox.addLayout(vbox)
    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)
    self.setLayout(hbox) 

  def selected_video_changed(self, selected, deselected):
    if not selected.indexes():
      return
    self.video_path = str(selected.indexes()[0].data(Qt.DisplayRole))
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

  def connectivity_triggered(self):
    indexes = self.roi_list.selectionModel().selectedIndexes()
    roinames = [index.data(Qt.DisplayRole) for index in indexes]
    rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
    if not self.view.vb.img:
      qtutil.critical('Select video.')
    elif not rois:
      qtutil.critical('Select Roi(s).')
    else:
      win = ConnectivityDialog(self.video_path, self.view.vb.img,
                               rois, self)
      win.show()
      self.open_dialogs.append(win)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Connectivity2'
    self.widget = Widget(project)
  
  def run(self):
    pass
