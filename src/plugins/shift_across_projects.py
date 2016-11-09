#!/usr/bin/env python3

import os
from os.path import isfile, join
from os import listdir
import sys
import traceback
import ast
import time
import numpy as np
from shutil import copyfile
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui

sys.path.append('..')
import qtutil
from project import Project
import tifffile as tiff

from .util.mygraphicsview import MyGraphicsView
from .util import mse_ui_elements as mue
from .util import project_functions as pfs
from .util import fileloader

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

    # define ui components and global data
    self.view = MyGraphicsView(self.project)
    self.project_list = []
    self.project_at_ind = [] # project_at_ind[x] is what project the value in video_list at the x'th index is from
    self.shown_video_path = None
    self.video_list = QListView()
    self.list_shifted = QListView()
    self.origin_label = QLabel()
    (self.x, self.y) = ast.literal_eval(self.project['origin'])
    self.origin_label.setText('Origin to align to: ({} | {})'.format(round(self.x, 2), round(self.y, 2)))
    self.left = QFrame()
    self.right = QFrame()
    self.setup_ui()

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.list_shifted.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'shifted':
        self.video_list.model().appendRow(QStandardItem(f['path']))

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Data from other projects'))
    pb = QPushButton('Load JSON files from other projects')
    pb.clicked.connect(self.new_json)
    vbox.addWidget(pb)
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    vbox.addWidget(self.video_list)
    vbox.addWidget(qtutil.separator())
    vbox.addWidget(QLabel('Data from other projects'))
    vbox.addWidget(self.origin_label)
    pb = QPushButton('Align selected data to this project')
    pb.clicked.connect(self.shift_to_this)
    vbox.addWidget(pb)
    vbox.addWidget(QLabel('Shifted Data from other projects'))
    self.list_shifted.setStyleSheet('QListView::item { height: 26px; }')
    self.list_shifted.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.list_shifted)
    self.right.setLayout(vbox)
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)

  def selected_video_changed(self, selected, deselected):
      if not self.video_list.selectedIndexes():
          return
      self.selected_videos = []
      for index in self.video_list.selectedIndexes():
          project_from = self.project_at_ind[index.row()]
          vidpath = str(os.path.join(project_from, index.data(Qt.DisplayRole)) + '.npy')
          if vidpath not in self.selected_videos and vidpath != 'None':
              self.selected_videos = self.selected_videos + [vidpath]
              self.projects_selected_videos_are_from = self.projects_selected_videos_are_from + [project_from]
              self.shown_video_path = str(os.path.join(project_from,
                                                       self.video_list.currentIndex().data(Qt.DisplayRole))
                                          + '.npy')
      frame = pfs.load_reference_frame(self.shown_video_path)
      self.view.show(frame)

  def new_json(self):
    self.video_list.model().clear()
    fd = FileDialog()
    fd.exec_()
    fd.show()
    dirnames = fd.selectedFiles()

    if not dirnames or dirnames[0] == fd.directory():
        return
    for project_dir in dirnames:
        only_files = [join(project_dir, f) for f in listdir(project_dir) if isfile(join(project_dir, f))]
        json_paths = [f for f in only_files if f[-5:] == '.json']
        if not json_paths:
            qtutil.critical("Not a project directory. No JSON file found in " + project_dir + ". Skipping.")
            continue
        self.project_list = self.project_list + [Project(project_dir)]
        for project in self.project_list:
            for f in project.files:
                if f['type'] != 'video':
                    continue
                self.video_list.model().appendRow(QStandardItem(f['name']))
                self.project_at_ind = self.project_at_ind + [project.path]
            self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

  def shift_to_this(self):
      if not self.selected_videos:
          return
      for i, video_path in enumerate(self.selected_videos):
          project_from = self.projects_selected_videos_are_from[i]
          name_before, ext = os.path.splitext(os.path.basename(video_path))
          name_after = str(name_before + '_' + 'from_' + project_from.name)
          frames = fileloader.load_file(video_path)
          path_output = str(os.path.join(self.project.path, name_after) + '.npy')

          project_from_path = project_from.path
          str(os.path.join(project_from_path, index.data(Qt.DisplayRole)) + '.npy')

          project.path

  def apply_shifts(self, frames, shifts, progress_callback):
      shifted_frames = []
      for frame_no, shift in enumerate(shifts):
          tvec = shift["tvec"]
          progress_callback(frame_no / float(len(shifts)))
          frame = frames[frame_no]
          shifted_frames.append(ird.transform_img(frame, tvec=tvec))
      progress_callback(1)
      return shifted_frames

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
            qtutil.critical('Import of \'{}\' failed:\n'.format(filename) + \
                            traceback.format_exc())
        else:
            self.listview.model().appendRow(QStandardItem(filename))

#SLOW
class FileDialog(QtGui.QFileDialog):
    def __init__(self, *args):
        QtGui.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        for view in self.findChildren((QtGui.QListView, QtGui.QTreeView)):
            if isinstance(view.model(), QtGui.QFileSystemModel):
                view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

class MyPlugin:
    def __init__(self, project):
        self.name = 'Shift Across Projects'
        self.widget = Widget(project)
    def run(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget(None))
    w.show()
    app.exec_()
    sys.exit()
