#!/usr/bin/env python3

import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

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
