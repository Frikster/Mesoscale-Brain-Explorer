# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import csv
import os
from shutil import copyfile

import numpy as np
import qtutil
from PyQt4 import QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView


#This the code for getting the ROI locations from bregma.

#Bregma is (0,0).

#Units are mm.

#ppmm is number of px per millimeter.  Should be 256 px /10.75 mm for last summer.

#ppmm = size(If2,1)/8.6; #user defined
#ii = 1; #clear pos
#
#pos(ii).name = 'M2'; pos(ii).y = 2.5; pos(ii).x = 1; ii = ii + 1;
#pos(ii).name = 'M1'; pos(ii).y = 1.75; pos(ii).x = 1.5;  ii = ii + 1;
#pos(ii).name = 'AC'; pos(ii).y = 0; pos(ii).x = .5; ii = ii + 1;
#pos(ii).name = 'HL'; pos(ii).y = 0; pos(ii).x = 2;  ii = ii + 1;
#pos(ii).name = 'BC'; pos(ii).y = -1; pos(ii).x = 3.5; ii = ii + 1;
#pos(ii).name = 'RS'; pos(ii).y = -2.5; pos(ii).x = .5;  ii = ii + 1;
#pos(ii).name = 'V1'; pos(ii).y = -2.5; pos(ii).x = 2.5; ii = ii + 1;
#
##clear xx yy yy2
#for i = 1:length(pos)
#    xx(i) = yb + -ppmm*pos(i).y;
#    yy(i) = xb - ppmm*pos(i).x;
#    yy2(i) = xb + ppmm*pos(i).x;
#end
#xx = round([xx xx]);
#yy = round([yy yy2]);


