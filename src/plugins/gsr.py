#!/usr/bin/env python3

import os
import numpy as np

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import filter_jeff as fj
from .util import fileloader
from .util import project_functions as pfs

# on button click!

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return
    self.project = project

    # define ui components and global data
    self.view = MyGraphicsView(self.project)
    self.listview = QListView()
    self.left = QFrame()
    self.right = QFrame()

    self.setup_ui()
    self.selected_videos = []

    self.listview.setModel(QStandardItemModel())
    self.listview.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_video_changed)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.listview.model().appendRow(QStandardItem(f['name']))
    self.listview.setCurrentIndex(self.listview.model().index(0, 0))

  def selected_video_changed(self, selected, deselected):
    if not selected.indexes():
      return

    for index in deselected.indexes():
      vidpath = str(os.path.join(self.project.path,
                                 index.data(Qt.DisplayRole))
                    + '.npy')
      self.selected_videos = [x for x in self.selected_videos if x != vidpath]
    for index in selected.indexes():
      vidpath = str(os.path.join(self.project.path,
                                 index.data(Qt.DisplayRole))
                    + '.npy')
    if vidpath not in self.selected_videos and vidpath != 'None':
      self.selected_videos = self.selected_videos + [vidpath]

    self.shown_video_path = str(os.path.join(self.project.path,
                                             selected.indexes()[0].data(Qt.DisplayRole))
                                + '.npy')
    frame = fileloader.load_reference_frame(self.shown_video_path)
    self.view.show(frame)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.listview.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.listview)
    hhbox = QHBoxLayout()
    butt_gsr = QPushButton('Global Signal Regression')
    hhbox.addWidget(butt_gsr)
    vbox.addLayout(hhbox)
    vbox.addStretch()
    butt_gsr.clicked.connect(self.gsr_clicked)
    self.right.setLayout(vbox)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)

  def gsr_clicked(self):
      progress = QProgressDialog('Computing gsr for selection', 'Abort', 0, 100, self)
      progress.setAutoClose(True)
      progress.setMinimumDuration(0)

      def callback(x):
          progress.setValue(x * 100)
          QApplication.processEvents()

      self.gsr(callback)

  def gsr(self, progress_callback):
    for i, video_path in enumerate(self.selected_videos):
        progress_callback(i / len(self.selected_videos))
        frames = fileloader.load_file(video_path)

        width = frames.shape[1]
        height = frames.shape[2]
        frames = fj.gsr(frames, width, height)

        pfs.save_project(video_path, self.project, frames, 'gsr', 'video')
    progress_callback(1)

class MyPlugin:
  def __init__(self, project):
    self.name = 'GSR'
    self.widget = Widget(project)
  
  def run(self):
    pass
