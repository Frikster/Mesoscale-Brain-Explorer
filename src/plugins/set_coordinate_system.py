#!/usr/bin/env python3

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader
from .util import project_functions as pfs

import qtutil

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project

    self.setup_ui()

    self.selected_videos = []
    self.listview.setModel(QStandardItemModel())
    self.listview.selectionModel().selectionChanged[QItemSelection,
      QItemSelection].connect(self.selected_video_changed)

    pfs.refresh_video_list(self.project, self.listview)
    # for f in project.files:
    #   if f['type'] != 'video':
    #     continue
    #   self.listview.model().appendRow(QStandardItem(f['name']))
    # self.listview.setCurrentIndex(self.listview.model().index(0, 0))

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project)
    self.view.vb.setCursor(Qt.CrossCursor)
    hbox.addWidget(self.view)
    
    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.listview = QListView()
    self.listview.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.listview)

    self.origin_label = QLabel('Origin:')
    vbox.addWidget(self.origin_label)

    hhbox = QHBoxLayout()
    hhbox.addWidget(QLabel('mm/pixel:'))
    sb = QDoubleSpinBox()
    sb.setRange(0.001, 9999.0)
    sb.setSingleStep(0.01)
    sb.setValue(self.project['mmpixel'])
    sb.valueChanged[float].connect(self.set_mmpixel)
    hhbox.addWidget(sb)

    # pb = QPushButton('&Averaged origin from selection')
    # pb.clicked.connect(self.avg_origin)
    # vbox.addWidget(pb)

    vbox.addLayout(hhbox)
    vbox.addStretch()
    
    hbox.addLayout(vbox)
    self.setLayout(hbox)

    self.setEnabled(False)

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

      # shown_video_path = str(os.path.join(self.project.path,
      #                                          selected.indexes()[0].data(Qt.DisplayRole))
      #                             + '.npy')
      frame = fileloader.load_reference_frame(self.selected_videos[0])
      self.view.show(frame)

  # def avg_origin(self):
  #     qutil.info('Please choose the origin for each file')
  #     self.view.vb.clicked.connect(self.vbc_clicked)
  #     """Set origin to mouse pos averaged over all clicks"""
  #     for selected_path in self.selected_videos:
  #         frame = fileloader.load_reference_frame(selected_path)
  #         self.view.show(frame)

  def set_origin_label(self, x, y):
    #x, y = self.project['origin']
    self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))

  def update(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    if not videos:
      self.setEnabled(False)
      return
    frame = fileloader.load_reference_frame(videos[0]['path'])
    self.view.show(frame)
    #self.set_origin_label()
    self.setEnabled(True)

  def save(self):
    self.project.save()

  def set_mmpixel(self, value):
    self.project['mmpixel'] = value
    self.view.update()
    self.save()

  def vbc_clicked(self, x, y):
    pfs.change_origin(self.project, self.selected_videos[0], (x, y))
    self.set_origin_label(x, y)
    self.view.update()

    #self.project['origin'] = (x, y)
    #self.set_origin_label()
    #self.view.update()
    #self.save()

class MyPlugin:
  def __init__(self, project):
    self.name = 'Set coordinate system'
    self.widget = Widget(project)

  def run(self):
    self.widget.update()
