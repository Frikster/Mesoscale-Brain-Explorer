#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import qtutil
from qtutil import PandasModel

class JSObjectModel(QAbstractTableModel):
  def __init__(self, data, parent=None):
    super(JSObjectModel, self).__init__(parent)
    self._data = data

    cols = []
    for obj in data:
      cols.extend(obj.keys())
    self.cols = list(set(cols))

  def rowCount(self, parent):
    return len(self._data)

  def columnCount(self, parent): 
    return len(self.cols)

  def data(self, index, role):
    if role == Qt.DisplayRole:
      col = self.cols[index.column()]
      obj = self._data[index.row()]
      return col in obj and obj[col] or ''
    return QVariant()

  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole and orientation == Qt.Horizontal:
      return self.cols[section]
    return QVariant()

  def retrieve(self, row, key=None):
    obj = self._data[row]
    if key:
      return obj[key]
    else:
      return obj

class FileTableModel(JSObjectModel):
  def __init__(self, data, parent=None):
    super(FileTableModel, self).__init__(data, parent)
  
  def get_path(self, index):
    return self.retrieve(index.row(), 'path')
  
  def get_entry(self, index):
    return self.retrieve(index.row())

class FileTable(QTableView):
  def __init__(self, project=None, parent=None):
    super(FileTable, self).__init__(parent)

    self.verticalHeader().hide()
    self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    #self.horizontalHeader().setStretchLastSection(True)
    self.setSelectionBehavior(QAbstractItemView.SelectRows) 

    if project:
      self.setModel(FileTableModel(project))

  def selected_paths(self):
    selection = self.selectionModel().selectedRows()
    filenames = [self.model().get_path(index) for index in selection]
    return filenames

class MyListView(QListView):
  def __init__(self, parent=None):
    super(MyListView, self).__init__(parent)
    self.setStyleSheet('QListView::item { height: 26px; }')

class MyProgressDialog(QProgressDialog):
  def __init__(self, title, desc, parent=None):
    super(MyProgressDialog, self).__init__(desc, QString(), 0, 100, parent)
    self.setWindowTitle(title)
    self.setAutoClose(True)
    self.setMinimumDuration(0)

class InfoWidget(QFrame):
  def __init__(self, text, parent=None):
    super(InfoWidget, self).__init__(parent)
    self.setup_ui(text)
  
  def setup_ui(self, text):
    hbox = QHBoxLayout()
    icon = QLabel()
    image = QImage('pics/info.png')
    icon.setPixmap(QPixmap.fromImage(image.scaled(30, 30)))
    hbox.addWidget(icon)
    self.label = QLabel(text)
    self.label.setWordWrap(True)
    hbox.addWidget(self.label)
    #hbox.addStretch()
    hbox.setStretch(0, 0)
    hbox.setStretch(1, 1)
    self.setLayout(hbox)

    self.setFrameStyle(QFrame.Panel | QFrame.Raised)
    self.setLineWidth(2)
    self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')
