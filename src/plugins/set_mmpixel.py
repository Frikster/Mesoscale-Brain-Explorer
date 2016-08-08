#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  def __init__(self):
    sb = QDoubleSpinBox()
    sb.setRange(0.001, 9999.0)
    sb.setSingleStep(0.01)
    sb.setValue(0.04)
    sb.valueChanged[float].connect(self.update_mmpixel)
  def update_mmpixel(self, mmpixel):
    self.mmpixel = mmpixel
    width = int(self.sidePanel.vidWidthValue.text())
    height = int(self.sidePanel.vidHeightValue.text())
    self.img_shape = (width, height)
    self.update_rect()

class MyPlugin:
  def __init__(self):
    self.name = 'Set mm per pixel'
    self.widget = QWidget()
  
  def run(self):
    pass
