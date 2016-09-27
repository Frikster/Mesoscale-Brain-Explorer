#!/usr/bin/env python3

import os
import sys
import pandas as pd

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from plugins.util.qt import FileTable, FileTableModel

class DetailsModel(QAbstractTableModel):
  def __init__(self, obj, parent=None):
    super(DetailsModel, self).__init__(parent)
    self.obj = obj
    self.header = ['Field', 'Value']

  def rowCount(self, parent):
    return len(self.obj)

  def columnCount(self, parent):
    return len(self.header)

  def data(self, index, role):
    if role == Qt.DisplayRole:
      return list(self.obj.items())[index.row()][index.column()]
    return

  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole:
      return self.header[section]
    return

class DetailsDialog(QDialog):
  def __init__(self, fileinfo, parent=None):
    super(DetailsDialog, self).__init__(parent)
    self.fileinfo = fileinfo
    self.setup_ui()
    self.table.setModel(DetailsModel(fileinfo))

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.table = FileTable()
    vbox.addWidget(self.table)
    self.setLayout(vbox)
    self.resize(600, 400)

class RemoveDialog(QDialog):
  def __init__(self, fileinfo, parent=None):
    super(RemoveDialog, self).__init__(parent)
    self.fileinfo = fileinfo
    self.setup_ui()

  def setup_ui(self):
    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Removing file\n\'{}\''.format(self.fileinfo['path'])))
    vbox.addSpacing(20)
    hbox = QHBoxLayout()
    hbox.addStretch()
    pb = QPushButton('&Cancel')
    pb.clicked.connect(self.cancel_clicked)
    hbox.addWidget(pb)
    pb = QPushButton('&Detach from project')
    pb.clicked.connect(self.detach_clicked)
    hbox.addWidget(pb)
    pb = QPushButton('&Remove permanently')
    pb.clicked.connect(self.remove_clicked)
    hbox.addWidget(pb)
    vbox.addLayout(hbox)
    self.setLayout(vbox)
    self.setWindowTitle('File Removal')
    self.layout().setSizeConstraint(QLayout.SetFixedSize)

  def cancel_clicked(self):
    self.action = None
    self.close()

  def detach_clicked(self):
    self.action = 'detach'
    self.close()

  def remove_clicked(self):
    self.action = 'remove'
    self.close()

class DataDialog(QDialog):
  reload_plugins = pyqtSignal()
  
  def __init__(self, parent=None):
    super(DataDialog, self).__init__(parent)

    self.setup_ui()

  def setup_ui(self):
    self.setWindowTitle('Data')

    hbox = QHBoxLayout()
    self.table = FileTable()
    self.table.setSelectionMode(QAbstractItemView.SingleSelection)
    self.table.doubleClicked.connect(self.double_clicked)
    hbox.addWidget(self.table)

    vbox = QVBoxLayout()
    pb = QPushButton('&Details')
    pb.clicked.connect(self.details_clicked)
    vbox.addWidget(pb)
    pb = QPushButton('&Remove file')
    pb.clicked.connect(self.remove_clicked)
    vbox.addWidget(pb)
    vbox.addStretch()
    hbox.addLayout(vbox)
    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)
   
    self.setLayout(hbox)
    self.resize(800, 600)

  def update(self, project):
    self.project = project
    model = FileTableModel(self.project.files)
    self.table.setModel(model)

  def open_details(self, fileinfo):
    dialog = DetailsDialog(fileinfo, self)
    dialog.exec_()

  def double_clicked(self, index):
    fileinfo = self.table.model().get_entry(index)
    self.open_details(fileinfo)

  def details_clicked(self):
    rows = self.table.selectionModel().selectedRows()
    if not rows:
      return
    assert(len(rows) == 1)
    fileinfo = self.table.model().get_entry(rows[0])
    self.open_details(fileinfo)

  def remove_clicked(self):
    rows = self.table.selectionModel().selectedRows()
    if not rows:
      return
    assert(len(rows) == 1)
    fileinfo = self.table.model().get_entry(rows[0])
    dialog = RemoveDialog(fileinfo, self)
    dialog.exec_()
    if not dialog.action:
      return
    if dialog.action == 'remove':
      try:
        os.remove(fileinfo['path'])
      except:
        qtutil.critical('Could not delete file.')
        return
    # detach
    self.project.files[:] = [
      f for f in self.project.files
      if f['path'] != fileinfo['path']
    ]
    self.project.save()
    self.reload_plugins.emit()
    self.update(self.project)
