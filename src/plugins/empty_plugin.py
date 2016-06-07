#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  def __init__(self, parent=None):
    super(Widget, self).__init__(parent)
 
    lt = QVBoxLayout()
    lt.addWidget(QLabel('<i>No plugin running.</i>'))
    lt.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
    self.setLayout(lt)

class MyPlugin:
  name = 'Plugin'
  widget = Widget()

  def run(self):
    pass
