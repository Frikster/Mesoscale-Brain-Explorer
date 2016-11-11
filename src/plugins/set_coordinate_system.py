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

    # define ui components and global data
    self.view = MyGraphicsView(self.project)
    self.video_list = QListView()
    self.origin_label = QLabel('Origin:')
    self.left = QFrame()
    self.right = QFrame()
    self.combo_box = QComboBox(self)
    self.setup_ui()

    self.selected_videos = []
    self.shown_video_path = None
    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.video_list.doubleClicked.connect(self.video_triggered)
    pfs.refresh_video_list(self.project, self.video_list)

    # for f in project.files:
    #   if f['type'] != 'video':
    #     continue
    #   self.listview.model().appendRow(QStandardItem(f['name']))
    # self.listview.setCurrentIndex(self.listview.model().index(0, 0))

  def video_triggered(self, index):
      pfs.video_triggered(self, index)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    self.view.vb.clicked.connect(self.vbc_clicked)
    vbox = QVBoxLayout()
    list_of_manips = pfs.get_list_of_project_manips(self.project)
    self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    vbox.addWidget(self.toolbutton)
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    vbox.addWidget(self.video_list)
    vbox.addWidget(self.origin_label)
    pb = QPushButton('&Average origin from selected files\' origins')
    pb.clicked.connect(self.avg_origin)
    vbox.addWidget(pb)
    vbox.addWidget(QLabel('pixel width x'))
    comboBox = self.combo_box
    comboBox.addItem("microns")
    comboBox.addItem("mm")
    vbox.addWidget(comboBox)
    comboBox.activated[str].connect(self.set_pixel_width_magnitude)
    hhbox = QHBoxLayout()
    hhbox.addWidget(QLabel('x/pixel:'))
    sb = QSpinBox()
    sb.setRange(1, 1000)
    sb.setSingleStep(1)
    sb.setValue(self.project['unit_per_pixel'])
    sb.valueChanged[int].connect(self.set_unit_per_pixel)
    hhbox.addWidget(sb)
    vbox.addLayout(hhbox)
    vbox.addStretch()
    self.right.setLayout(vbox)
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)
    self.setEnabled(False)

  def refresh_video_list_via_combo_box(self, trigger_item=None):
      pfs.refresh_video_list_via_combo_box(self, trigger_item)

  def set_pixel_width_magnitude(self, mag):
      self.view.unit_per_pixel = mag
      self.view.update()
      assert(mag == 'microns' or mag == 'mm')
      if mag == 'microns':
          print('microns')
      else:
          print('mm')

  def selected_video_changed(self, selected, deselected):
      if not self.video_list.selectedIndexes():
          return
      self.selected_videos = []
      for index in self.video_list.selectedIndexes():
          vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
          if vidpath not in self.selected_videos and vidpath != 'None':
              self.selected_videos = self.selected_videos + [vidpath]
              self.shown_video_path = str(os.path.join(self.project.path,
                                                       self.video_list.currentIndex().data(Qt.DisplayRole))
                                            + '.npy')

      # if not selected.indexes():
      #     return
      # for index in deselected.indexes():
      #     vidpath = str(os.path.join(self.project.path,
      #                                index.data(Qt.DisplayRole))
      #                   + '.npy')
      #     self.selected_videos = [x for x in self.selected_videos if x != vidpath]
      # for index in selected.indexes():
      #     vidpath = str(os.path.join(self.project.path,
      #                                index.data(Qt.DisplayRole))
      #                   + '.npy')
      # if vidpath not in self.selected_videos and vidpath != 'None':
      #     self.selected_videos = self.selected_videos + [vidpath]

      project_file = pfs.get_project_file_from_key_item(self.project,
                                                        'path',
                                                        self.shown_video_path)
      # Check if origin exists
      try:
        (x, y) = ast.literal_eval(project_file['origin'])
      except KeyError:
        self.origin_label.setText('Origin:')
      else:
        (x, y) = ast.literal_eval(project_file['origin'])
        self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))
      frame = fileloader.load_reference_frame(self.shown_video_path)
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
    # self.set_origin_label()
    self.setEnabled(True)

  def save(self):
    self.project.save()

  def set_unit_per_pixel(self, value):
    self.view.unit_per_pixel = self.combo_box.currentText()
    self.project['unit_per_pixel'] = value
    self.view.update()
    self.save()

  def vbc_clicked(self, x, y):
    pfs.change_origin(self.project, self.shown_video_path, (x, y))
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
