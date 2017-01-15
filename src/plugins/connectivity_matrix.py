#!/usr/bin/env python3
from __future__ import print_function

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import mse_ui_elements as mue
from .util.mygraphicsview import MyGraphicsView

sys.path.append('..')
import qtutil

import numpy as np
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt
import uuid
import csv
from .util import project_functions as pfs
from pyqtgraph.Qt import QtGui

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
    def __init__(self, selected_videos, image, rois, cm_type, parent=None, progress_callback=None):
        super(ConnectivityModel, self).__init__(parent)
        self.cm_type = cm_type
        self.rois = rois
        self.matrix_list = []
        avg_data = []
        tot_data = []
        dict_for_stdev = {}

        for key in [i for i in list(itertools.product(range(len(rois)), range(len(rois))))]:
            dict_for_stdev[key] = []

        for i, video_path in enumerate(selected_videos):
            if progress_callback:
                progress_callback(i / len(selected_videos))
            self._data = calc_connectivity(video_path, image, rois)
            self.matrix_list = self.matrix_list + [self._data]
            if tot_data == []:
                tot_data = self._data
            if avg_data == []:
                avg_data = self._data
            for i in range(len(tot_data)):
                for j in range(len(tot_data)):
                    dict_for_stdev[(i, j)] = dict_for_stdev[(i, j)] + [self._data[i][j]]
                    # ignore half of graph
                    if i < j:
                        dict_for_stdev[(i, j)] = [0]
                    # Start above with self._data receiving= the first value before adding on the rest.
                    # don't add the first value twice
                    if os.path.normpath(video_path) != os.path.normpath(selected_videos[0]):
                        tot_data[i][j] = tot_data[i][j] + self._data[i][j]
        # Finally compute averages
        for i in range(len(tot_data)):
            for j in range(len(tot_data)):
                if progress_callback:
                    progress_callback((i*j) / (len(tot_data)*len(tot_data)))
                # ignore half of graph
                if i < j:
                    avg_data[i][j] = 0
                else:
                    avg_data[i][j] = tot_data[i][j] / len(selected_videos)
        stdev_dict = {k: np.std(v) for k, v in dict_for_stdev.items()}
        assert(stdev_dict[(0, 0)] == 0)

        # combine stddev and avg data
        for i in range(len(avg_data)):
            for j in range(len(avg_data)):
                if progress_callback:
                    progress_callback((i*j) / (len(avg_data) * len(avg_data)))
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

            gradient_range = matplotlib.colors.Normalize(-1.0, 1.0)
            cmap = matplotlib.cm.ScalarMappable(
                gradient_range, self.cm_type)
            color = cmap.to_rgba(value, bytes=True)
            # color = plt.cm.jet(value)
            # color = [x * 255 for x in color]
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
    def __init__(self, selected_videos, image, rois, cm_type, parent=None, progress_callback=None):
        super(ConnectivityDialog, self).__init__(parent)
        self.setWindowTitle('Connectivity Diagram')
        self.setup_ui()
        self.model = ConnectivityModel(selected_videos, image, rois, cm_type, None, progress_callback)
        self.table.setModel(self.model)

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
    return super(RoiModel, self).removeRows(row, count, parent)

  def insertRows(self, row, count, parent):
    return super(RoiModel, self).insertRows(row, count, parent)

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
        self.cm_comboBox = QtGui.QComboBox(self)

        self.setup_ui()

        self.open_dialogs = []
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged[QItemSelection,
          QItemSelection].connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)

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
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
        vbox.addWidget(QLabel('Choose colormap:'))
        # todo: colormap list should be dealt with in a seperate script
        self.cm_comboBox.addItem("jet")
        self.cm_comboBox.addItem("coolwarm")
        self.cm_comboBox.addItem("PRGn")
        self.cm_comboBox.addItem("seismic")
        self.cm_comboBox.addItem("viridis")
        self.cm_comboBox.addItem("inferno")
        self.cm_comboBox.addItem("plasma")
        self.cm_comboBox.addItem("magma")
        vbox.addWidget(self.cm_comboBox)
        self.cm_comboBox.activated[str].connect(self.cm_choice)
        pb = QPushButton('Connectivity &Diagram')
        pb.clicked.connect(self.connectivity_triggered)
        vbox.addWidget(pb)
        pb = QPushButton('Save all open matrices to csv')
        pb.clicked.connect(self.save_open_dialogs_to_csv)
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

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def cm_choice(self, cm_choice):
        self.cm_type = cm_choice

    # def selected_video_changed(self, selected, deselected):
    #     if not selected.indexes():
    #         return
    #
    #     for index in deselected.indexes():
    #         vidpath = str(os.path.join(self.project.path,
    #                                  index.data(Qt.DisplayRole))
    #                           + '.npy')
    #         self.selected_videos = [x for x in self.selected_videos if x != vidpath]
    #     for index in selected.indexes():
    #         vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
    #         if vidpath not in self.selected_videos and vidpath != 'None':
    #             self.selected_videos = self.selected_videos + [vidpath]
    #
    #     self.shown_video_path = str(os.path.join(self.project.path,
    #                                        selected.indexes()[0].data(Qt.DisplayRole))
    #                           + '.npy')
    #     frame = fileloader.load_reference_frame(self.shown_video_path)
    #     self.view.show(frame)

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
        progress = QProgressDialog('Generating Connectivity Diagram...', 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()

        indexes = self.roi_list.selectionModel().selectedIndexes()
        roinames = [index.data(Qt.DisplayRole) for index in indexes]
        rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
        if not self.view.vb.img:
            qtutil.critical('Select video.')
        elif not rois:
            qtutil.critical('Select Roi(s).')
        else:

            win = ConnectivityDialog(self.selected_videos, self.view.vb.img,
                                   rois, self.cm_type, self, callback)
            callback(1)
            win.show()
            self.open_dialogs.append(win)

    def save_open_dialogs_to_csv(self):
        progress = QProgressDialog('Generating csv files...',
                                   'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)

        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()

        for i, dialog in enumerate(self.open_dialogs):
            callback(i / len(self.open_dialogs))
            rois_names = [dialog.model.rois[x].name for x in range(len(dialog.model.rois))]
            unique_id = str(uuid.uuid4())
            file_name_avg = self.project.name + '_averaged_connectivity_matrix_' + unique_id + '.csv'
            file_name_stdev = self.project.name + '_stdev_connectivity_matrix_' + unique_id + '.csv'

            with open(os.path.join(self.project.path, file_name_avg), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(rois_names)
                for row_ind in range(len(dialog.model._data)):
                    row = dialog.model._data[row_ind]
                    row = [row[x][0] for x in range(len(row))]
                    writer.writerow(row)
                writer.writerow(['Selected videos:']+self.selected_videos)
            # Do the standard deviation
            with open(os.path.join(self.project.path, file_name_stdev), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(rois_names)
                for row_ind in range(len(dialog.model._data)):
                    row = dialog.model._data[row_ind]
                    row = [row[x][1] for x in range(len(row))]
                    writer.writerow(row)
                writer.writerow(['Selected videos:'] + self.selected_videos)
        callback(1)
        qtutil.info("All matrices saved to project directory")
                # for row_ind in range(len(dialog.model._data)):
                #     row = dialog.model._data[row_ind]
                #     row = [row[x][0] for x in range(len(row))]
                #     writer.writerow(row)
                #     print(str(row))

            #     for x in range(len(rois_names)):
            #             row = dialog.model._data[row][x][0]
            #
            # avg_matrix = [[rois_names[x]] + dialog.model._data[x] for x in range(len(dialog.model._data))]
            # # empty space in top left
            # rois_names = [''] + rois_names
            # avg_matrix = [rois_names] + avg_matrix
            # #todo: get rid of TEST
            #
            # with open(os.path.join(self.project.path, 'TEST.csv'), 'w', newline='') as csvfile:
            #     writer = csv.writer(csvfile, delimiter=',')
            #     for row in avg_matrix:
            #         writer.writerow(row)
            #         print(str(row))


            # matrix_list = dialog.model.matrix_list
            # unique_id_avg = str(uuid.uuid4())
            # path = os.path.join(self.project.path, unique_id_avg)






class MyPlugin:
    def __init__(self, project):
        self.name = 'Connectivity Matrix'
        self.widget = Widget(project)

    def run(self):
        pass
