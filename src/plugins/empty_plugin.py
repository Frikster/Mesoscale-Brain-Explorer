#!/usr/bin/env python3

import os
import sys
from .chebyshev_filter import *

from PyQt4.QtGui import *
from .util import project_functions as pfs
from PyQt4.QtCore import *
from .videoplayer import PlayerDialog

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
 
    if not project:
      return
    self.project = project

    # define ui components and global data
    self.view = MyGraphicsView(self.project)
    self.video_list = QListView()
    self.left = QFrame()
    self.right = QFrame()
    self.open_dialogs = []

    self.setup_ui()
    self.selected_videos = []

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.video_list.doubleClicked.connect(self.video_triggered)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.video_list.model().appendRow(QStandardItem(f['name']))
    self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

  def video_triggered(self, index):
    filename = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
    dialog = PlayerDialog(self.project, filename, self)
    dialog.show()
    self.open_dialogs.append(dialog)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    list_of_manips = pfs.get_list_of_project_manips(self.project)
    self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    vbox.addWidget(self.toolbutton)
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    vbox.addWidget(self.video_list)
    hhbox = QHBoxLayout()
    custom_butt = QPushButton('Perform Custom Analysis')
    hhbox.addWidget(custom_butt)
    vbox.addLayout(hhbox)
    vbox.addStretch()
    custom_butt.clicked.connect(self.custom_butt_clicked)
    self.right.setLayout(vbox)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)


  def refresh_video_list_via_combo_box(self, trigger_item=None):
    pfs.refresh_video_list_via_combo_box(self, trigger_item)

  def selected_video_changed(self, selected, deselected):
    pfs.selected_video_changed_multi(self, selected, deselected)

  def custom_butt_clicked(self):
      print('Do custom stuff. Coding required.')

class MyPlugin:
  def __init__(self, project):
    self.name = 'Empty Plugin'
    self.widget = Widget(project)

  def run(self):
    pass

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget(None))
  w.show()
  app.exec_()
  sys.exit()
