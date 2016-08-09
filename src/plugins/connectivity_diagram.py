#!/usr/bin/env python

import os
import sys
import random

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class TableModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(TableModel, self).__init__(parent)

    self.setRowCount(20)
    self.setColumnCount(16)

  def data(self, index, role):
    if role == Qt.BackgroundRole:
      r, g, b = [random.randint(0, 255) for _ in range(3)]
      return QColor(r, g, b)
    elif role == Qt.DisplayRole:
      value = round(random.random(), 2)
      return str(value)
    elif role == Qt.TextAlignmentRole:
      return Qt.AlignCenter
    super(TableModel, self).data(index, role)

class TableView(QTableView):
   def __init__(self, parent=None):
     super(TableView, self).__init__(parent)

     self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
     self.verticalHeader().setResizeMode(QHeaderView.Stretch)
     self.horizontalHeader().hide()
     self.verticalHeader().hide()
     self.setModel(TableModel())

class MyPlugin:
  def __init__(self, project):
    self.name = 'Connectivity Diagram'
    self.widget = TableView()

  def run(self):
    pass

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(TableView())
  w.show()
  app.exec_()
  sys.exit()
