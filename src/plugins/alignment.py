#!/usr/bin/env python3

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pandas as pd
import time
import os
import numpy as np
import imreg_dft as ird

from .util import fileloader
from .util import displacement_jeff as djeff
from .util.qt import PandasModel, FileTableModel

class TableView(QTableView):
  def __init__(self, parent=None):
    super(TableView, self).__init__(parent)

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project
    self.setup_ui()
  
    self.update_tables()

    for table in self.table1, self.table2:
      table.verticalHeader().hide()
      table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
      table.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.table1.setSelectionMode(QAbstractItemView.MultiSelection)
  
  def setup_ui(self):
    vbox = QVBoxLayout()
    self.table1 = TableView()
    vbox.addWidget(self.table1)
    pb = QPushButton('&Align')
    pb.clicked.connect(self.align_clicked)
    vbox.addWidget(pb)
    self.table2 = TableView()
    vbox.addWidget(self.table2)
    self.setLayout(vbox)

  def update_tables(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    self.table1.setModel(FileTableModel(videos))

    videos = [
      f for f in self.project.files
      if 'manipulations' in f and 'align' in f['manipulations']
    ]
    self.table2.setModel(PandasModel(pd.DataFrame(videos)))

  def align_clicked(self):
    selection = self.table1.selectionModel().selectedRows()
    filenames = [self.table1.model().get_path(index) for index in selection]
    if not filenames:
      return

    progress = QProgressDialog('Aligning file...', 'Abort', 0, 100, self)
    progress.setAutoClose(True)
    progress.setMinimumDuration(0)

    def callback(x):
      progress.setValue(x * 100)
      QApplication.processEvents()
      #time.sleep(0.01)

    reference_frame = np.load(filenames[0])[400]
    filenames = self.align_videos(filenames, reference_frame, callback)

    for filename in filenames:
      if filename in [f['path'] for f in self.project.files]:
        continue
      name, ext = os.path.splitext(os.path.basename(filename))
      f = {
        'name': name,
        'path': filename,
        'type': 'video',
        'manipulations': 'align'
      }
      self.project.files.append(f)
    self.project.save()
    self.update_tables()

  def compute_shifts(self, template_frame, frames, progress_callback):
    results = []
    for i, frame in enumerate(frames):
      progress_callback(i / float(len(frames) - 1))
      results = results + [ird.translation(template_frame, frame)]
    return results

  def apply_shifts(self, frames, shifts, progress_callback):
    shifted_frames = []
    for frame_no, shift in enumerate(shifts):
      tvec = shift["tvec"]
      progress_callback(frame_no / float(len(shifts) - 1))
      frame = frames[frame_no]
      shifted_frames.append(ird.transform_img(frame, tvec=tvec))
    return shifted_frames

  def align_videos(self, filenames, reference_frame, progress_callback):
    """Return filenames of generated videos"""
    progress_callback(0)
    ret_filenames = []
    reference_frame
    for filename in filenames:
      frames = np.load(filename)
      shifts = self.compute_shifts(reference_frame, frames, progress_callback)
      shifted_frames = self.apply_shifts(frames, shifts, progress_callback)
      path = os.path.join(os.path.dirname(filename), 'aligned_' + \
                          os.path.basename(filename))
      fileloader.save_file(path, shifted_frames)
      ret_filenames.append(path)
    progress_callback(1)
    return ret_filenames

class MyPlugin:
  def __init__(self, project):
    self.name = 'Align images'
    self.widget = Widget(project)
  
  def run(self):
    pass
