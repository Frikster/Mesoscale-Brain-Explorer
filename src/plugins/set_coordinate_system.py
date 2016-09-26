#!/usr/bin/env python

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project

    self.setup_ui()

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project)
    self.view.vb.clicked.connect(self.vbc_clicked)
    self.view.vb.setCursor(Qt.CrossCursor)
    hbox.addWidget(self.view)
    
    vbox = QVBoxLayout()
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
    vbox.addLayout(hhbox)
    vbox.addStretch()
    
    hbox.addLayout(vbox)
    self.setLayout(hbox)

    self.setEnabled(False)

  def set_origin_label(self):
    x, y = self.project['origin']
    self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))

  def update(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    if not videos:
      self.setEnabled(False)
      return
    frame = fileloader.load_reference_frame(videos[0]['path'])
    self.view.show(frame)
    self.set_origin_label()
    self.setEnabled(True)

  def save(self):
    self.project.save()

  def set_mmpixel(self, value):
    self.project['mmpixel'] = value
    self.view.update()
    self.save()

  def vbc_clicked(self, x, y):
    """Set origin to mouse pos"""
    self.project['origin'] = (x, y)
    self.set_origin_label()
    self.view.update()
    self.save()

class MyPlugin:
  def __init__(self, project):
    self.name = 'Set coordinate system'
    self.widget = Widget(project)

  def run(self):
    self.widget.update()
