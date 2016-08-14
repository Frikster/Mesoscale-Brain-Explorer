# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import numpy as np

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util import fileloader

sys.path.append('..')
import qtutil
import uuid

class RoiItemModel(QAbstractListModel):
  textChanged = pyqtSignal(str, str)

  def __init__(self, parent=None):
    super(RoiItemModel, self).__init__(parent)
    self.rois = []

  def appendRoi(self, name):
    self.rois.append(name)

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
    

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return
    self.project = project
    self.setup_ui()

    self.rois_in_view = {}

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
    self.roi_list.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_roi_changed)
    rois = [f['name'] for f in project.files if f['type'] == 'roi']
    for roi in rois: 
      model.appendRoi(roi)
    self.roi_list.setCurrentIndex(model.index(0, 0))

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

    vbox.addWidget(qtutil.separator())

    vbox2 = QVBoxLayout()
    pb = QPushButton('Save')
    pb.clicked.connect(self.save_roi)
    vbox2.addWidget(pb)
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

  def roi_item_changed(self, prev_name, new_name):
    print(prev_name, new_name)
    

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)

  def selected_roi_changed(self, selection):
    if not selection.indexes():
      return
    roi_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    if roi_path in self.rois_in_view.keys():
      roi = self.rois_in_view[roi_path]
      self.view.vb.selectROI(roi)
    else:
      self.view.vb.loadROI([self.project.path+'/'+roi_path+'.roi'])
    self.update_rois_in_view()

  def update_rois_in_view(self):
    rois = self.view.vb.rois
    for roi in rois:
      if roi not in self.rois_in_view.items():
        self.view.vb.selectROI(roi)
        self.view.vb.removeROI()
        #key = (key for key, value in self.rois_in_view.items() if value == roi).next()
        #del self.rois_in_view[key]

  def create_roi(self):
    self.view.vb.addPolyRoiRequest()
    for f in self.project.files:
      if f['type'] != 'roi':
        continue
      self.roi_list.model().appendRow(QStandardItem(f['path']))
    self.roi_list.setCurrentIndex(self.roi_list.model().index(0, 0))

  def save_roi(self):
    name = str(uuid.uuid4())
    if not name:
      qtutil.critical('Choose a name.')
    elif name in [f['name'] for f in self.project.files if 'name' in f]:
      qtutil.critical('ROI name taken.')
    else:
      path = os.path.join(self.project.path, name + '.roi')
      self.view.vb.saveROI(path)
      #TODO check if saved, notifiy user of save and save location (really needed if they can simply export?)
      self.project.files.append({
        'path': path,
        'type': 'roi',
        'source_video': self.video_path,
        'name': name
      })
      self.rois_in_view[self.video_path] = self.view.vb.rois[self.view.vb.currentROIindex]
      ### self.roi_list
      self.project.save()

  def crop_ROI(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    # todo: make videos selectable.
    fileName = videos[0]['path']

    frames = fileloader.load_file(fileName)
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

    # In imageJ - Gap Between Images The number of bytes from the end of one image to the beginning of the next.
    # Set this value to width × height × bytes-per-pixel × n to skip n images for each image read. So use 4194304
    # Dont forget to set Endian value and set to 64 bit
    roi_frames = (frames * combined_mask[np.newaxis, :, :])

    # todo: solve issue where rerunning this will overwrite any previous 'roi.npy'
    path = os.path.join(self.project.path, 'roi' + '.npy')
    np.save(path, roi_frames)
    self.project.files.append({
      'path': path,
      'type': 'video',
      'source_video': self.video_path,
      'manipulations': ['gsr']
    })

class MyPlugin:
  def __init__(self, project=None):
    self.name = 'Create ROIs'
    self.widget = Widget(project)
  
  def run(self):
    pass
