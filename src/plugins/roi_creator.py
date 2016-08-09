# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util.fileloader import load_file

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
  
    self.graphics_view = MyGraphicsView()
    hbox.addWidget(self.graphics_view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.listview)
    pb = QPushButton('Create poly ROI')
    pb.clicked.connect(self.create_roi)
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
    frames = load_file(self.video_path)
    if frames is None:
      qtutil.critical('Video file could not be loaded.')
      return
    frame = frames[min(400, len(frames))]
    frame = frame.swapaxes(0,1)
    if   frame.ndim==2: frame = frame[:,::-1]
    elif frame.ndim==3: frame = frame[:,::-1,:]
    self.graphics_view.vb.showImage(frame)

  def create_roi(self):
    self.graphics_view.vb.addPolyRoiRequest()
    
  def save_roi(self):
    name = str(self.edit.text())
    if not name:
      qtutil.critical('Choose a name.')
    elif name in [f['name'] for f in self.project.files if 'name' in f]:
      qtutil.critical('ROI name taken.')
    else:
      path = os.path.join(self.project.path, name + '.roi')
      self.graphics_view.vb.saveROI(path)
      #TODO check if saved
      self.project.files.append({
        'path': path,
        'type': 'roi',
        'source_video': self.video_path,
        'name': name
      })
      self.project.save()

class MyPlugin:
  def __init__(self, project=None):
    self.name = 'Create ROIs'
    self.widget = Widget(project)
  
  def run(self):
    pass
