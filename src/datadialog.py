#!/usr/bin/env python

import os
import sys
import pandas as pd

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from qtutil import PandasModel

class TableView(QTableView):
  def __init__(self, parent=None):
    super(TableView, self).__init__(parent)

    self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    self.verticalHeader().hide()

class DataDialog(QDialog):
  def __init__(self, parent=None):
    super(DataDialog, self).__init__(parent)

    self.setup_ui()

  def setup_ui(self):
    self.setWindowTitle('Data')

    vbox = QVBoxLayout()
    self.view = TableView()
    vbox.addWidget(self.view)
   
    self.setLayout(vbox)
    self.resize(600, 400)

  def update(self, project):
    df = pd.DataFrame(project.files)
    model = PandasModel(df)
    self.view.setModel(model)
