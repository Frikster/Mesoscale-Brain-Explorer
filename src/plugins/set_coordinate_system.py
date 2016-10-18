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
import ast

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

    self.view.vb.clicked.connect(self.vbc_clicked)

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

    pb = QPushButton('&Average origin from selected files\' origins')
    pb.clicked.connect(self.avg_origin)
    vbox.addWidget(pb)

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

      project_file = pfs.get_project_file_from_key_item(self.project,
                                                        'path',
                                                        self.selected_videos[0])
      # Check if origin exists
      try:
        (x, y) = ast.literal_eval(project_file['origin'])
      except KeyError:
        self.origin_label.setText('Origin:')
      else:
        (x , y) = ast.literal_eval(project_file['origin'])
        self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))
      # shown_video_path = str(os.path.join(self.project.path,
      #                                          selected.indexes()[0].data(Qt.DisplayRole))
      #                             + '.npy')
      frame = fileloader.load_reference_frame(self.selected_videos[0])
      self.view.show(frame)

  def avg_origin(self):
    """Set origin to averaged over all selected files' origins"""
    if not self.selected_videos:
        return

    relevant_files = []
    for selected_path in self.selected_videos:
        relevant_files = relevant_files + \
                         [pfs.get_project_file_from_key_item(self.project, 'path', selected_path)]

    # check to see if all selected files have an origin
    try:
        [file['origin'] for file in relevant_files]
    except KeyError:
        qtutil.warning('One or more of your selected files have no origin. These will be ignored.')

    #collect dict items that have origins
    orgs = [file.get("origin") for file in relevant_files]
    orgs = [x for x in orgs if x is not None]
    orgs = [ast.literal_eval(org) for org in orgs]

    # collect and avg origins
    (x_tot, y_tot) = (0, 0)
    for (x, y) in orgs:
      (x_tot, y_tot) = (x_tot+x, y_tot+y)
    no_orgs = len(relevant_files)
    (x_avg, y_avg) = (x_tot / no_orgs, y_tot / no_orgs)
    self.project['origin'] = (x_avg, y_avg)
    self.view.update()
    self.save()

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
