#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  def __init__(self, parent=None):
    super(Widget, self).__init__(parent)

    hbox = QHBoxLayout()
    left = QVBoxLayout()
    right = QFrame()
    right.setFrameShadow(QFrame.Raised)
    right.setFrameShape(QFrame.Panel)
    right.setContentsMargins(10,0,1,0)
    right.setMinimumWidth(200)

    lt_right = QVBoxLayout()
    lt_right.setContentsMargins(8,8,8,8)

    lt_right.addWidget(QLabel('Crop to region:'))
  
    grid = QGridLayout()
    grid.addWidget(QLabel('x1:'), 0, 0)
    grid.addWidget(QSpinBox(), 0, 1)
    grid.addWidget(QLabel('y1:'), 1, 0)
    grid.addWidget(QSpinBox(), 1, 1)
    grid.addWidget(QLabel('x2:'), 2, 0)
    grid.addWidget(QSpinBox(), 2, 1)
    grid.addWidget(QLabel('y2:'), 3, 0)
    grid.addWidget(QSpinBox(), 3, 1)

    lt_right.addLayout(grid)

    lt_right.addWidget(QPushButton('&Crop'))

    lt_right.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
    pb_done = QPushButton('&Done')
    lt_right.addWidget(pb_done)

    right.setLayout(lt_right)

    self.pixmap = QPixmap('../data/flower.jpg')
    self.pic = QLabel()
    self.pic.setStyleSheet('background-color: black')
    self.pic.setPixmap(self.pixmap)
    left.addWidget(self.pic)   

    hbox.addLayout(left)
    hbox.addWidget(right)

    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)

    self.setLayout(hbox)


class MyPlugin:
  name = 'ImageCropper'
  widget = Widget()

  def run(self):
    pass


