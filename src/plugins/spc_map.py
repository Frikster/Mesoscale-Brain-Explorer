#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
    def compute_spc_map(self, x, y):
        if self.sidePanel.SPC_map_mode_value.isChecked() == False:
            return

        fileName = str(self.sidePanel.imageFileList.currentItem().text())
        width = int(self.sidePanel.vidWidthValue.text())
        height = int(self.sidePanel.vidHeightValue.text())
        dtype_string = str(self.sidePanel.dtypeValue.text())
        self.spc_map = fj.get_correlation_map(y, x, fj.get_frames(fileName, width, height, dtype_string))

        # Make the location of the seed - self.image[y,x] - blatantly obvious
        self.spc_map[y+1, x+1] = 1.0
        self.spc_map[y+1, x] = 1.0
        self.spc_map[y, x+1] = 1.0
        self.spc_map[y-1, x-1] = 1.0
        self.spc_map[y-1, x] = 1.0
        self.spc_map[y, x-1] = 1.0
        self.spc_map[y+1, x-1] = 1.0
        self.spc_map[y-1, x+1] = 1.0

        # transorm self.image into rgb
        self.spc_map_colour = plt.cm.jet((self.spc_map))*255

        self.preprocess_for_showImage(self.spc_map_colour)
        self.showing_spc = True
        self.showing_std = False
        self.view.vb.showImage(self.arr)

class MyPlugin:
  def __init__(self, project):
    self.name = 'SPC map'
    self.widget = Widget()

  def run(self):
    pass
