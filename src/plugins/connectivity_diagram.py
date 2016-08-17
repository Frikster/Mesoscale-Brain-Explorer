#!/usr/bin/env python

import os, sys
import numpy as np
import random

from scipy import stats
import matplotlib.pylab as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util import fileloader

import uuid
import psutil
import qtutil


class RoiItemModel(QAbstractListModel):
    textChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(RoiItemModel, self).__init__(parent)
        self.rois = []

    def appendRoi(self, name):
        self.rois.append(name)
        row = len(self.rois) - 1
        self.dataChanged.emit(self.index(row), self.index(row))

    def rowCount(self, parent):
        return len(self.rois)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.rois[index.row()]
        return QVariant()

    def setData(self, index, value, role):
        if role in [Qt.DisplayRole, Qt.EditRole]:
            self.textChanged.emit(self.rois[index.row()], value.toString())
            self.rois[index.row()] = str(value.toString())
            return True
        return super(RoiItemModel, self).setData(index, value, role)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def removeRow(self, roi_to_remove):
        for roi in self.rois:
            if roi == roi_to_remove:
                del roi
                break


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
            self.listview.model().appendRow(QStandardItem(f['path']))
        self.listview.setCurrentIndex(self.listview.model().index(0, 0))

        model = RoiItemModel()
        model.textChanged.connect(self.roi_item_changed)
        self.roi_list.setModel(model)
        self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # A flag to see whether selected_roi_changed is being entered for the first time
        self.selected_roi_changed_flag = 0
        self.roi_list.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_roi_changed)
        roi_names = [f['name'] for f in project.files if f['type'] == 'roi']
        for roi_name in roi_names:
            model.appendRoi(roi_name)
        self.roi_list.setCurrentIndex(model.index(0, 0))
        self.view.vb.roi_placed.connect(self.update_roi_names)

    def roi_item_edited(self, item):
        new_name = item.text()
        prev_name = item.data(Qt.UserRole)
        # disconnect and reconnect signal
        self.roi_list.itemChanged.disconnect()
        item.setData(new_name, Qt.UserRole)
        self.roi_list.model().itemChanged[QStandardItem.setData].connect(self.roi_item_edited)

    def setup_ui(self):
        hbox = QHBoxLayout()

        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.listview = QListView()
        self.listview.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.listview)

        pb = QPushButton('Create poly ROI')
        pb.clicked.connect(self.create_roi)
        vbox.addWidget(pb)
        pb = QPushButton('Crop poly ROI')
        pb.clicked.connect(self.crop_ROI)
        vbox.addWidget(pb)
        pb = QPushButton('Delete selected ROIs')
        pb.clicked.connect(self.delete_roi)
        vbox.addWidget(pb)

        vbox.addWidget(qtutil.separator())

        pb = QPushButton('Connectivity Diagram')
        pb.clicked.connect(self.connectivity_diagram)
        vbox.addWidget(pb)

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
        self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
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

    def roi_item_changed(self, prev_name, new_name):
        # todo: Why not pass the paramaters as strings? Is it important to have them in this format?
        prev_name = str(prev_name)
        new_name = str(new_name)
        if str(new_name) == '':
            qtutil.critical('Choose a name.')
            return
        elif str(new_name) in [f['name'] for f in self.project.files if 'name' in f]:
            qtutil.critical('ROI name taken.')
            return
        self.remove_all_rois()
        self.view.vb.loadROI([self.project.path + '/' + str(prev_name) + '.roi'])
        roi = self.view.vb.rois[0]
        roi.setName(str(new_name))
        for i in range(len(self.project.files)):
            if self.project.files[i]['path'].endswith(str(prev_name) + '.roi'):
                os.rename(self.project.files[i]['path'], self.project.files[i]['path'].replace(prev_name, new_name))
                self.project.files[i]['path'] = self.project.files[i]['path'].replace(prev_name, new_name)
                self.project.files[i]['name'] = str(new_name)
        self.project.save()

    def update_roi_names(self, roi):
        if self.view.vb.drawROImode:
            return

        name = str(uuid.uuid4())
        if not name:
            qtutil.critical('Choose a name.')
        elif name in [f['name'] for f in self.project.files if 'name' in f]:
            qtutil.critical('ROI name taken.')
        else:
            roi.setName(name)
            path = os.path.join(self.project.path, name + '.roi')
            self.view.vb.saveROI(path)
            # TODO check if saved, notifiy user of save and save location (really needed if they can simply export?)
            self.project.files.append({
                'path': path,
                'type': 'roi',
                'source_video': self.video_path,
                'name': name
            })
            self.project.save()

            roi_names = [f['name'] for f in self.project.files if f['type'] == 'roi']
            for roi_name in roi_names:
                if roi_name not in self.roi_list.model().rois:
                    self.roi_list.model().appendRoi(roi_name)

    def create_roi(self):
        self.view.vb.addPolyRoiRequest()

    def delete_roi(self):
        rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole).toString())
                         for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
        if rois_selected == None:
            return
        rois_dict = [self.project.files[x] for x in range(len(self.project.files))
                     if (self.project.files[x]['type'] == 'roi' and self.project.files[x]['name'] in rois_selected)]
        self.project.files = [self.project.files[x] for x in range(len(self.project.files))
                              if self.project.files[x] not in rois_dict]
        self.project.save()
        self.view.vb.setCurrentROIindex(None)

        for roi_to_remove in [rois_dict[x]['name'] for x in range(len(rois_dict))]:
            self.roi_list.model().removeRow(roi_to_remove)

    def crop_ROI(self):
        frames = fileloader.load_file(self.video_path)
        # Return if there is no image or rois in view
        if self.view.vb.img == None or len(self.view.vb.rois) == 0:
            print("there is no image or rois in view ")
            return

        # swap axis for aligned_frames
        frames_swap = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)
        # Collect ROI's and combine
        numROIs = len(self.view.vb.rois)
        arrRegion_masks = []
        for i in xrange(numROIs):
            roi = self.view.vb.rois[i]
            arrRegion_mask = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
            arrRegion_masks.append(arrRegion_mask)

        combined_mask = np.sum(arrRegion_masks, axis=0)
        # Make all rows with all zeros na
        combined_mask[(combined_mask == 0)] = None
        self.mask = combined_mask
        # TODO: save mask as well
        # #combined_mask.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"mask.raw")
        # print("mask saved to " + os.path.expanduser('/Downloads/')+"mask.raw")

        roi_frames = (frames * combined_mask[np.newaxis, :, :])

        # todo: solve issue where rerunning this will overwrite any previous 'roi.npy'
        path = os.path.join(self.project.path, 'roi' + '.npy')
        np.save(path, roi_frames)
        self.project.files.append({
            'path': path,
            'type': 'video',
            'source_video': self.video_path,
            'manipulations': ['crop']
        })

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
        numROIs = len(self.view.vb.rois)
        for i in xrange(numROIs):
            roi = self.view.vb.rois[i]
            arrRegion_mask = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
            #arrRegion_mask[(arrRegion_mask == 0)] = None
            mask_size = np.count_nonzero(arrRegion_mask)
            roi_frames = (frames * arrRegion_mask[np.newaxis, :, :])
            roi_frames_flatten = np.ndarray.sum(np.ndarray.sum(roi_frames, axis=1), axis=1)
            avg_of_rois[roi] = roi_frames_flatten/mask_size

        connectivity_matrix = {}
        for roi1 in self.view.vb.rois:
            for roi2 in self.view.vb.rois:
                connectivity_matrix[(roi1, roi2)] = stats.pearsonr(
                    avg_of_rois[roi1], avg_of_rois[roi2])[0]

        w = QMainWindow()
        w.setCentralWidget(TableView(self.project, connectivity_matrix, self))
        #dialog = TableView(self.project, connectivity_matrix, self)
        w.show()
        self.open_dialogs.append(w)

class TableModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(TableModel, self).__init__(parent)

    self.setRowCount(20)
    self.setColumnCount(16)
    #plt.cm.jet(spc_map)

  def data(self, index, role):
    if role == Qt.BackgroundRole:
      r, g, b = [random.randint(0, 255) for _ in range(3)]
      return QColor(r, g, b)
    elif role == Qt.DisplayRole:
      value = round(random.random(), 2)
      return str(value)
    elif role == Qt.TextAlignmentRole:
      return Qt.AlignCenter
    super(TableModel, self).data(index, role)

class TableView(QTableView):
   def __init__(self, project, connectivity_matrix, parent=None):
     super(TableView, self).__init__(parent)

     self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
     self.verticalHeader().setResizeMode(QHeaderView.Stretch)
     self.horizontalHeader().hide()
     self.verticalHeader().hide()
     self.setModel(TableModel())
     self.resizeColumnsToContents()
     self.resizeRowsToContents()



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
    w.setCentralWidget(Widget())
    w.show()
    app.exec_()
    sys.exit()
