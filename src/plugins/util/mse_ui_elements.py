#!/usr/bin/env python3
import os

import numpy as np
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import fileloader
from .mygraphicsview import MyGraphicsView


class Video_Selector(QListView):
  active_vid_changed = pyqtSignal(str, int)

  def __init__(self, parent=None):
    super(Video_Selector, self).__init__(parent)
    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')

  def currentChanged(self, current, previous):
    super(Video_Selector, self).currentChanged(current, previous)
    vid_name = str(current.data(Qt.UserRole))
    vid_position = current.row()
    self.active_vid_changed.emit(vid_name, vid_position)

# class Video_Selector:
#     def __init__(self, project, view):
#         self.project = project
#         self.view = view
#
#     def selected_video_changed(self, selected, deselected):
#         if not selected.indexes():
#             return
#
#         for index in deselected.indexes():
#             vidpath = str(os.path.join(self.project.path,
#                                      index.data(Qt.DisplayRole))
#                               + '.npy')
#             self.selected_videos = [x for x in self.selected_videos if x != vidpath]
#         for index in selected.indexes():
#             vidpath = str(os.path.join(self.project.path,
#                                      index.data(Qt.DisplayRole))
#                               + '.npy')
#         if vidpath not in self.selected_videos and vidpath != 'None':
#             self.selected_videos = self.selected_videos + [vidpath]
#
#         self.shown_video_path = str(os.path.join(self.project.path,
#                                            selected.indexes()[0].data(Qt.DisplayRole))
#                               + '.npy')
#         frame = fileloader.load_reference_frame(self.shown_video_path)
#         self.view.show(frame)

class RoiItemModel(QAbstractListModel):
    textChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(RoiItemModel, self).__init__(parent)
        self.rois = []

    def appendRoi(self, name):
        self.rois.append(name)
        row = len(self.rois) - 1
        self.dataChanged.emit(self.index(row), self.index(row))

    def edit_roi_name(self, name, index):
        self.rois.append(name)
        row = len(self.rois) - 1
        self.dataChanged.emit(self.index(row), self.index(row))

    def rowCount(self, parent):
        return len(self.rois)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.rois[index.row()]
        return

    def setData(self, index, value, role):
      if role == Qt.EditRole:
        value = str(value)
        if value in self.rois[index.row()]:
          pass
        elif value in self.rois:
          qtutil.critical('Roi name taken.')
        else:
          self.textChanged.emit(self.rois[index.row()], value)
          self.rois[index.row()] = value
        return True
      return super(RoiItemModel, self).setData(index, value, role)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def removeRow(self, roi_to_remove):
        for roi in self.rois:
            if roi == roi_to_remove:
                del roi
                break

class RoiList(QListView):
    class Labels(object):
        roi_list_indices_label = "ROIs"

    class Defaults(object):
        roi_list_indices_default = [0]

    def __init__(self, widget, roi_types):
        super(RoiList, self).__init__()
        self.setModel(RoiItemModel())
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.widget = widget

        self.selected_roi_changed_flag = 0
        roi_names = [f['name'] for f in self.widget.project.files if f['type'] in roi_types]
        for roi_name in roi_names:
            if roi_name not in self.model().rois:
                self.model().appendRoi(roi_name)

        self.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_roi_changed)

    def selected_roi_changed(self, selection):
        if self.selected_roi_changed_flag == 0:
            self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
            return
        if not selection.indexes() or self.widget.view.vb.drawROImode:
            return

        self.remove_all_rois()
        rois_selected = [str(self.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
                          for x in range(len(self.selectionModel().selectedIndexes()))]
        rois_in_view = [self.widget.view.vb.rois[x].name for x in range(len(self.widget.view.vb.rois))]
        rois_to_add = [x for x in rois_selected if x not in rois_in_view]
        for roi_to_add in rois_to_add:
            self.widget.view.vb.loadROI([self.widget.project.path + '/' + roi_to_add + '.roi'])

    def remove_all_rois(self):
        rois = self.widget.view.vb.rois[:]
        for roi in rois:
            if not roi.isSelected:
                self.widget.view.vb.selectROI(roi)
            self.widget.view.vb.removeROI()

    def setup_params(self, reset=False):
        if len(self.widget.params) == 1 or reset:
            self.widget.update_plugin_params(self.Labels.roi_list_indices_label, self.Defaults.roi_list_indices_default)
        roi_indices = self.widget.params[self.Labels.roi_list_indices_label]
        theQIndexObjects = [self.model().createIndex(rowIndex, 0) for rowIndex in
                            roi_indices]
        for Qindex in theQIndexObjects:
            self.selectionModel().select(Qindex, QItemSelectionModel.Select)

    def setup_param_signals(self):
        self.selectionModel().selectionChanged.connect(self.prepare_roi_list_for_update)

    def prepare_roi_list_for_update(self, selected, deselected):
        val = [v.row() for v in self.selectedIndexes()]
        self.widget.update_plugin_params(self.Labels.roi_list_indices_label, val)

class InfoWidget(QFrame):
    def __init__(self, text, parent=None):
        super(InfoWidget, self).__init__(parent)
        self.setup_ui(text)

    def setup_ui(self, text):
        hbox = QHBoxLayout()
        icon = QLabel()
        image = QImage('pics/info.png')
        icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
        hbox.addWidget(icon)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        hbox.addWidget(self.label)
        hbox.addStretch()
        self.setLayout(hbox)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class WarningWidget(QFrame):
    def __init__(self, text, parent=None):
        super(WarningWidget, self).__init__(parent)
        self.setup_ui(text)

    def setup_ui(self, text):
        hbox = QHBoxLayout()
        icon = QLabel()
        image = QImage('pics/delete.png')
        icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
        hbox.addWidget(icon)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        hbox.addWidget(self.label)
        hbox.addStretch()
        self.setLayout(hbox)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class CheckableComboBox(QtGui.QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

class PlayerDialog(QDialog):
  def __init__(self, project, filename, parent=None, scaling=True):
    super(PlayerDialog, self).__init__(parent)
    self.project = project
    self.setup_ui()

    self.scale = scaling
    self.fp = np.load(filename, mmap_mode='r')
    if isinstance(scaling, bool) and scaling:
        self.global_min = np.min(self.fp)
        self.global_max = np.max(self.fp)
    if isinstance(scaling, tuple):
        self.global_min = scaling[0]
        self.global_max = scaling[1]
    self.slider.setMaximum(len(self.fp)-1)
    self.show_frame(0)

  def show_frame(self, frame_num):
    frame = self.fp[frame_num]
    self.label_frame.setText(str(frame_num) + ' / ' + str(len(self.fp)-1))
    if hasattr(self, 'global_min') and hasattr(self, 'global_max'):
        self.view.show(frame, self.global_min, self.global_max)
    else:
        self.view.show(frame)

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    hbox = QHBoxLayout()
    self.slider = QSlider(Qt.Horizontal)
    self.slider.valueChanged.connect(self.slider_moved)
    hbox.addWidget(self.slider)
    self.label_frame = QLabel('- / -')
    hbox.addWidget(self.label_frame)
    vbox.addLayout(hbox)
    self.setLayout(vbox)

  def slider_moved(self, value):
    self.show_frame(value)