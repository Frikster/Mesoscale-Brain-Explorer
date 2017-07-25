#!/usr/bin/env python3

import os

import numpy as np
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import file_io
from .mygraphicsview import MyGraphicsView
import qtutil


class JSObjectModel(QAbstractTableModel):
  def __init__(self, data, parent=None):
    super(JSObjectModel, self).__init__(parent)
    self._data = data

    cols = []
    for obj in data:
      cols.extend(obj.keys())
    self.cols = list(set(cols))

  def rowCount(self, parent):
    return len(self._data)

  def columnCount(self, parent): 
    return len(self.cols)

  def data(self, index, role):
    if role == Qt.DisplayRole:
      col = self.cols[index.column()]
      obj = self._data[index.row()]
      return col in obj and obj[col] or ''
    return

  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole and orientation == Qt.Horizontal:
      return self.cols[section]
    return

  def retrieve(self, row, key=None):
    obj = self._data[row]
    if key:
      return obj[key]
    else:
      return obj

class FileTableModel(JSObjectModel):
  def __init__(self, data, parent=None):
    super(FileTableModel, self).__init__(data, parent)

  def get_path(self, index):
    return self.retrieve(index.row(), 'path')
  
  def get_entry(self, index):
    return self.retrieve(index.row())

class FileTable(QTableView):
  def __init__(self, project=None, parent=None):
    super(FileTable, self).__init__(parent)

    self.verticalHeader().hide()
    self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
    # self.horizontalHeader().setStretchLastSection(True)
    self.setSelectionBehavior(QAbstractItemView.SelectRows) 

    if project:
      self.setModel(FileTableModel(project))

  def selected_paths(self):
    selection = self.selectionModel().selectedRows()
    filenames = [self.model().get_path(index) for index in selection]
    return filenames

class ImageStackListView(QListView):
    video_player_scaled_signal = pyqtSignal()
    video_player_unscaled_signal = pyqtSignal()
    delete_signal = pyqtSignal()
    detatch_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(ImageStackListView, self).__init__(parent)
        self.setStyleSheet('QListView::item { height: 26px; }')

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        submenu1 = menu.addMenu("Open Video Player")
        submenu2 = menu.addMenu("Remove Files")
        video_player_scaled_action = submenu1.addAction("Scaled (takes time to establish scale)")
        video_player_unscaled_action = submenu1.addAction("Unscaled (loads fast)")
        delete_action = submenu2.addAction("Delete Permanently")
        detatch_action = submenu2.addAction("Detatch from Project")

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == video_player_scaled_action:
            self.video_player_scaled_signal.emit()
        if action == video_player_unscaled_action:
            self.video_player_unscaled_signal.emit()
        if action == delete_action:
            self.delete_signal.emit()
        if action == detatch_action:
            self.detatch_signal.emit()

class MyProgressDialog(QProgressDialog):
  def __init__(self, title, desc, parent=None):
    super(MyProgressDialog, self).__init__(desc, str(), 0, 100, parent)
    # super(MyProgressDialog, self).__init__(desc, QString(), 0, 100, parent)
    self.setWindowTitle(title)
    self.setAutoClose(True)
    self.setMinimumDuration(0)


class InfoWidget(QFrame):
  def __init__(self, text, parent=None):
    super(InfoWidget, self).__init__(parent)
    self.setup_ui(text)
  
  def setup_ui(self, text):
    hbox = QHBoxLayout()
    icon = QLabel()
    image = QImage('pics/info.png')
    icon.setPixmap(QPixmap.fromImage(image.scaled(30, 30)))
    hbox.addWidget(icon)
    self.label = QLabel(text)
    self.label.setWordWrap(True)
    hbox.addWidget(self.label)
    #hbox.addStretch()
    hbox.setStretch(0, 0)
    hbox.setStretch(1, 1)
    self.setLayout(hbox)

    self.setFrameStyle(QFrame.Panel | QFrame.Raised)
    self.setLineWidth(2)
    self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')
    

# Added from mse_ui_elements merge (commit 8f0d28d2a22430a7e3f3494c249dc22fac510ff1)

