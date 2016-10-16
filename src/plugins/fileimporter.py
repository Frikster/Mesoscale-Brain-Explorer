#!/usr/bin/env python3

import os
import sys
import traceback
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

sys.path.append('..')
import qtutil
import tifffile as tiff

from .util import fileloader, fileconverter

class NotConvertedError(Exception):
  pass

class FileAlreadyInProjectError(Exception):
  def __init__(self, filename):
    self.filename = filename

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project
    self.setup_ui()

    self.listview.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'video':
        self.listview.model().appendRow(QStandardItem(f['path']))

  def setup_ui(self):
    vbox = QVBoxLayout()

    ## Related to importing Raws
    self.setWindowTitle('Import Raw File')

    vbox.addWidget(QLabel('Set the size all files are to be rescaled to'))

    grid = QGridLayout()

    grid.addWidget(QLabel('Width:'), 0, 0)
    self.rescale_width = QSpinBox()
    self.rescale_width.setMinimum(1)
    self.rescale_width.setMaximum(1024)
    self.rescale_width.setValue(256)
    grid.addWidget(self.rescale_width, 0, 1)

    grid.addWidget(QLabel('Height:'), 1, 0)
    self.rescale_height = QSpinBox()
    self.rescale_height.setMinimum(1)
    self.rescale_height.setMaximum(1024)
    self.rescale_height.setValue(256)
    grid.addWidget(self.rescale_height, 1, 1)

    grid.addWidget(QLabel('Set paramaters for of all imported raws'),2,0)
    grid.addWidget(QLabel('All raws will be rescaled upon import'),3,0)

    grid.addWidget(QLabel('Width:'), 4, 0)
    self.sb_width = QSpinBox()
    self.sb_width.setMinimum(1)
    self.sb_width.setMaximum(1024)
    self.sb_width.setValue(256)
    grid.addWidget(self.sb_width, 4, 1)

    grid.addWidget(QLabel('Height:'), 5, 0)
    self.sb_height = QSpinBox()
    self.sb_height.setMinimum(1)
    self.sb_height.setMaximum(1024)
    self.sb_height.setValue(256)
    grid.addWidget(self.sb_height, 5, 1)

    grid.addWidget(QLabel('Channel:'), 6, 0)
    self.sb_channel = QSpinBox()
    self.sb_channel.setMinimum(1)
    self.sb_channel.setMaximum(3)
    self.sb_channel.setValue(3)
    grid.addWidget(self.sb_channel, 6, 1)

    grid.addWidget(QLabel('dtype:'), 7, 0)
    self.cb_dtype = QComboBox()
    for t in 'uint8', 'float32', 'float64':
      self.cb_dtype.addItem(t)
    grid.addWidget(self.cb_dtype, 7, 1)

    vbox.addLayout(grid)
    vbox.addStretch()

    self.setLayout(vbox)
    self.resize(400, 220)

    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    self.listview.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.listview)

    hbox = QVBoxLayout()
    pb = QPushButton('New Video')
    pb.clicked.connect(self.new_video)
    hbox.addWidget(pb)

    vbox.addLayout(hbox)
    vbox.addStretch()
    self.setLayout(vbox)

  def convert_raw(self, filename):
    rescale_width = int(self.rescale_width.value())
    rescale_height = int(self.rescale_height.value())
    dtype = str(self.cb_dtype.currentText())
    width = int(self.sb_width.value())
    height = int(self.sb_height.value())
    channels = int(self.sb_channel.value())
    path = os.path.splitext(os.path.basename(filename))[0] + '.npy'
    path = os.path.join(self.project.path, path)

    progress = QProgressDialog('Converting raw to npy...', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    def callback(value):
      progress.setValue(int(value * 100))
      QApplication.processEvents()

    try:
      fileconverter.raw2npy(filename, path, dtype, width, height,
        channels, callback)
    except:
      qtutil.critical('Converting raw to npy failed.')
      progress.close()
    else:
      if width != rescale_width or height != rescale_height:
        unscaled = np.load(path)
        no_frames = len(unscaled)
        try:
          scaled = self.bin_ndarray(unscaled, (no_frames, rescale_height,
                                      rescale_width), callback, operation='mean')
          np.save(path, scaled)
        except:
          qtutil.critical('Rebinning raw failed. We can only scale down from larger sized files to preserve data')
          progress.close()
        else:
          ret_filename = path
      else:
        ret_filename = path
    return ret_filename

  def convert_tif(self, filename):
    rescale_width = int(self.rescale_width.value())
    rescale_height = int(self.rescale_height.value())
    channels = int(self.sb_channel.value())

    path = os.path.splitext(os.path.basename(filename))[0] + '.npy'
    path = os.path.join(self.project.path, path)

    progress = QProgressDialog('Converting tif to npy...', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    def callback(value):
      progress.setValue(int(value * 100))
      QApplication.processEvents()

    try:
      fileconverter.tif2npy(filename, path, callback)
    except:
      qtutil.critical('Converting tiff to npy failed.')
      progress.close()
    else:
      with tiff.TiffFile(filename) as tif:
        w, h = tif[0].shape
        no_frames = len(tif)
        if w != rescale_width or h != rescale_height:
          unscaled = np.load(path)
          try:
            scaled = self.bin_ndarray(unscaled, (no_frames, rescale_height,
                                        rescale_width), callback, operation='mean')
            np.save(path, scaled)
          except:
            qtutil.critical('Rebinning tiff failed. We can only scale down from larger sized files to preserve data')
            progress.close()
          else:
            ret_filename = path
        else:
          ret_filename = path
    return ret_filename

  def to_npy(self, filename):
    if filename.endswith('.raw'):
      filename = self.convert_raw(filename)
    elif filename.endswith('.tif'):
      filename = self.convert_tif(filename)
    else:
      raise fileloader.UnknownFileFormatError()
    return filename

  def import_file(self, filename):
    if not filename.endswith('.npy'):
      new_filename = self.to_npy(filename)
      if not new_filename:
        raise NotConvertedError()
      else:
        filename = new_filename

    if filename in [f['path'] for f in self.project.files]:
      raise FileAlreadyInProjectError(filename)      

    name, ext = os.path.splitext(os.path.basename(filename))

    self.project.files.append({
      'name': name,
      'path': filename,
      'type': 'video',
      'manipulations': []
    })
    self.project.save()
    return filename

  def import_files(self, filenames):
    for filename in filenames:
      if filename in [f['path'] for f in self.project.files]:
        continue
      try:
        filename = self.import_file(filename)
      except NotConvertedError:
        qtutil.warning('Skipping file \'{}\' since not converted.'.format(filename))
      except FileAlreadyInProjectError as e:
        qtutil.warning('Skipping file \'{}\' since already in project.'.format(e.filename))
      except:
        qtutil.critical('Import of \'{}\' failed:\n'.format(filename) +\
          traceback.format_exc())
      else:
        self.listview.model().appendRow(QStandardItem(filename))

  def new_video(self):
    filenames = QFileDialog.getOpenFileNames(
      self, 'Load images', QSettings().value('last_load_data_path'),
      'Video files (*.npy *.tif *.raw)')
    if not filenames:
      return
    QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
    self.import_files(filenames)

  def bin_ndarray(self, ndarray, new_shape, progress_callback, operation='sum'):
    """
    Bins an ndarray in all axes based on the target shape, by summing or
        averaging.

    Number of output dimensions must match number of input dimensions and
        new axes must divide old ones.

    Example
    -------
    #>>> m = np.arange(0,100,1).reshape((10,10))
    #>>> n = bin_ndarray(m, new_shape=(5,5), operation='sum')
    #>>> print(n)

    [[ 22  30  38  46  54]
     [102 110 118 126 134]
     [182 190 198 206 214]
     [262 270 278 286 294]
     [342 350 358 366 374]]

    """
    operation = operation.lower()
    if not operation in ['sum', 'mean']:
      raise ValueError("Operation not supported.")
    if ndarray.ndim != len(new_shape):
      raise ValueError("Shape mismatch: {} -> {}".format(ndarray.shape,
                                                         new_shape))
    compression_pairs = [(d, c // d) for d, c in zip(new_shape,
                                                     ndarray.shape)]
    flattened = [l for p in compression_pairs for l in p]
    ndarray = ndarray.reshape(flattened)
    for i in range(len(new_shape)):
      progress_callback(i / len(new_shape))
      op = getattr(ndarray, operation)
      ndarray = op(-1 * (i + 1))
    progress_callback(1)
    return ndarray

class MyPlugin:
  def __init__(self, project):
    self.name = 'Import video files'
    self.widget = Widget(project)

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
