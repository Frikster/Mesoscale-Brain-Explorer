#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import qtutil
from qtutil import PandasModel

import pandas as pd

class FileTableModel(PandasModel):
  def __init__(self, data, parent=None):
    super(FileTableModel, self).__init__(pd.DataFrame(data), parent)
  
  def get_path(self, index):
    return self._data['path'][index.row()]

class FileTable(QTableView):
  def __init__(self, parent=None):
    super(FileTable, self).__init__(parent)

    self.verticalHeader().hide()
    self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    self.setSelectionBehavior(QAbstractItemView.SelectRows) 

  def selected_paths(self):
    selection = self.selectionModel().selectedRows()
    filenames = [self.model().get_path(index) for index in selection]
    return filenames
    
