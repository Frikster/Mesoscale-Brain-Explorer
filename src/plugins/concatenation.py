#!/usr/bin/env python

import os
import numpy as np
import uuid

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util import fileloader
from util.qt import FileTable, FileTableModel, qtutil

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    if not project:
      return
    self.project = project
    self.setup_ui() 
    self.update_tables()

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.table1 = FileTable()
    self.table1.setSelectionMode(QAbstractItemView.MultiSelection)
    vbox.addWidget(self.table1)
    pb = QPushButton('C&oncatenate')
    pb.clicked.connect(self.concat_clicked)
    vbox.addWidget(pb)
    self.table2 = FileTable()
    vbox.addWidget(self.table2)
    self.setLayout(vbox)    

  def update_tables(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    self.table1.setModel(FileTableModel(videos))
    videos = [
      f for f in self.project.files
      if 'manipulations' in f and 'concat' in f['manipulations']
    ]
    self.table2.setModel(FileTableModel(videos))

  def concat_clicked(self):
    filenames = self.table1.selected_paths()
    if len(filenames) < 2:
      qtutil.warning('Select multiple files to concatenate.')
      return
    frames = [fileloader.load_file(f) for f in filenames]
    frames = np.concatenate(frames)
    path = os.path.join(self.project.path, str(uuid.uuid4()) + '.npy')
    np.save(path, frames)
    self.project.files.append({
      'path': path,
      'type': 'video',
      'manipulations': 'concat',
      'source': filenames
    })
    self.project.save()
    self.update_tables()

class MyPlugin:
  def __init__(self, project):
    self.name = 'Concat videos'
    self.widget = Widget(project)
  
  def run(self):
    pass
