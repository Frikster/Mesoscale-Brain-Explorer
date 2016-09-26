#!/usr/bin/env python

import os
import sys
from .chebyshev_filter import *

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
  def __init__(self, project):
    self.name = 'Empty Plugin'
    self.widget = Widget()

  def run(self):
    pass

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget())
  w.show()
  app.exec_()
  sys.exit()