class RoiItemModel(QAbstractListModel):
  textChanged = pyqtSignal(str, str)
  #dataChanged = pyqtSignal(int, int)

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
    if role in [Qt.DisplayRole, Qt.EditRole]:
      self.textChanged.emit(self.rois[index.row()], value)
      self.rois[index.row()] = str(value)
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
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    # check project
    if not project:
      return
    self.project = project

    # define widgets
    self.headers = None
    self.data = None
    self.view = MyGraphicsView(self.project)
    self.table_widget = AutoROICoords(self.data, 0, 4)
    self.left = QFrame()
    self.right = QFrame()

    self.setup_ui()

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.video_list.doubleClicked.connect(self.video_triggered)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.video_list.model().appendRow(QStandardItem(str(f['name'])))
    self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    model = RoiItemModel()
    # todo: this wont update that specific changed value
    self.view.vb.roi_placed.connect(self.update_project_roi)
    model.textChanged.connect(self.update_project_roi)
    self.roi_list.setModel(model)
    self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # A flag to see whether selected_roi_changed is being entered for the first time
    self.selected_roi_changed_flag = 0
    self.roi_list.selectionModel().selectionChanged[QItemSelection,
                                                    QItemSelection].connect(self.selected_roi_changed)
    roi_names = [f['name'] for f in project.files if f['type'] == 'roi']
    for roi_name in roi_names:
      if roi_name not in self.roi_list.model().rois:
        model.appendRoi(roi_name)

      # setup roi table
      if 'roi_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
          self.data = None
          self.headers = None
      else:
          text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
                            if self.project.files[x]['type'] == 'roi_table']
          assert (len(text_file_path) == 1)
          text_file_path = text_file_path[0]
          roi_table = []  # numpy way: np.empty(shape=(4, ))
          with open(text_file_path, 'rt', encoding='ascii') as csvfile:
              roi_table_it = csv.reader(csvfile, delimiter=',')
              for row in roi_table_it:
                  roi_table = roi_table + [row]
          roi_table = np.array(roi_table)
          self.headers = [str.strip(x) for x in roi_table[0,]]
          roi_table_range = range(len(roi_table))[1:]
          roi_names = [roi_table[x, 0] for x in roi_table_range]
          roi_sizes = [int(roi_table[x, 1]) for x in roi_table_range]
          roi_coord_x = [float(roi_table[x, 2]) for x in roi_table_range]
          roi_coord_y = [float(roi_table[x, 3]) for x in roi_table_range]
          self.data = {self.headers[0]: roi_names, self.headers[1]: roi_sizes,
                       self.headers[2]: roi_coord_x, self.headers[3]: roi_coord_y}
          if text_file_path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
              self.project.files.append({
                  'path': text_file_path,
                  'type': 'roi_table',
                  'source_video': self.video_path,
                  'name': os.path.basename(text_file_path)
              })
          self.table_widget.clear()
          self.table_widget.setRowCount(len(self.data[self.headers[0]]))
          self.table_widget.update(self.data)

  def video_triggered(self, index):
      pfs.video_triggered(self, index)
  # def roi_item_edited(self, item):
  #   new_name = item.text()
  #   prev_name = item.data(Qt.UserRole)
  #   # disconnect and reconnect signal
  #   self.roi_list.itemChanged.disconnect()
  #   item.setData(new_name, Qt.UserRole)
  #   self.roi_list.model().itemChanged[QStandardItem.setData].connect(self.roi_item_edited)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    list_of_manips = pfs.get_list_of_project_manips(self.project)
    self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    vbox.addWidget(self.toolbutton)
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list = QListView()
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    vbox.addWidget(self.video_list)
    pb = QPushButton('Load anatomical coordinates (relative to selected origin)')
    pb.clicked.connect(self.load_ROI_table)
    vbox.addWidget(pb)
    vbox.addWidget(self.table_widget)
    self.table_widget.itemChanged.connect(self.update_auto_rois)
    pb = QPushButton('Add these ROIs to project')
    pb.clicked.connect(self.auto_ROI)
    vbox.addWidget(pb)
    # vbox2 = QVBoxLayout()
    # w = QWidget()
    # w.setLayout(vbox2)
    # vbox.addWidget(w)
    vbox.addWidget(qtutil.separator())
    vbox.addWidget(QLabel('ROIs'))
    self.roi_list = QListView()
    vbox.addWidget(self.roi_list)
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
    if self.selected_roi_changed_flag == 0:
      self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
      return
    if not selection.indexes() or self.view.vb.drawROImode:
      return

    self.remove_all_rois()
    # todo: re-explain how you can figure out to go from commented line to uncommented line
    # rois_selected = str(selection.indexes()[0].data(Qt.DisplayRole))
    rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
                     for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
    rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
    rois_to_add = [x for x in rois_selected if x not in rois_in_view]
    for roi_to_add in rois_to_add:
      self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])

  def load_ROI_table(self):
      text_file_path = QFileDialog.getOpenFileName(
          self, 'Load images', QSettings().value('last_load_text_path'),
          'Video files (*.csv *.txt)')
      if not text_file_path:
          return
      QSettings().setValue('last_load_text_path', os.path.dirname(text_file_path))

      roi_table = [] # numpy way: np.empty(shape=(4, ))
      with open(text_file_path, 'rt', encoding='ascii') as csvfile:
         roi_table_it = csv.reader(csvfile, delimiter=',')
         for row in roi_table_it:
           roi_table = roi_table + [row]
      roi_table = np.array(roi_table)
      self.headers = [str.strip(x) for x in roi_table[0, ]]
      roi_table_range = range(len(roi_table))[1:]
      roi_names = [str(roi_table[x, 0]) for x in roi_table_range]
      roi_sizes = [int(roi_table[x, 1]) for x in roi_table_range]
      roi_coord_x = [float(roi_table[x, 2]) for x in roi_table_range]
      roi_coord_y = [float(roi_table[x, 3]) for x in roi_table_range]
      self.data = {self.headers[0]: roi_names, self.headers[1]: roi_sizes,
      self.headers[2]: roi_coord_x, self.headers[3]: roi_coord_y}
      text_file_path_for_project = os.path.join(self.project.path, os.path.basename(text_file_path))
      # for now only support having one roi_table associated per project
      if 'roi_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
        if text_file_path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
            if not (os.path.normpath(text_file_path) ==
                        os.path.normpath(text_file_path_for_project)):
                copyfile(text_file_path, text_file_path_for_project)
            self.project.files.append({
            'path': text_file_path_for_project,
            'type': 'roi_table',
            'source_video': self.video_path,
            'name': os.path.basename(text_file_path)
          })
        else:
          # Replace old values if the same file with different values is given
          for i, item in enumerate(self.project.files):
              if item['path'] == text_file_path_for_project:
                  self.project.files[i] = {
                  'path': text_file_path_for_project,
                  'type': 'roi_table',
                  'source_video': self.video_path,
                  'name': os.path.basename(text_file_path)
              }
      else:
          # Replace old table with new one
          # todo: remove duplicates
          for i, item in enumerate(self.project.files):
              if item['type'] == 'roi_table':
                  self.project.files[i] = {
                  'path': text_file_path_for_project,
                  'type': 'roi_table',
                  'source_video': self.video_path,
                  'name': os.path.basename(text_file_path)
              }
      self.table_widget.clear()
      self.table_widget.setRowCount(len(self.data[self.headers[0]]))
      self.table_widget.update(self.data)
      self.auto_ROI()

  def auto_ROI(self):
    locs = zip(self.data[self.headers[0]], self.data[self.headers[1]],
               self.data[self.headers[2]], self.data[self.headers[3]])

    # Warning: size must always be the second column
    for quad in list(locs):
      half_length = quad[1] * (self.project['unit_per_pixel']/2)
      self.remove_all_rois()
      x1 = (quad[2] - half_length)
      x2 = (quad[2] - half_length)
      x3 = (quad[2] + half_length)
      x4 = (quad[2] + half_length)
      y1 = (quad[3] - half_length)
      y2 = (quad[3] + half_length)
      y3 = (quad[3] + half_length)
      y4 = (quad[3] - half_length)

      self.view.vb.addPolyRoiRequest()
      self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x1, y1))
      self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x2, y2))
      self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x3, y3))
      self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x4, y4))
      self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x4, y4))
      self.view.vb.autoDrawPolygonRoi(quad[0], finished=True)
      assert (len(self.view.vb.rois) == 1)
      roi = self.view.vb.rois[0]
      self.update_project_roi(roi)

  # def update_table(self):
  #   locs = zip(self.data[self.headers[0]], self.data[self.headers[1]],
  #              self.data[self.headers[2]], self.data[self.headers[3]])
  #   model = AutoROICoords(self.data, len(list(locs)), 4)
  #   model.show()
  #   # self.open_dialogs.append(model)

  # def delete_roi(self):
  #   rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
  #                    for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
  #   if rois_selected == None:
  #     return
  #   rois_dict = [self.project.files[x] for x in range(len(self.project.files))
  #                if (self.project.files[x]['type'] == 'roi' and self.project.files[x]['name'] in rois_selected)]
  #   self.project.files = [self.project.files[x] for x in range(len(self.project.files))
  #                         if self.project.files[x] not in rois_dict]
  #   self.project.save()
  #   self.view.vb.setCurrentROIindex(None)
  #
  #   for roi_to_remove in [rois_dict[x]['name'] for x in range(len(rois_dict))]:
  #     self.roi_list.model().removeRow(roi_to_remove)

  def update_project_roi(self, roi):
    name = roi.name
    if not name:
      raise ValueError('ROI has no name')
    if self.view.vb.drawROImode:
      return

    path = os.path.join(self.project.path, name + '.roi')
    self.view.vb.saveROI(path)
    # TODO check if saved, notifiy user of save and save location (really needed if they can simply export?)
    if path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
      self.project.files.append({
        'path': path,
        'type': 'roi',
        'source_video': self.video_path,
        'name': name
      })
    else:
      for i, file in enumerate(self.project.files):
        if file['path'] == path:
          self.project.files[i]['source_video'] = self.video_path
    self.project.save()

    roi_names = [f['name'] for f in self.project.files if f['type'] == 'roi']
    for roi_name in roi_names:
      if roi_name not in self.roi_list.model().rois:
        self.roi_list.model().appendRoi(roi_name)

  #even tried deleting everything...
  # roi_names = [f['name'] for f in self.project.files if f['type'] == 'roi']
  # for roi_name in roi_names:
  #     if roi_name not in self.roi_list.model().rois:
  #         self.roi_list.model().appendRoi(roi_name)

  def update_auto_rois(self, item):
    col = item.column()
    row = item.row()
    try:
      val = float(item.text())
    except:
      val = str(item.text())
    if item.tableWidget().horizontalHeaderItem(col):
        header = item.tableWidget().horizontalHeaderItem(col).text()
        header = str(header)
        col_to_change = self.data[header]
        col_to_change[row] = val
        self.data[header] = col_to_change
        self.auto_ROI()




class AutoROICoords(QTableWidget):
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
      self.resizeColumnsToContents()
      self.resizeRowsToContents()
      self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
      self.verticalHeader().setResizeMode(QHeaderView.Stretch)
      if self.data is not None:
        self.setmydata()


class MyPlugin:
  def __init__(self, project):
    self.name = 'Auto ROI placer'
    self.widget = Widget(project)
  
  def run(self):
    pass
