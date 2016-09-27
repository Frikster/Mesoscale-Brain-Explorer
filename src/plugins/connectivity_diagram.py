#!/usr/bin/env python3

import os, sys
import numpy as np
import random

from scipy import stats
import matplotlib.pylab as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader

import uuid
import psutil
import qtutil

class Widget(QWidget):
    def __init__(self, project=None, parent=None):
        super(Widget, self).__init__(parent)

        if not project:
            return
        self.project = project
        self.setup_ui()
        self.open_dialogs = []

        self.listview.setModel(QStandardItemModel())
        self.listview.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_video_changed)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.listview.model().appendRow(QStandardItem(f['name']))
        self.listview.setCurrentIndex(self.listview.model().index(0, 0))

        self.roi_list.setModel(QStandardItemModel())
        self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # A flag to see whether selected_roi_changed is being entered for the first time
        self.selected_roi_changed_flag = 0
        self.roi_list.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_roi_changed)
        #roi_names = [f['name'] for f in project.files if f['type'] == 'roi']
        for f in project.files:
            if f['type'] == 'roi':
                item = QStandardItem(f['name'])
                item.setData(f['path'], Qt.UserRole)
                self.roi_list.model().appendRow(item)

        #self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        self.roi_list.setCurrentIndex(self.roi_list.model().index(0, 0))

    def setup_ui(self):
        hbox = QHBoxLayout()

        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.listview = QListView()
        self.listview.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.listview)

        pb = QPushButton('Connectivity Diagram')
        pb.clicked.connect(self.connectivity_diagram)
        vbox.addWidget(pb)

        vbox.addWidget(qtutil.separator())

        vbox2 = QVBoxLayout()
        w = QWidget()
        w.setLayout(vbox2)
        vbox.addWidget(w)

        vbox.addWidget(qtutil.separator())
        vbox.addWidget(QLabel('ROIs'))
        self.roi_list = QListView()
        vbox.addWidget(self.roi_list)

        hbox.addLayout(vbox)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

    def remove_all_rois(self):
        rois = self.view.vb.rois[:]
        for roi in rois:
            if not roi.isSelected:
                self.view.vb.selectROI(roi)
            self.view.vb.removeROI()

    def selected_video_changed(self, selection):
        if not selection.indexes():
            return
        self.video_path = str(os.path.join(self.project.path,
                                           selection.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)

    def selected_roi_changed(self, selection):
        # if self.selected_roi_changed_flag == 0:
        #   self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
        #   return
        if not selection.indexes() or self.view.vb.drawROImode:
            return
        self.remove_all_rois()

        # todo: re-explain how you can figure out to go from commented line to uncommented line
        # rois_selected = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
        rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole).toString())
                         for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
        rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
        rois_to_add = [x for x in rois_selected if x not in rois_in_view]
        for roi_to_add in rois_to_add:
            self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])

    def connectivity_diagram(self):
        frames = fileloader.load_file(self.video_path)
        # Return if there is no image or rois in view
        if self.view.vb.img == None or len(self.view.vb.rois) == 0:
            print("there is no image or rois in view ")
            return

        # swap axis for aligned_frames
        frames_swap = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)
        # Collect ROI's and average each one
        avg_of_rois = {}

        roi_names = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
        for i, roi_name in enumerate(roi_names):
            roi = self.view.vb.rois[i]
            arrRegion_mask = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
            #arrRegion_mask[(arrRegion_mask == 0)] = None
            mask_size = np.count_nonzero(arrRegion_mask)
            roi_frames = (frames * arrRegion_mask[np.newaxis, :, :])
            roi_frames_flatten = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
            avg_of_rois[roi_name] = roi_frames_flatten/mask_size

        connectivity_matrix = {}
        rois = self.view.vb.rois
        for i, roi2 in enumerate(rois):
            col = []
            for j, roi1 in enumerate(rois):
                row_name = roi1.name
                col_name = roi2.name
                col.append(stats.pearsonr(
                    avg_of_rois[row_name], avg_of_rois[col_name])[0])
            connectivity_matrix[col_name] = col

        #w = QMainWindow()
        #w.setCentralWidget(TableWidget(connectivity_matrix, self))
        numROIs = len(self.view.vb.rois)
        table = MyTable(connectivity_matrix, numROIs, numROIs)
        #dialog = TableView(self.project, connectivity_matrix, self)
        table.show()
        self.open_dialogs.append(table)

class MyTable(QTableWidget):
    def __init__(self, data, *args):
        QTableWidget.__init__(self, *args)
        self.data = data
        self.setmydata()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setResizeMode(QHeaderView.Stretch)

    def setmydata(self):
        horHeaders = []
        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)
            for m, item in enumerate(self.data[key]):
                r, g, b = [random.randint(0, 255) for _ in range(3)]
                newitem = QTableWidgetItem(str(item))
                newitem.setBackgroundColor(QColor(r, g, b))
                self.setItem(m, n, newitem)
        self.setHorizontalHeaderLabels(horHeaders)
        self.setVerticalHeaderLabels(horHeaders)



# class TableModel(QStandardItemModel):
#   def __init__(self, parent=None):
#     super(TableModel, self).__init__(parent)
#
#     self.setRowCount(20)
#     self.setColumnCount(16)
#     #plt.cm.jet(spc_map)
#
#   def data(self, index, role):
#     if role == Qt.BackgroundRole:
#       r, g, b = [random.randint(0, 255) for _ in range(3)]
#       return QColor(r, g, b)
#     # elif role == Qt.DisplayRole:
#     #   value = round(random.random(), 2)
#     #   return str(value)
#     elif role == Qt.TextAlignmentRole:
#       return Qt.AlignCenter
#     super(TableModel, self).data(index, role)

# #todo: how to tell who to superclass on?
# class TableWidget(QTableWidget):
#     #todo: why not specify parent in constructor parameter?
#     def __init__(self, data, parent=None, *args):
#      #todo: How do I tell which of these two lines to use?
#      #super(TableWidget, self).__init__(parent)
#      QTableWidget.__init__(self, *args)
#
#      self.data = data
#      self.setmydata()
#      self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
#      self.verticalHeader().setResizeMode(QHeaderView.Stretch)
#      self.setModel(TableModel())
#      self.resizeColumnsToContents()
#      self.resizeRowsToContents()
#
#     def setmydata(self):
#         horHeaders = [self.data.keys()[x][1][0] for x in range(len(self.data.keys()))]
#         verticalHeaders = [self.data.keys()[x][1][1] for x in range(len(self.data.keys()))]
#         self.setHorizontalHeaderLabels(horHeaders)
#         self.setVerticalHeaderLabels(verticalHeaders)
#         for key in self.data.keys():
#             corr_val = self.data[key]
#             i, j = key[0]
#             corr_val_item = QTableWidgetItem(corr_val)
#             self.setItem(j, i, corr_val_item)
#
#         print('here')


class MyPlugin:
    def __init__(self, project):
        self.name = 'Connectivity Diagram'
        self.widget = Widget(project)

    def run(self):
        pass

if __name__=='__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    data = {('roi1','roi2'): ['1', '2', '3'], ('col2'): ['4', '5', '6'], ('col3'): ['7', '8', '9']}

    w.setCentralWidget(TableWidget())
    w.show()
    app.exec_()
    sys.exit()
