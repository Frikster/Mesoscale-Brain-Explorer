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

from .util import fileloader, fileconverter

class NotConvertedError(Exception):
  pass

class FileAlreadyInProjectError(Exception):
  def __init__(self, filename):
    self.filename = filename

class RawConverterDialog(QDialog):
  def __init__(self, project, filename, parent=None):
    super(RawConverterDialog, self).__init__(parent)
    self.project = project
    self.filename = filename
    self.setup_ui()
  
  def setup_ui(self):
    self.setWindowTitle('Import Raw File')

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('<center><b>Importing \'{}\'</b></center>'.format(
      os.path.basename(self.filename))))
    vbox.addSpacing(10)

    grid = QGridLayout()

    grid.addWidget(QLabel('Width:'), 0, 0)
    self.sb_width = QSpinBox()
    self.sb_width.setMinimum(1)
    self.sb_width.setMaximum(1024)
    self.sb_width.setValue(256)
    grid.addWidget(self.sb_width, 0, 1)

    grid.addWidget(QLabel('Height:'), 1, 0)
    self.sb_height = QSpinBox()
    self.sb_height.setMinimum(1)
    self.sb_height.setMaximum(1024)
    self.sb_height.setValue(256)
    grid.addWidget(self.sb_height, 1, 1)

    grid.addWidget(QLabel('Channel:'), 2, 0)
    self.sb_channel = QSpinBox()
    self.sb_channel.setMinimum(1)
    self.sb_channel.setMaximum(3)
    self.sb_channel.setValue(3)
    grid.addWidget(self.sb_channel, 2, 1)

    grid.addWidget(QLabel('dtype:'), 3, 0)
    self.cb_dtype = QComboBox()
    for t in 'uint8', 'float32', 'float64':
      self.cb_dtype.addItem(t)
    grid.addWidget(self.cb_dtype, 3, 1)

    vbox.addLayout(grid)
    vbox.addStretch()

    pb = QPushButton('&Convert')
    pb.clicked.connect(self.convert_clicked)
    vbox.addWidget(pb)

    self.setLayout(vbox)
    self.resize(400, 220)

  def convert_clicked(self):
    dtype = str(self.cb_dtype.currentText())
    width = int(self.sb_width.value())
    height = int(self.sb_height.value())
    channels = int(self.sb_channel.value())
    path = os.path.splitext(os.path.basename(self.filename))[0] + '.npy'
    path = os.path.join(self.project.path, path)

    progress = QProgressDialog('Converting raw to npy...', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)
    progress.setValue(0)

    def callback(value):
      progress.setValue(int(value * 100))
      QApplication.processEvents()

    try:
      fileconverter.raw2npy(self.filename, path, dtype, width, height,
        channels, callback)
    except:
      qtutil.critical('Converting raw to npy failed.')
      progress.close()
    else:
      self.ret_filename = path
      self.close()

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

    ##


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
    dialog = RawConverterDialog(self.project, filename, self)
    dialog.ret_filename = None
    dialog.exec_()
    return dialog.ret_filename      

  def convert_tif(self, filename):
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
      qtutil.critical('Converting raw to npy failed.')
      progress.close()
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
