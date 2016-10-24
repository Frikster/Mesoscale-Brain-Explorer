#!/usr/bin/env python3
from __future__ import print_function

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader
from .util import mse_ui_elements as mue

sys.path.append('..')
import qtutil

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import pyqtgraph as pg

import itertools

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
    def __init__(self, selected_videos, image, rois, parent=None):
        super(ConnectivityModel, self).__init__(parent)
        self.rois = rois

        avg_data = []
        tot_data = []
        dict_for_stdev = {}

        for key in [i for i in list(itertools.product(xrange(len(rois)), xrange(len(rois))))]:
            dict_for_stdev[key] = []

        for video_path in selected_videos:
            self._data = calc_connectivity(video_path, image, rois)
            if tot_data == []:
                tot_data = self._data
            if avg_data == []:
                avg_data = self._data
            for i in xrange(len(tot_data)):
                for j in xrange(len(tot_data)):
                    dict_for_stdev[(i, j)] = dict_for_stdev[(i, j)] + [self._data[i][j]]
                    if video_path != selected_videos[0]:
                        tot_data[i][j] = tot_data[i][j] + self._data[i][j]
        # Finally compute averages
        for i in xrange(len(tot_data)):
            for j in xrange(len(tot_data)):
                avg_data[i][j] = tot_data[i][j] / len(selected_videos)
        stdev_dict = {k: np.std(v) for k, v in dict_for_stdev.items()}
        assert(stdev_dict[(0, 0)] == 0)

        # combine stddev and avg data
        for i in xrange(len(avg_data)):
            for j in xrange(len(avg_data)):
                avg_data[i][j] = (avg_data[i][j], stdev_dict[(i, j)])

        self._data = avg_data
        assert(avg_data != [])

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data)

    def data(self, index, role):
        tup = self._data[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return str(round(tup[0], 2))+" +/- "+str(round(tup[1], 2))
        elif role == Qt.BackgroundRole:
            value = float(tup[0])
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
    def __init__(self, selected_videos, image, rois, parent=None):
        super(ConnectivityDialog, self).__init__(parent)
        self.setWindowTitle('Connectivity Diagram')
        self.setup_ui()

        self.table.setModel(ConnectivityModel(selected_videos, image, rois))

    def setup_ui(self):
        vbox = QVBoxLayout()
        self.table = ConnectivityTable()
        vbox.addWidget(self.table)
        self.setLayout(vbox)

class RoiModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(RoiModel, self).__init__(parent)

  def supportedDropActions(self):
    return Qt.MoveAction

  def dropMimeData(self, data, action, row, column, parent):
    return super(RoiModel, self).dropMimeData(data, action, row, column, parent)

  def flags(self, index):
    if not index.isValid() or index.row() >= self.rowCount() or index.model() != self:
       return Qt.ItemIsDropEnabled # we allow drops outside the items
    return super(RoiModel, self).flags(index) & (~Qt.ItemIsDropEnabled)

  def removeRows(self, row, count, parent):
    #print('remove', row, count)
    return super(RoiModel, self).removeRows(row, count, parent)

  def insertRows(self, row, count, parent):
    #print('insert', row, count)
    return super(RoiModel, self).insertRows(row, count, parent)

  def get_plugin_names(self):
    ret = []
    for i in range(self.rowCount()):
      index = self.index(i, 0)
      value = str(self.data(index, Qt.UserRole))
      ret.append(value)
    return ret

  def set_plugins(self, plugins):
    for name, title in plugins:
      item = QStandardItem(title)
      item.setData(name, Qt.UserRole)
      self.appendRow(item)

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)

        if not project:
            return
        self.project = project

        # define ui components and global data
        self.left = QFrame()
        self.right = QFrame()
        self.view = MyGraphicsView(self.project)
        self.video_list = QListView()
        self.roi_list = QListView()

        self.setup_ui()

        self.open_dialogs = []
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged[QItemSelection,
          QItemSelection].connect(self.selected_video_changed)

        self.roi_list.setModel(RoiModel())
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

    def setup_ui(self):
        vbox_view = QVBoxLayout()
        vbox_view.addWidget(self.view)
        self.view.vb.crosshair_visible = False
        self.left.setLayout(vbox_view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Select video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)
        vbox.addWidget(qtutil.separator())
        vbox.addWidget(mue.InfoWidget('Click shift to select multiple ROIs. Drag to reorder.'))
        vbox.addWidget(QLabel('Select ROIs:'))
        self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.roi_list.setAcceptDrops(True)
        self.roi_list.setDragEnabled(True)
        self.roi_list.setDropIndicatorShown(True)
        self.roi_list.setDragDropMode(QAbstractItemView.DragDrop)
        self.roi_list.setDragDropOverwriteMode(False)
        vbox.addWidget(self.roi_list)
        pb = QPushButton('Connectivity &Diagram')
        pb.clicked.connect(self.connectivity_triggered)
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

    def selected_video_changed(self, selected, deselected):
        if not selected.indexes():
            return

        for index in deselected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
            self.selected_videos = [x for x in self.selected_videos if x != vidpath]
        for index in selected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
        if vidpath not in self.selected_videos and vidpath != 'None':
            self.selected_videos = self.selected_videos + [vidpath]

        self.shown_video_path = str(os.path.join(self.project.path,
                                           selected.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.shown_video_path)
        self.view.show(frame)

    def selected_roi_changed(self, selected, deselected):
        #todo: how in the world did you know to do this? deselected.indexes only returns one object no matter what - roiname also only ever has one value so this function must be being called multiple times for each selection/deselection
        #todo: what's the point of the forloops?
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
            #todo:

            #pg.ImageItem(arr, autoRange=False, autoLevels=False)
            win = ConnectivityDialog(self.selected_videos, self.view.vb.img,
                                   rois, self)
            win.show()
            self.open_dialogs.append(win)

class MyPlugin:
    def __init__(self, project):
        self.name = 'Connectivity2'
        self.widget = Widget(project)

    def run(self):
        pass
