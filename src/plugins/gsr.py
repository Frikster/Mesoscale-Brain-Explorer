#!/usr/bin/env python

import os
import numpy as np

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util import filter_jeff as fj
from util import fileloader

# on button click!

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

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project)
    self.view.vb.setCursor(Qt.CrossCursor)
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.listview)

    hhbox = QHBoxLayout()
    butt_gsr = QPushButton('Global Signal Regression')
    hhbox.addWidget(butt_gsr)
    vbox.addLayout(hhbox)
    vbox.addStretch()
    butt_gsr.clicked.connect(self.gsr)

    hbox.addLayout(vbox)
    self.setLayout(hbox)

  def gsr(self):
    frames = fileloader.load_file(self.video_path)

    width = frames.shape[1]
    height = frames.shape[2]
    frames = fj.gsr(frames, width, height)

    #todo: solve issue where rerunning this will overwrite any previous 'gsr.npy'
    path = os.path.join(self.project.path, 'gsr' + '.npy')
    np.save(path, frames)
    self.project.files.append({
      'path': path,
      'type': 'video',
      'source_video': self.video_path,
      'manipulations': ['gsr']
    })
    self.project.save()

    #np.save(os.path.expanduser('/Downloads/')+"gsr", frames)
    #frames.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"gsr.raw")
    #print("gsr saved to "+os.path.expanduser('/Downloads/')+"gsr")

class MyPlugin:
  def __init__(self, project):
    self.name = 'GSR'
    self.widget = Widget(project)
  
  def run(self):
    pass
