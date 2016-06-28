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

    lt_right.addWidget(QLabel('Rotate by angle:'))
   
    sb = QSpinBox()
    sb.setMaximum(360)
    sb.setValue(180)
    lt_right.addWidget(sb)
  
    lt_right.addWidget(QPushButton('&Rotate'))

    lt_right.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
    pb_done = QPushButton('&Done')
    lt_right.addWidget(pb_done)

    right.setLayout(lt_right)

    self.pixmap = QPixmap('../data/flower2.jpg')
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
  def __init__(self):
    self.name = 'ImageRotator'
    self.widget = Widget()

  def run(self):
    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget())
    w.show()
    app.exec_()
    sys.exit()
