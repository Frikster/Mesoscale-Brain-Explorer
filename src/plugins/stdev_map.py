#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util import filter_jeff
from util.mygraphicsview import MyGraphicsView
from util.qt import MyListView, MyProgressDialog
from util.gradient import GradientLegend

from util import fileloader

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math

def calc_stddev(video_path, progress):
  progress.setValue(0)
  frames = fileloader.load_file(video_path)
  #stddev = filter_jeff.standard_deviation(frames, progress)
  stddev = filter_jeff.standard_deviation(frames)
  progress.setValue(100)

  return stddev

def prepare_image(stddev, max_stdev):
  stddev[np.isnan(stddev)] = 0.0
  gradient_range = matplotlib.colors.Normalize(0.0, max_stdev)
  image = matplotlib.cm.ScalarMappable(
    gradient_range, 'jet').to_rgba(stddev, bytes=True)
  image = image.swapaxes(0, 1)
  if image.ndim == 2:
    image = image[:, ::-1]
  elif image.ndim == 3:
    image = image[:, ::-1, :]
  return image

class StdDevDialog(QDialog):
  def __init__(self, project, video_path, stddevmap, max_stdev, parent=None):
    super(StdDevDialog, self).__init__(parent)
    self.project = project
    self.video_path = video_path
    self.stddev = stddevmap
    self.max_stdev = max_stdev
    self.setup_ui()
    l = GradientLegend(0.0, max_stdev)
    l.setParentItem(self.view.vb)
    self.setWindowTitle('Standard Deviation Map')

    self.view.show(prepare_image(stddevmap, max_stdev))
    self.view.vb.hovering.connect(self.vbc_hovering)

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.the_label = QLabel()
    vbox.addWidget(self.the_label)
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    self.setLayout(vbox)

  def vbc_hovering(self, x, y):
    x_origin, y_origin = self.project['origin']
    mmpixel = self.project['mmpixel']
    x = x / mmpixel
    y = y / mmpixel
    stddev = self.stddev.swapaxes(0, 1)
    stddev = stddev[:, ::-1]
    try:
      value = str(stddev[int(x)+int(x_origin), int(y)+int(y_origin)])
    except:
      value = '-'
    self.the_label.setText('Standard deviation at crosshair: {}'.format(value))

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    if not project:
      return
    self.project = project
    self.setup_ui()

    self.video_path = None
    self.open_dialogs = []

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.video_list.model().appendRow(QStandardItem(f['path']))
    self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project) 
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list = MyListView()
    vbox.addWidget(self.video_list)
    self.max_stdev = QDoubleSpinBox(decimals=4)
    self.max_stdev.setMinimum(0.0000)
    self.max_stdev.setValue(1.0000)
    vbox.addWidget(self.max_stdev)
    pb = QPushButton('Generate Std. Dev. Map')
    pb.clicked.connect(self.go)
    vbox.addWidget(pb)
    
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

  def go(self):
    if not self.video_path:
      return

    progress = MyProgressDialog('Standard Deviation Map', 'Generating map...', self)
    stddev = calc_stddev(self.video_path, progress)
    dialog = StdDevDialog(self.project, self.video_path, stddev, self.max_stdev.value(), self)
    dialog.show()
    self.open_dialogs.append(dialog)


class MyPlugin:
  def __init__(self, project):
    self.name = 'Standard deviation map'
    self.widget = Widget(project)

  def run(self):
    pass
