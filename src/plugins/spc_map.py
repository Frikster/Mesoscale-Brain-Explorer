#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util import filter_jeff
from util.mygraphicsview import MyGraphicsView
from util.qt import MyListView

from util import fileloader

import matplotlib.pyplot as plt

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    if not project:
      return
    self.project = project
    self.setup_ui()

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
    vbox.addStretch()
    
    hbox.addLayout(vbox)    
    self.setLayout(hbox)

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)
  
  def compute_spc_map(self, x, y):
    if self.sidePanel.SPC_map_mode_value.isChecked() == False:
      return

    fileName = str(self.sidePanel.imageFileList.currentItem().text())
    width = int(self.sidePanel.vidWidthValue.text())
    height = int(self.sidePanel.vidHeightValue.text())
    dtype_string = str(self.sidePanel.dtypeValue.text())
    self.spc_map = fj.get_correlation_map(y, x, fj.get_frames(fileName, width, height, dtype_string))

    # Make the location of the seed - self.image[y,x] - blatantly obvious
    self.spc_map[y+1, x+1] = 1.0
    self.spc_map[y+1, x] = 1.0
    self.spc_map[y, x+1] = 1.0
    self.spc_map[y-1, x-1] = 1.0
    self.spc_map[y-1, x] = 1.0
    self.spc_map[y, x-1] = 1.0
    self.spc_map[y+1, x-1] = 1.0
    self.spc_map[y-1, x+1] = 1.0

    # transorm self.image into rgb
    self.spc_map_colour = plt.cm.jet((self.spc_map))*255

    self.preprocess_for_showImage(self.spc_map_colour)
    self.showing_spc = True
    self.showing_std = False
    self.view.vb.showImage(self.arr)

class MyPlugin:
  def __init__(self, project):
    self.name = 'SPC map'
    self.widget = Widget(project)

  def run(self):
    pass
