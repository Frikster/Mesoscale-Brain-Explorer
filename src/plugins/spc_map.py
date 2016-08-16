#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util import filter_jeff
from util.mygraphicsview import MyGraphicsView
from util.qt import MyListView

from util import fileloader

import matplotlib.pyplot as plt

class InfoWidget(QFrame):
  def __init__(self, text, parent=None):
    super(InfoWidget, self).__init__(parent)
    self.setup_ui(text)
  
  def setup_ui(self, text):
    hbox = QHBoxLayout()
    icon = QLabel()
    image = QImage('pics/info.png')
    icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
    hbox.addWidget(icon)
    self.label = QLabel(text)
    self.label.setWordWrap(True)
    hbox.addWidget(self.label)
    hbox.addStretch()
    self.setLayout(hbox)

    self.setFrameStyle(QFrame.Panel | QFrame.Raised)
    self.setLineWidth(2)
    self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class SPCMapDialog(QDialog):
  def __init__(self, project, spcmap, parent=None):
    super(SPCMapDialog, self).__init__(parent)
    self.project = project
    self.setup_ui()

    self.view.show(spcmap)

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    self.setLayout(vbox)

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

    self.view.vb.clicked.connect(self.vbc_clicked)

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project) 
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list = MyListView()
    vbox.addWidget(self.video_list)
    vbox.addStretch()
    vbox.addWidget(InfoWidget('Click on the image to generate SPC map.'))
    
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

  def vbc_clicked(self, x, y):
    if not self.video_path:
      return
    frame = fileloader.load_reference_frame(self.video_path)
    width, height = frame.shape

    x = int(x)
    y = int(height - y)

    frames = fileloader.load_file(self.video_path)

    progress = QProgressDialog('Generating correlation map...', 'Abort', 0, 100, self)
    progress.setWindowTitle('SPC Map')
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)
    spc_map = filter_jeff.correlation_map(y, x, frames, progress)

    # Make the location of the seed - self.image[y,x] - blatantly obvious
    spc_map[y+1, x+1] = 1
    spc_map[y+1, x] = 1
    spc_map[y, x+1] = 1
    spc_map[y-1, x-1] = 1
    spc_map[y-1, x] = 1
    spc_map[y, x-1] = 1
    spc_map[y+1, x-1] = 1
    spc_map[y-1, x+1] = 1

    # transorm self.image into rgb
    spc_map_color = plt.cm.jet(spc_map) * 255

    dialog = SPCMapDialog(self.project, spc_map_color, self)
    dialog.show()
    self.open_dialogs.append(dialog)

    self.showing_spc = True
    self.showing_std = False

class MyPlugin:
  def __init__(self, project):
    self.name = 'SPC map'
    self.widget = Widget(project)

  def run(self):
    pass
