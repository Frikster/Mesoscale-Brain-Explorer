#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pandas as pd
import time

import util.displacement_jeff as djeff
from util.qt import PandasModel, FileTableModel

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
  
    self.update_tables()

    for table in self.table1, self.table2:
      table.verticalHeader().hide()
      table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
      table.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.table1.setSelectionMode(QAbstractItemView.MultiSelection)
  
  def setup_ui(self):
    vbox = QVBoxLayout()
    self.table1 = TableView()
    vbox.addWidget(self.table1)
    pb = QPushButton('&Align')
    pb.clicked.connect(self.align_clicked)
    vbox.addWidget(pb)
    self.table2 = TableView()
    vbox.addWidget(self.table2)
    self.setLayout(vbox)

  def update_tables(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    self.table1.setModel(FileTableModel(videos))

    videos = [
      f for f in self.project.files
      if 'manipulations' in f and 'align' in f['manipulations']
    ]
    self.table2.setModel(PandasModel(pd.DataFrame(videos)))

  def align_clicked(self):
    selection = self.table1.selectionModel().selectedRows()
    filenames = [self.table1.model().get_path(index) for index in selection]
    if not filenames:
      return

    progress = QProgressDialog('Aligning file...', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)

    def callback(x):
      progress.setValue(x * 100)
      QApplication.processEvents()
      #time.sleep(0.01)

    filenames = djeff.align_videos(filenames, callback)

    for filename in filenames:
      if filename in [f['path'] for f in self.project.files]:
        continue
      f = {
        'path': filename,
        'type': 'video',
        'manipulations': 'align'
      }
      self.project.files.append(f)
    self.project.save()
    self.update_tables()

class MyPlugin:
  def __init__(self, project):
    self.name = 'Align images'
    self.widget = Widget(project)
  
  def run(self):
    pass
