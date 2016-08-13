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

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

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

  def setup_ui(self):
    hbox = QHBoxLayout()
  
    self.view = MyGraphicsView(self.project)
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.listview)

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
    hbox2 = QHBoxLayout()
    hbox2.addWidget(QLabel('ROI name:'))
    self.edit = QLineEdit()
    hbox2.addWidget(self.edit)     
    vbox2.addLayout(hbox2)
    pb = QPushButton('Save')
    pb.clicked.connect(self.save_roi)
    vbox2.addWidget(pb)
    w = QWidget()
    w.setLayout(vbox2)
    #w.setEnabled(False)
    vbox.addWidget(w)

    vbox.addWidget(qtutil.separator())
    vbox.addWidget(QLabel('ROIs'))
    self.roi_list = QListView()
    vbox.addWidget(self.roi_list)

    hbox.addLayout(vbox)
    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)
    self.setLayout(hbox)

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)

  def create_roi(self):
    self.view.vb.addPolyRoiRequest()
    
  def save_roi(self):
    name = str(self.edit.text())
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
      self.project.save()

  def crop_ROI(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    # todo: make videos selectable.
    fileName = videos[0]['path']

    frames = fileloader.load_file(fileName)
    width = frames.shape[1]
    height = frames.shape[2]

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
