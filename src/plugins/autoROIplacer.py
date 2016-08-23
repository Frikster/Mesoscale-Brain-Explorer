# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import numpy as np
import pyqtgraph as pg

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4 import QtGui


from util.mygraphicsview import MyGraphicsView
from util import fileloader

sys.path.append('..')
import qtutil
import uuid
from util import fileloader
from util.viewboxcustom import MultiRoiViewBox

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
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    anatomy_rois = {"M1": [3, (1.0, 2.5)], "M2": [3, (1.5, 1.75)],
                "AC": [3, (0.0, 0.5)], "HL": [3, (2.0, 0.0)],
                "BC": [3, (3.5, -1.0)], "RS": [3, (0.5, -2.5)], "V1": [3, (2.5, -2.5)]}
    roi_names = anatomy_rois.keys()
    roi_sizes = [anatomy_rois[x][0] for x in anatomy_rois.keys()]
    roi_coord_x = [anatomy_rois[x][1][0] for x in anatomy_rois.keys()]
    roi_coord_y = [anatomy_rois[x][1][1] for x in anatomy_rois.keys()]
    self.headers = ["1) ROI Name", "2) Length", "3) X Coordinate", "4) Y Coordinate"]
    self.data = {self.headers[0]: roi_names, self.headers[1]: roi_sizes,
                 self.headers[2]: roi_coord_x, self.headers[3]: roi_coord_y}

    self.open_dialogs = []

    if not project:
      return
    self.project = project
    self.setup_ui()

    self.listview.setModel(QStandardItemModel())
    self.listview.selectionModel().selectionChanged[QItemSelection,
                                                    QItemSelection].connect(self.selected_video_changed)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.listview.model().appendRow(QStandardItem(f['path']))
    self.listview.setCurrentIndex(self.listview.model().index(0, 0))

    model = RoiItemModel()
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
    self.roi_list.setCurrentIndex(model.index(0, 0))
    #self.view.vb.roi_placed.connect(self.update_roi_names)

  def show_table(self):
    locs = zip(self.data[self.headers[0]], self.data[self.headers[2]], self.data[self.headers[3]])
    model = AutoROICoords(self.data, len(locs), 4)
    model.itemChanged.connect(self.update_auto_rois)
    model.show()
    self.open_dialogs.append(model)

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

    # todo: finish implementing commented out ui elements
    # pb = QPushButton('Create poly ROI')
    # pb.clicked.connect(self.create_roi)
    # vbox.addWidget(pb)

    vbox.addWidget(QLabel('ROI size NxN'))
    self.roi_size = QSpinBox()
    self.roi_size.setMinimum(1)
    self.roi_size.setValue(3)
    vbox.addWidget(self.roi_size)
    pb = QPushButton('auto ROI')
    pb.clicked.connect(self.auto_ROI)
    vbox.addWidget(pb)
    pb = QPushButton('auto ROI table')
    pb.clicked.connect(self.show_table)
    vbox.addWidget(pb)
    pb = QPushButton('Delete selected ROIs')
    pb.clicked.connect(self.delete_roi)
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
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
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
    # rois_selected = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole).toString())
                     for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
    rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
    rois_to_add = [x for x in rois_selected if x not in rois_in_view]
    for roi_to_add in rois_to_add:
      self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])

  # def roi_item_changed(self, prev_name, new_name):
  #   # todo: Why not pass the paramaters as strings? Is it important to have them in this format?
  #   prev_name = str(prev_name)
  #   new_name = str(new_name)
  #   if str(new_name) == '':
  #     qtutil.critical('Choose a name.')
  #   elif str(new_name) in [f['name'] for f in self.project.files if 'name' in f]:
  #     qtutil.critical('ROI name taken.')
  #   self.remove_all_rois()
  #   self.view.vb.loadROI([self.project.path + '/' + str(prev_name) + '.roi'])
  #   roi = self.view.vb.rois[0]
  #   roi.setName(str(new_name))
  #   for i in range(len(self.project.files)):
  #     if self.project.files[i]['path'].endswith(str(prev_name) + '.roi'):
  #       os.rename(self.project.files[i]['path'], self.project.files[i]['path'].replace(prev_name, new_name))
  #       self.project.files[i]['path'] = self.project.files[i]['path'].replace(prev_name, new_name)
  #       self.project.files[i]['name'] = str(new_name)
  #   self.project.save()

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

  def update_auto_rois(self, item):
    col = item.column()
    row = item.row()
    try:
      val = float(item.text())
    except:
      val = str(item.text())
    header = item.tableWidget().horizontalHeaderItem(col).text()
    header = str(header)
    col_to_change = self.data[header]
    col_to_change[row] = val
    self.data[header] = col_to_change
    self.auto_ROI()


  def auto_ROI(self):
    locs = zip(self.data[self.headers[0]], self.data[self.headers[2]], self.data[self.headers[3]])
    half_length = self.roi_size.value() * self.project['mmpixel']

    # model = AutoROICoords(self.data, len(locs), 4)
    # model.itemChanged.connect(self.update_auto_rois)
    # model.show()
    # self.open_dialogs.append(model)

    for tri in locs:
      self.remove_all_rois()
      x1 = (tri[1] - half_length)
      x2 = (tri[1] - half_length)
      x3 = (tri[1] + half_length)
      x4 = (tri[1] + half_length)
      y1 = (tri[2] - half_length)
      y2 = (tri[2] + half_length)
      y3 = (tri[2] + half_length)
      y4 = (tri[2] - half_length)

      self.view.vb.addPolyRoiRequest()
      self.view.vb.autoDrawPolygonRoi(tri[0], pos=QtCore.QPointF(x1, y1))
      self.view.vb.autoDrawPolygonRoi(tri[0], pos=QtCore.QPointF(x2, y2))
      self.view.vb.autoDrawPolygonRoi(tri[0], pos=QtCore.QPointF(x3, y3))
      self.view.vb.autoDrawPolygonRoi(tri[0], pos=QtCore.QPointF(x4, y4))
      self.view.vb.autoDrawPolygonRoi(tri[0], pos=QtCore.QPointF(x4, y4))
      self.view.vb.autoDrawPolygonRoi(tri[0], finished=True)
      roi = self.view.vb.rois[0]
      self.update_project_roi(roi)

class AutoROICoords(QTableWidget):
  def __init__(self, data, *args):
    QTableWidget.__init__(self, *args)
    self.data = data
    self.resizeColumnsToContents()
    self.resizeRowsToContents()
    self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    self.verticalHeader().setResizeMode(QHeaderView.Stretch)
    self.setmydata()


  def setmydata(self):
    horHeaders = self.data.keys()
    for n, key in enumerate(sorted(horHeaders)):
      for m, item in enumerate(self.data[key]):
        newitem = QTableWidgetItem(str(item))
        self.setItem(m, n, newitem)
    self.setHorizontalHeaderLabels(sorted(horHeaders))


class MyPlugin:
  def __init__(self, project):
    self.name = 'Auto ROI placer'
    self.widget = Widget(project)
  
  def run(self):
    pass