# List with more useful currentChangedTo signal (current and previous in currentSelect are rarely used)
# Plan was to make this the superclass for ImageStackListView
class MyListView(QListView):
  currentChangedTo = pyqtSignal(str, int)

  def __init__(self, parent=None):
    super(MyListView, self).__init__(parent)
    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')

  def currentChanged(self, current, previous):
    super(MyListView, self).currentChanged(current, previous)
    name = str(current.data(Qt.UserRole))
    position = current.row()
    self.currentChangedTo.emit(name, position)

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

    def __init__(self, widget, roi_types, standard_model=False):
        super(RoiList, self).__init__()
        self.widget = widget
        roi_names = [f['name'] for f in self.widget.project.files if f['type'] in roi_types]
        if not standard_model:
            self.setModel(RoiItemModel())
            self.selected_roi_changed_flag = 0
            for roi_name in roi_names:
                if roi_name not in self.model().rois:
                    self.model().appendRoi(roi_name)
        else:
            self.setModel(RoiModel())
            for f in widget.project.files:
                if f['type'] in roi_types:
                    item = QStandardItem(f['name'])
                    item.setData(f['path'], Qt.UserRole)
                    self.model().appendRow(item)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)



        self.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_roi_changed)

    def selected_roi_changed(self, selection):
        # if self.selected_roi_changed_flag == 0:
        #   self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
        #   return
        if not selection.indexes() or self.widget.view.vb.drawROImode:
            return
        self.remove_all_rois()

        # todo: re-explain how you can figure out to go from commented line to uncommented line
        # rois_selected = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
        rois_selected = [str(self.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
                         for x in range(len(self.selectionModel().selectedIndexes()))]
        if 'None' in rois_selected:
            return
        rois_in_view = [self.widget.view.vb.rois[x].name for x in range(len(self.widget.view.vb.rois))]
        rois_to_add = [x for x in rois_selected if x not in rois_in_view]
        for roi_to_add in rois_to_add:
            self.widget.view.vb.loadROI([self.widget.project.path + '/' + roi_to_add + '.roi'])

    # def selected_roi_changed(self, selection):
    #     if self.selected_roi_changed_flag == 0:
    #         self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
    #         return
    #     if not selection.indexes() or self.widget.view.vb.drawROImode:
    #         return
    #
    #     self.widget.remove_all_rois()
    #     rois_selected = [str(self.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
    #                       for x in range(len(self.selectionModel().selectedIndexes()))]
    #     rois_in_view = [self.widget.view.vb.rois[x].name for x in range(len(self.widget.view.vb.rois))]
    #     rois_to_add = [x for x in rois_selected if x not in rois_in_view]
    #     for roi_to_add in rois_to_add:
    #         self.widget.view.vb.loadROI([self.widget.project.path + '/' + roi_to_add + '.roi'])

    def remove_all_rois(self):
        rois = self.widget.view.vb.rois[:]
        for roi in rois:
            if not roi.isSelected:
                self.widget.view.vb.selectROI(roi)
            self.widget.view.vb.removeROI()

    def setup_params(self, reset=False):
        if len(self.widget.params) == 3 or reset:
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

class MyTableWidget(QTableWidget):
  def __init__(self, data=None, *args):
    QTableWidget.__init__(self, *args)
    self.data = data
    self.update(self.data)

  def setmydata(self):
    horHeaders = self.data.keys()
    for n, key in enumerate(sorted(horHeaders)):
      for m, item in enumerate(self.data[key]):
        newitem = QTableWidgetItem(str(item))
        self.setItem(m, n, newitem)
    self.setHorizontalHeaderLabels(sorted(horHeaders))

  def update(self, data):
      self.data = data
      # self.resizeColumnsToContents()
      # self.resizeRowsToContents()
      self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
      self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
      if self.data is not None:
        self.setmydata()

class PlayerDialog(QDialog):
  def __init__(self, project, filename, parent=None, scaling=True):
    super(PlayerDialog, self).__init__(parent)
    self.project = project
    self.setup_ui()
    self.setWindowTitle(os.path.basename(filename))

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
