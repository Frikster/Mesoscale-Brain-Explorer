#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  def __init__(self, parent=None):
    super(Widget, self).__init__(parent)

    vbox = QVBoxLayout()
 
    pb_done = QPushButton('&Done')
    vbox.addWidget(pb_done)
    #pb_done.clicked.connect(self.leave)

    self.setLayout(vbox)


class MyPlugin:
  name = 'ImageViewer'
  widget = Widget()

  def run(self):
    pass

