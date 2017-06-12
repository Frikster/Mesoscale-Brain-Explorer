#!/usr/bin/env python3

import functools
import os
import sys
import traceback
from shutil import copyfile

import numpy as np
import psutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append('..')
import qtutil
import tifffile as tiff
from .util.plugin import PluginDefault

from .util import file_io, fileconverter
from .util import custom_qt_items as cqt

class NotConvertedError(Exception):
  pass

class FileAlreadyInProjectError(Exception):
  def __init__(self, filename):
    self.filename = filename

class Widget(QWidget):
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
    dtype_default = 0

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)

    if not project or not isinstance(plugin_position, int):
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
    self.setup_whats_this()

  def setup_params(self):
    if len(self.params) == 1:
        self.update_plugin_params(self.Labels.scale_factor_label, self.Defaults.scale_factor_default)
        self.update_plugin_params(self.Labels.channel_label, self.Defaults.channel_default)
        self.update_plugin_params(self.Labels.width_label, self.Defaults.width_default)
        self.update_plugin_params(self.Labels.height_label, self.Defaults.height_default)
        self.update_plugin_params(self.Labels.no_channels_label, self.Defaults.no_channels_default)
        self.update_plugin_params(self.Labels.dtype_label, self.Defaults.dtype_default)

    self.scale_factor.setValue(self.params[self.Labels.scale_factor_label])
    self.channel.setValue(self.params[self.Labels.channel_label])
    self.sb_width.setValue(self.params[self.Labels.width_label])
    self.sb_height.setValue(self.params[self.Labels.height_label])
    self.sb_channel.setValue(self.params[self.Labels.no_channels_label])
    self.cb_dtype.setCurrentIndex(self.params[self.Labels.dtype_label])

  def setup_ui(self):
    vbox = QVBoxLayout()

    ## Related to importing Raws
    self.setWindowTitle('Import Raw File')
    grid = QGridLayout()
    grid.addWidget(QLabel('Set channel and scale factor used for all imported data'), 0, 0)

    grid.addWidget(QLabel('Scale Factor:'), 1, 0)
    self.scale_factor = QDoubleSpinBox()
    self.scale_factor.setSingleStep(0.25)
    self.scale_factor.setMinimum(0.25)
    self.scale_factor.setMaximum(1.00)
    self.scale_factor.setValue(1.0)
    grid.addWidget(self.scale_factor, 1, 1)

    grid.addWidget(qtutil.separator(), 2, 0)
    grid.addWidget(qtutil.separator(), 2, 1)

    grid.addWidget(QLabel('This section only applies to imported raw files.'), 3, 0)
    grid.addWidget(QLabel('All imported raws will also be rescaled using the above value'), 4, 0)

    grid.addWidget(QLabel('Width:'), 5, 0)
    self.sb_width = QSpinBox()
    self.sb_width.setMinimum(1)
    self.sb_width.setMaximum(1024)
    self.sb_width.setValue(256)
    grid.addWidget(self.sb_width, 5, 1)
    grid.addWidget(QLabel('Height:'), 6, 0)
    self.sb_height = QSpinBox()
    self.sb_height.setMinimum(1)
    self.sb_height.setMaximum(1024)
    self.sb_height.setValue(256)
    grid.addWidget(self.sb_height, 6, 1)
    grid.addWidget(QLabel('Number of channels in raw:'), 7, 0)
    self.sb_channel = QSpinBox()
    self.sb_channel.setMinimum(1)
    self.sb_channel.setMaximum(3)
    self.sb_channel.setValue(3)
    grid.addWidget(self.sb_channel, 7, 1)

    grid.addWidget(QLabel('Channel in raw to be imported:'), 8, 0)
    self.channel = QSpinBox()
    self.channel.setMinimum(1)
    self.channel.setMaximum(3)
    self.channel.setValue(2)
    grid.addWidget(self.channel, 8, 1)

    grid.addWidget(QLabel('Raw dtype:'), 9, 0)
    self.cb_dtype = QComboBox()
    for t in 'uint8', 'float32', 'float64':
      self.cb_dtype.addItem(t)
    grid.addWidget(self.cb_dtype, 9, 1)
    grid.addWidget(qtutil.separator(), 10, 0)
    grid.addWidget(qtutil.separator(), 10, 1)
    vbox.addLayout(grid)

    self.setLayout(vbox)
    self.resize(400, 220)

    vbox.addWidget(cqt.WarningWidget('Warning. This application has not been memory optimized for conversion.'
                                     ' We advise you only import raw or tiff files no larger than 1/4 of your memory. '
                                     'e.g. If you have 8GB RAM then we recommend not importing a raw or tiff larger '
                                     'than 2GB. It may or may not freeze your system otherwise.'
                                     '\n \n'
                                     'Press the button below to proceed once all parameters above have been set.'))
    pb = QPushButton('Import Image Stack(s)')
    pb.clicked.connect(self.execute_primary_function)
    vbox.addWidget(pb)

    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    self.listview.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.listview)

    vbox.addStretch()
    self.setLayout(vbox)

  def setup_param_signals(self):
      self.scale_factor.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.scale_factor_label))
      self.channel.valueChanged[int].connect(functools.partial(self.update_plugin_params, self.Labels.channel_label))
      self.sb_width.valueChanged[int].connect(functools.partial(self.update_plugin_params, self.Labels.width_label))
      self.sb_height.valueChanged[int].connect(functools.partial(self.update_plugin_params, self.Labels.height_label))
      self.sb_channel.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                  self.Labels.no_channels_label))
      self.cb_dtype.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                       self.Labels.dtype_label))

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
    # todo: figure out whether channel goes in path name or somehow in
    new_filename = os.path.basename(filename)[:-4]
    new_filename = os.path.join(self.project.path, new_filename) + '.npy'
    if os.path.isfile(new_filename):
        i = 1
        path_after = new_filename
        while os.path.isfile(path_after):
            name_after = new_filename[:-4] + '(' + str(i) + ')' + '.npy'
            path_after = os.path.join(self.project.path, name_after)
            i = i + 1
        path = path_after
    else:
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
        fileconverter.raw2npy(filename, path, dtype, width, height, channels, channel, callback)
    except:
      warn_msg = "Continue trying to convert raw to npy despite problems? Your data might be corrupt."
      reply = QMessageBox.question(self, 'Import Issues Detected',
                                     warn_msg, QMessageBox.Yes, QMessageBox.No)
      if reply == QMessageBox.Yes:
          try:
              fileconverter.raw2npy(filename, path, dtype, width, height, channels, channel, callback,
                                    ignore_shape_error=True)
          except:
              qtutil.critical('Converting raw to npy still fails.')
              progress.close()
              return
      if reply == QMessageBox.No:
          return

    ret_filename = path
    if rescale_value != 1.00:
      unscaled = np.load(path)
      no_frames = len(unscaled)
      try:
        scaled = self.bin_ndarray(unscaled, (no_frames, rescale_height,
                                    rescale_width), callback, operation='mean')
        np.save(path, scaled)
      except:
        qtutil.critical("Rebinning raw failed. Please check your scale factor. Use the Help -> 'Whats this' feature"
                        " on the scale factor for more info.")
        progress.close()
    return ret_filename

  def convert_tif(self, filename):
    rescale_value = float(self.scale_factor.value())
    channel = int(self.channel.value())

    new_filename = os.path.basename(filename)[:-4]
    new_filename = os.path.join(self.project.path, new_filename) + '.npy'
    if os.path.isfile(new_filename):
        i = 1
        path_after = new_filename
        while os.path.isfile(path_after):
            name_after = new_filename[:-4] + '(' + str(i) + ')' + '.npy'
            path_after = os.path.join(self.project.path, name_after)
            i = i + 1
        path = path_after
    else:
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
      raise file_io.UnknownFileFormatError()
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
          file_size = os.path.getsize(filename)
          available = list(psutil.virtual_memory())[1]
          if file_size > available:
              qtutil.critical('Not enough memory. File is of size ' + str(file_size) +
                              ' and available memory is: ' + str(available))
              raise MemoryError('Not enough memory. File is of size ' + str(file_size) +
                                ' and available memory is: ' + str(available))


          qtutil.info('Copying .npy from ' + filename + ' to ' + new_filename +
                      '. We recommend doing this manually for large files')
          copyfile_progress = QProgressDialog('Progress Copying ' + filename + 'to ' + new_filename,
                                              'Abort', 0, 100, self)
          copyfile_progress.setAutoClose(True)
          copyfile_progress.setMinimumDuration(0)

          def callback(x):
              copyfile_progress.setValue(x * 100)
              QApplication.processEvents()
          callback(0.0)
          if copyfile_progress.wasCanceled():
              return
          copyfile(filename, new_filename)
          if copyfile_progress.wasCanceled():
              return
          callback(1.0)
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
        qtutil.warning('Skipping file \'{}\' since not converted.'.format(filename))
      except:
        qtutil.critical('Import of \'{}\' failed:\n'.format(filename) +\
          traceback.format_exc())
      else:
        self.listview.model().appendRow(QStandardItem(imported_path))
        imported_paths = imported_paths + [imported_path]
    return imported_paths

  def execute_primary_function(self, input_paths = None):
    if not input_paths:
        filenames = QFileDialog.getOpenFileNames(
          self, 'Load images', QSettings().value('last_load_data_path'),
          'Video files (*.npy *.tif *.raw)')
        if not filenames:
          return
        QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
    else:
        filenames = input_paths
    # proj_file_names = [self.project.files[i]['name'] for i in range(len(self.project.files))]
    # new_file_names = [os.path.splitext(os.path.basename(filename))[0] for filename in filenames]
    # tester = [name for name in proj_file_names if name in new_file_names]
    #
    # # if tester:
    # #     qtutil.critical("These files already exist in the project: "
    # #                     + str(tester) +
    # #                     " Please change their names if you want to import them")
    # #     return [" "] #todo: end automation more elegantly
    return self.import_files(filenames)

  def get_input_paths(self):
      filenames = QFileDialog.getOpenFileNames(
          self, 'Load images', QSettings().value('last_load_data_path'),
          'Video files (*.npy *.tif *.raw)')
      if not filenames:
          return
      QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
      return filenames

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

  def setup_whats_this(self):
      self.scale_factor.setWhatsThis("Scales the imported image stack down by this factor. e.g a 256x256 image stack "
                                     "will be 128x128 with this set to 0.5. Note that import values that don't "
                                     "scale your image stack down to a height and width where both are integers you "
                                     "will receive an error. e.g you cannot scale a 128x128 by 0.6 as this will "
                                     "attempt to create a 76.8x76.8 file which is not possible as we cannot have"
                                     "'0.6' of a pixel.")
      self.channel.setWhatsThis("Set which channel is imported from your raw. Only one channel imports are "
                                "currently supported for tiff files a npy files. Please separate your multi-channel"
                                "tiff image stacks into separate files one per channel to import all the channels")
      self.sb_width.setWhatsThis("Raw files lack headers so file shape needs to be specified manually")
      self.sb_height.setWhatsThis("Raw files lack headers so file shape needs to be specified manually")
      self.sb_channel.setWhatsThis("Set how many channel the raw has since raw files do not have headers specifying "
                                   "shape")
      self.cb_dtype.setWhatsThis("Specify the data type of your raw file to be imported. Raw files do not have headers "
                                 "so this needs to be specified manually")


class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Import Image Stacks'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def get_input_paths(self):
    return self.widget.get_input_paths()

  def check_ready_for_automation(self, expected_input_number):
      return True

  def automation_error_message(self):
      return "YOU SHOULD NOT BE ABLE TO SEE THIS"


if __name__ == '__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget())
  w.show()
  app.exec_()
  sys.exit()
