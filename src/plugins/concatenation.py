#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
    def do_concat(self):
        width = int(self.sidePanel.vidWidthValue.text())
        height = int(self.sidePanel.vidHeightValue.text())
        dtype_string = str(self.sidePanel.dtypeValue.text())
        # Get Filenames
        fileNames = range(0, self.sidePanel.imageFileList.__len__())
        for i in range(0, self.sidePanel.imageFileList.__len__()):
            fileNames[i] = str(self.sidePanel.imageFileList.item(i).text())

        # Get a list of all videos
        vids = {}
        if len(fileNames)>0:
            for fileName in fileNames:
                if fileName!='':
                    frames = fj.load_frames(str(fileName), width, height, dtype_string)
                    vids[str(fileName)] = frames

        concat_frames = np.concatenate(vids.values())
        np.save(os.path.expanduser('~/Downloads/')+"concatenated", concat_frames)
        #concat_frames.astype(dtype_string).tofile(os.path.expanduser('~/Downloads/')+"concatenated.raw")
        print("concatenated file saved to "+os.path.expanduser('~/Downloads/')+"concatenated")

class MyPlugin:
  def __init__(self, project):
    self.name = 'Concatenation'
    self.widget = QWidget()
  
  def run(self):
    pass
