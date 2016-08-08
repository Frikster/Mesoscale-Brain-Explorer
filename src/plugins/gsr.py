#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

# on button click!

def gsr(self):
  fileName = str(self.sidePanel.imageFileList.currentItem().text())
  width = int(self.sidePanel.vidWidthValue.text())
  height = int(self.sidePanel.vidHeightValue.text())
  dtype_string = str(self.sidePanel.dtypeValue.text())
  frames = fj.load_frames(fileName, width, height, dtype_string)

  frames = fj.gsr(frames, width, height)
  #np.save(os.path.expanduser('/Downloads/')+"gsr", frames)
  #frames.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"gsr.raw")
  #print("gsr saved to "+os.path.expanduser('/Downloads/')+"gsr")

class MyPlugin:
  def __init__(self):
    self.name = 'GSR'
    self.widget = QWidget()
  
  def run(self):
    pass
