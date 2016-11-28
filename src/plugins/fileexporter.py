import os
import shutil
import sys
import traceback

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append('..')
import qtutil

from .util.qt import FileTable, MyProgressDialog
from .util import fileloader

import tifffile as tiff
#import cv2

class Exporter(QWidget):
  def __init__(self, parent=None):
    super(Exporter, self).__init__(parent)

  def export_mp4(self, fileinfo, filename):
    pass
  
  def export_avi(self, fileinfo, filename):
    return
    progress = MyProgressDialog('File Exporter', 'Writing to avi...', self)
    try:
      frames = fileloader.load_file(fileinfo['path'])
      if frames.dtype != np.uint8:
        frames = frames.astype(np.uint8)
      video = cv2.VideoWriter(
        filename, cv2.cv.CV_FOURCC(*'DIVX'), 10,
        (frames.shape[1], frames.shape[2]), False
      )
      for i, frame in enumerate(frames):
        progress.setValue(100 * i / float(len(frames)-1))
        video.write(frame)
      cv2.destroyAllWindows()
      video.release()
    except:
      progress.close()
      qtutil.critical('Video file could not be written.', self)
  
  def export_tif(self, fileinfo, filename):
    frames = fileloader.load_file(fileinfo['path'])
    #todo: include option in export to select dtype (only 16 and 32 work in imageJ)
    frames = frames.astype(np.float32)
    tiff.imsave(filename, frames)
  
  def export_raw(self, fileinfo, filename):
    frames = fileloader.load_file(fileinfo['path'])
    frames.tofile(filename)
  
  def export_roi(self, fileinfo, filename):
    try:
      shutil.copyfile(fileinfo['path'], filename)
    except:
      qtutil.critical('File could not be copied.\n' + traceback.format_exc(), self)

class NoFileSelectedError(Exception):
  pass

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project
    self.setup_ui()
    self.exporter = Exporter(self)

  def setup_ui(self):
    vbox = QVBoxLayout()

    self.table = FileTable(self.project.files)
    self.table.setSelectionMode(QAbstractItemView.SingleSelection)
    self.table.doubleClicked.connect(self.row_doubleclicked)
    vbox.addWidget(self.table)

    pb = QPushButton('&Export')
    pb.clicked.connect(self.export_clicked)
    vbox.addWidget(pb)

    self.setLayout(vbox)

  def filedialog(self, name, filters):
    path = QSettings().value('export_path')
    dialog = QFileDialog(self)
    dialog.setWindowTitle('Export to')
    dialog.setDirectory(str(path))
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setOption(QFileDialog.DontUseNativeDialog)
    dialog.selectFile(name)
    dialog.setFilter(';;'.join(filters.values()))
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    if not dialog.exec_():
      return None
    filename = str(dialog.selectedFiles()[0])
    QSettings().setValue('export_path', os.path.dirname(filename))
    filter_ = str(dialog.selectedNameFilter())
    ext = [f for f in filters if filters[f] == filter_][0] 
    if not filename.endswith(ext):
      filename = filename + ext
    return filename

  def export_roi(self, fileinfo):
    """Ask for filename and call exporter function"""
    filters = {
      '.roi': 'ROI file (*.roi)'
    }
    default = 'name' in fileinfo and fileinfo['name'] or 'untitled'
    filename = self.filedialog(default, filters)
    if filename:
      assert(filename.endswith('.roi'))
      self.exporter.export_roi(fileinfo, filename)

  def export_video(self, fileinfo):
    """Ask for filename and dispatch based on requested file format"""
    filters = {
      #'.mp4': 'MP4 file (*.mp4)',
      '.avi': 'AVI file (*.avi)',
      '.tif': 'TIF file (*.tif)',
      '.raw': 'RAW file (*.raw)'
    }
    default = 'name' in fileinfo and fileinfo['name'] or 'untitled'
    filename = self.filedialog(default, filters)
    if not filename:
      return

    if filename.endswith('.avi'):
      self.exporter.export_avi(fileinfo, filename)
    elif filename.endswith('.mp4'):
      self.exporter.export_mp4(fileinfo, filename)
    elif filename.endswith('.tif'):
      self.exporter.export_tif(fileinfo, filename)
    elif filename.endswith('.raw'):
      self.exporter.export_raw(fileinfo, filename)
    else:
      assert(False)

  def export(self, fileinfo):
    """Dispatch according to field 'type'"""
    if fileinfo['type'] == 'roi':
      self.export_roi(fileinfo)
    elif fileinfo['type'] == 'video':
      self.export_video(fileinfo)
    else:
      qtutil.critical('Unsupported file type.')

  def export_clicked(self):
    """Retrieve fileinfo and call export"""
    rows = self.table.selectionModel().selectedRows()
    if not rows:
      return
    assert(len(rows) == 1)
    f = self.table.model().get_entry(rows[0])    
    self.export(f)

  def row_doubleclicked(self, index):
    """Retrieve fileinfo and call export"""
    f = self.table.model().get_entry(index)
    self.export(f)

class MyPlugin:
  def __init__(self, project):
    self.name = 'Export files'
    self.widget = Widget(project)

  def run(self):
    pass
