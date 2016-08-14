#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    self.project = project

  def do_alignment(self):
    reference_for_align = str(self.sidePanel.imageFileList.currentItem().text())
    if reference_for_align == '':
        return
    width = int(self.sidePanel.vidWidthValue.text())
    height = int(self.sidePanel.vidHeightValue.text())
    dtype_string = str(self.sidePanel.dtypeValue.text())
    frame_ref = int(self.sidePanel.frameRefNameValue.text())

    # Get Filenames
    fileNames = range(0, self.sidePanel.imageFileList.__len__())
    for i in range(0, self.sidePanel.imageFileList.__len__()):
        fileNames[i] = str(self.sidePanel.imageFileList.item(i).text())

    # Fix for PySide. PySide doesn't support QStringList types. PyQt4 getOpenFileNames returns a QStringList, whereas PySide
    # returns a type (the first entry being the list of filenames).
    if isinstance(fileNames, types.TupleType): fileNames = fileNames[0]
    if hasattr(QtCore, 'QStringList') and isinstance(fileNames, QtCore.QStringList): fileNames = [str(i) for i in fileNames]

    # Get a dictionary of all videos
    newVids = {}
    if len(fileNames)>0:
        for fileName in fileNames:
            if fileName!='':
                frames = fj.load_frames(str(fileName), width, height, dtype_string)
                newVids[str(fileName)] = frames

    # Do alignments
    print("Doing alignments...")
    if (self.lp == None):
        self.lp = dj.get_distance_var(fileNames, frame_ref, newVids)
    print('Working on this file: ' + reference_for_align)

    # frames = dj.get_frames(reference_for_align, width, height) # This might work better if you have weird error: frames = dj.get_green_frames(str(self.lof[raw_file_to_align_ind]),width,height)
    for ind in range(len(self.lp)):
        frames = newVids[fileNames[ind]]
        frames = dj.shift_frames(frames, self.lp[ind])
        np.save(os.path.expanduser('~/Downloads/') + "aligned_" + str(ind), frames)
        #frames.astype(dtype_string).tofile(os.path.expanduser('~/Downloads/') + "aligned_" + str(ind) + ".raw")
        print("Alignment saved to "+os.path.expanduser('~/Downloads/') + "aligned_" + str(ind))

class MyPlugin:
  def __init__(self, project):
    self.name = 'Align images'
    self.widget = QWidget(project)
  
  def run(self):
    pass
