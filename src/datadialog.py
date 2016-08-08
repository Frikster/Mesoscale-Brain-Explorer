#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class DataDialog(QDialog):
  def __init__(self, parent=None):
    super(DataDialog, self).__init__(parent)

    self.setup_ui()

  def setup_ui(self):
    self.setWindowTitle('Data')
    self.setContentsMargins(4, 6, 5, 0)

    vbox = QVBoxLayout()

    self.data_list = QListView()
    self.data_list.setStyleSheet('QListView::item { height: 26px; }')
    self.data_list.setIconSize(QSize(18, 18))

    vbox.addWidget(self.data_list)
   
    #vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    self.setLayout(vbox)


