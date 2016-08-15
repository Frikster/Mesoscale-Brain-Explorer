#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView

class TableView(QTableView):
  def __init__(self, parent=None):
    super(TableView, self).__init__(parent)

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    if not project:
      return
    self.project = project
    self.setup_ui()

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    hbox = QHBoxLayout()
    slider = QSlider(Qt.Horizontal)
    hbox.addWidget(slider)
    self.label_frame = QLabel('- / -')
    hbox.addWidget(self.label_frame)
    vbox.addLayout(hbox)
    self.setLayout(vbox)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Play video'
    self.widget = Widget(project)
  
  def run(self):
    pass

