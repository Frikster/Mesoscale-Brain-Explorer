#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util import filter_jeff as fj

# on button click!

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project
    self.setup_ui()

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project)
    self.view.vb.setCursor(Qt.CrossCursor)
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    hhbox = QHBoxLayout()
    butt_gsr = QPushButton('Global Signal Regression')
    hhbox.addWidget(butt_gsr)
    vbox.addLayout(hhbox)
    vbox.addStretch()
    butt_gsr.clicked.connect(self.gsr)

    hbox.addLayout(vbox)
    self.setLayout(hbox)

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
  def __init__(self, project):
    self.name = 'GSR'
    self.widget = Widget(project)
  
  def run(self):
    pass
