#!/usr/bin/env python3

import os
import sys
import traceback
import functools
from shutil import copyfile

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append('..')
import qtutil
import tifffile as tiff

from .util import fileloader, fileconverter
from .util import mse_ui_elements as mue

class Labels:
    scale_factor_label = "Scale Factor"
    channel_label = "Channel"
    width_label = "Width"
    height_label = "Height"
    no_channels_label = "Number of channels"
    dtype_label = "dtype"

class Defaults:
    scale_factor_default = 1.00
    channel_default = 2
    width_default = 256
    height_default = 256
    no_channels_default = 3
    dtype_default = 0 #index

class NotConvertedError(Exception):
  pass

class FileAlreadyInProjectError(Exception):
  def __init__(self, filename):
    self.filename = filename

class Widget(QWidget):
  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return
    self.plugin_position = plugin_position
    self.project = project

    self.setup_ui()
    if isinstance(plugin_position, int):
        self.params = project.pipeline[self.plugin_position]
        assert(self.params['name'] == 'fileimporter')
        self.setup_param_signals()
        self.setup_params()

    self.listview.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'video':
        self.listview.model().appendRow(QStandardItem(f['path']))

  def setup_params(self):
    if len(self.params) == 1:
        self.update_plugin_params(Labels.scale_factor_label, Defaults.scale_factor_default)
        self.update_plugin_params(Labels.channel_label, Defaults.channel_default)
        self.update_plugin_params(Labels.width_label, Defaults.width_default)
        self.update_plugin_params(Labels.height_label, Defaults.height_default)
        self.update_plugin_params(Labels.no_channels_label, Defaults.no_channels_default)
        self.update_plugin_params(Labels.dtype_label, Defaults.dtype_default)

    # "Scale Factor": 1.00,
    # "Channel": 2,
    # "Width": 256,
    # "Height": 256,
    # "Number of channels": 3,
    # "dtype": "uint8"

    self.scale_factor.setValue(self.params[Labels.scale_factor_label])
    self.channel.setValue(self.params[Labels.channel_label])
    self.sb_width.setValue(self.params[Labels.width_label])
    self.sb_height.setValue(self.params[Labels.height_label])
    self.sb_channel.setValue(self.params[Labels.no_channels_label])
    self.cb_dtype.setCurrentIndex(self.params[Labels.dtype_label])

  def setup_ui(self):
    vbox = QVBoxLayout()

    ## Related to importing Raws
    self.setWindowTitle('Import Raw File')

    # vbox.addWidget(QLabel('Set the size all data are to be rescaled to'))

    grid = QGridLayout()
    grid.addWidget(QLabel('Set channel and scale factor used for all imported data'), 0, 0)

    # grid.addWidget(QLabel('Width:'), 0, 0)
    # self.rescale_width = QSpinBox()
    # self.rescale_width.setMinimum(1)
    # self.rescale_width.setMaximum(1024)
    # self.rescale_width.setValue(256)
    # grid.addWidget(self.rescale_width, 0, 1)

    # grid.addWidget(QLabel('Height:'), 1, 0)
    # self.rescale_height = QSpinBox()
    # self.rescale_height.setMinimum(1)
    # self.rescale_height.setMaximum(1024)
    # self.rescale_height.setValue(256)
    # grid.addWidget(self.rescale_height, 1, 1)

    grid.addWidget(QLabel('Scale Factor:'), 1, 0)
    self.scale_factor = QDoubleSpinBox()
    self.scale_factor.setSingleStep(0.25)
    self.scale_factor.setMinimum(0.25)
    self.scale_factor.setMaximum(1.00)
    self.scale_factor.setValue(1.0)
    grid.addWidget(self.scale_factor, 1, 1)

    grid.addWidget(QLabel('Channel:'), 2, 0)
    self.channel = QSpinBox()
    self.channel.setMinimum(1)
    self.channel.setMaximum(3)
    self.channel.setValue(2)
    grid.addWidget(self.channel, 2, 1)

    grid.addWidget(qtutil.separator(), 3, 0)
    grid.addWidget(qtutil.separator(), 3, 1)
    grid.addWidget(QLabel('Set paramaters for all imported raws'), 4, 0)
    grid.addWidget(QLabel('All raws will be rescaled and specified channel imported upon conversion'), 5, 0)
    grid.addWidget(QLabel('Width:'), 6, 0)
    self.sb_width = QSpinBox()
    self.sb_width.setMinimum(1)
    self.sb_width.setMaximum(1024)
    self.sb_width.setValue(256)
    grid.addWidget(self.sb_width, 6, 1)
    grid.addWidget(QLabel('Height:'), 7, 0)
    self.sb_height = QSpinBox()
    self.sb_height.setMinimum(1)
    self.sb_height.setMaximum(1024)
    self.sb_height.setValue(256)
    grid.addWidget(self.sb_height, 7, 1)
    grid.addWidget(QLabel('Number of channels:'), 8, 0)
    self.sb_channel = QSpinBox()
    self.sb_channel.setMinimum(1)
    self.sb_channel.setMaximum(3)
    self.sb_channel.setValue(3)
    grid.addWidget(self.sb_channel, 8, 1)
    grid.addWidget(QLabel('dtype:'), 9, 0)
    self.cb_dtype = QComboBox()
    for t in 'uint8', 'float32', 'float64':
      self.cb_dtype.addItem(t)
    grid.addWidget(self.cb_dtype, 9, 1)
    grid.addWidget(qtutil.separator(), 10, 0)
    grid.addWidget(qtutil.separator(), 10, 1)
    vbox.addLayout(grid)
    vbox.addStretch()

    self.setLayout(vbox)
    self.resize(400, 220)

    vbox.addWidget(mue.WarningWidget('Warning. This application has not yet been memory optimized for conversion.'
                                     ' We advise you only import files no larger than 1/4 of your memory'))
    pb = QPushButton('New Video')
    pb.clicked.connect(self.new_video)
    vbox.addWidget(pb)

    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    self.listview.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.listview)

    vbox.addStretch()
    self.setLayout(vbox)

  def setup_param_signals(self):
      self.scale_factor.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      Labels.scale_factor_label))
      self.channel.valueChanged[int].connect(functools.partial(self.update_plugin_params, Labels.channel_label))
      self.sb_width.valueChanged[int].connect(functools.partial(self.update_plugin_params, Labels.width_label))
      self.sb_height.valueChanged[int].connect(functools.partial(self.update_plugin_params, Labels.height_label))
      self.sb_channel.valueChanged[int].connect(functools.partial(self.update_plugin_params, Labels.no_channels_label))
      self.cb_dtype.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params, Labels.dtype_label))

  def update_plugin_params(self, key, val):
      self.params[key] = val
      self.project.pipeline[self.plugin_position] = self.params
      self.project.save()


  def convert_raw(self, filename):
    rescale_value = float(self.scale_factor.value())
    dtype = str(self.cb_dtype.currentText())
    width = int(self.sb_width.value())
    height = int(self.sb_height.value())
    rescale_width = int(width * rescale_value)
    rescale_height = int(height * rescale_value)
    channels = int(self.sb_channel.value())
    channel = int(self.channel.value())
    path = os.path.splitext(os.path.basename(filename))[0] + '_channel_' + str(channel) + '.npy'
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
        channels, channel, callback)
    except:
      qtutil.critical('Converting raw to npy failed.')
      progress.close()
    else:
      ret_filename = path
      if rescale_value != 1.00:
        unscaled = np.load(path)
        no_frames = len(unscaled)
        try:
          scaled = self.bin_ndarray(unscaled, (no_frames, rescale_height,
                                      rescale_width), callback, operation='mean')
          np.save(path, scaled)
        except:
          qtutil.critical('Rebinning raw failed. We can only scale down from larger sized files to preserve data')
          progress.close()
    return ret_filename

  def convert_tif(self, filename):
    rescale_value = float(self.scale_factor.value())
    # channel = int(self.channel.value())

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
      ret_filename = path
      with tiff.TiffFile(filename) as tif:
        if rescale_value != 1.00:
          w, h = tif[0].shape
          rescale_width = int(w * rescale_value)
          rescale_height = int(h * rescale_value)
          no_frames = len(tif)
          unscaled = np.load(path)
          try:
            scaled = self.bin_ndarray(unscaled, (no_frames, rescale_height,
                                        rescale_width), callback, operation='mean')
            np.save(path, scaled)
          except:
            qtutil.critical('Rebinning tiff failed. We can only scale down from larger sized files to preserve data')
            progress.close()
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
    else:
      new_filename = os.path.basename(filename)
      new_filename = os.path.join(self.project.path, new_filename)
      if os.path.normpath(filename) != os.path.normpath(new_filename):
          qtutil.info('Copying .npy from ' + filename + ' to ' + new_filename +
                      '. You can do this manually for large files to see a progress bar')
          copyfile(filename, new_filename)
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
    imported_paths = []
    for filename in filenames:
      if filename in [f['path'] for f in self.project.files]:
        continue
      try:
        imported_path = self.import_file(filename)
      except NotConvertedError:
        qtutil.warning('Skipping file \'{}\' since not converted.'.format(imported_path))
      except FileAlreadyInProjectError as e:
        qtutil.warning('Skipping file \'{}\' since already in project.'.format(e.imported_path))
      except:
        qtutil.critical('Import of \'{}\' failed:\n'.format(imported_path) +\
          traceback.format_exc())
      else:
        self.listview.model().appendRow(QStandardItem(imported_path))
        imported_paths = imported_paths + [imported_path]
    return imported_paths

  def new_video(self):
    filenames = QFileDialog.getOpenFileNames(
      self, 'Load images', QSettings().value('last_load_data_path'),
      'Video files (*.npy *.tif *.raw)')
    if not filenames:
      return
    QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
    return self.import_files(filenames)

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
  def __init__(self, project, plugin_position):
    self.name = 'Import Image Stacks'
    self.widget = Widget(project, plugin_position)

  def run(self, input_paths = None):
    return self.widget.new_video()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget())
  w.show()
  app.exec_()
  sys.exit()
