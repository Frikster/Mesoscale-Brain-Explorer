#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
    def compute_stdev_map(self):
        fileName = str(self.sidePanel.imageFileList.currentItem().text())
        width = int(self.sidePanel.vidWidthValue.text())
        height = int(self.sidePanel.vidHeightValue.text())
        dtype_string = str(self.sidePanel.dtypeValue.text())
        self.st_map = fj.standard_deviation(fj.get_frames(fileName, width, height, dtype_string))

        self.st_map_colour = plt.cm.jet((self.st_map)) * 255

        self.preprocess_for_showImage(self.st_map_colour)
        self.showing_spc = False
        self.showing_std = True
        self.view.vb.showImage(self.arr)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Standard deviation map'
    self.widget = Widget()

  def run(self):
    pass
