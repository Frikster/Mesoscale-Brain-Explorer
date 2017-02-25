#!/usr/bin/env python3

import ast
import os
import sys
import traceback
from os import listdir
from os.path import isfile, join

import numpy as np
from PyQt4 import QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

sys.path.append('..')
import qtutil
from project import Project
import imreg_dft as ird

from .util.mygraphicsview import MyGraphicsView
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
    self.selected_videos = []
    #self.projects_selected_videos_are_from = []
    [self.x, self.y] = self.project['origin']
    self.origin_from_project = QLabel("Make sure the origin of all external projects loaded is correct")
    self.origin_label.setText('Origin of this project all files will be shifted to: ({} | {})'.format(round(self.x, 2),
                                                                                                      round(self.y, 2)))
    self.left = QFrame()
    self.right = QFrame()
    self.setup_ui()

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.video_list.doubleClicked.connect(self.video_triggered)
    self.list_shifted.setModel(QStandardItemModel())
    self.list_shifted.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_shifted_changed)
    for f in self.project.files:
      if f['type'] == 'shifted':
        self.video_list.model().appendRow(QStandardItem(f['path']))

  def video_triggered(self, index):
      pfs.video_triggered(self, index)

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    pb = QPushButton('Load JSON files from other projects')
    pb.clicked.connect(self.new_json)
    vbox.addWidget(pb)
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    vbox.addWidget(self.video_list)
    vbox.addWidget(qtutil.separator())
    vbox.addWidget(self.origin_label)
    pb = QPushButton('Shift selected data to this project')
    pb.clicked.connect(self.shift_to_this)
    vbox.addWidget(pb)
    vbox.addWidget(QLabel('Data imported to this project after shift'))
    self.list_shifted.setStyleSheet('QListView::item { height: 26px; }')
    self.list_shifted.setSelectionMode(QAbstractItemView.SingleSelection)
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

  def selected_shifted_changed(self, selected, deselected):
      if not self.list_shifted.selectedIndexes():
          return
      self.selected_videos = []
      for index in self.list_shifted.selectedIndexes():
          vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
          if vidpath not in self.selected_videos and vidpath != 'None':
              self.selected_videos = self.selected_videos + [vidpath]
              self.shown_video_path = str(os.path.join(self.project.path,
                                                       self.list_shifted.currentIndex().data(Qt.DisplayRole))
                                          + '.npy')
      frame = pfs.load_reference_frame(self.shown_video_path)
      self.view.show(frame)

  def selected_video_changed(self, selected, deselected):
      if not self.video_list.selectedIndexes():
          return
      self.selected_videos = []
      for index in self.video_list.selectedIndexes():
          project_from = self.project_at_ind[index.row()]
          vidpath = str(os.path.join(project_from.path, index.data(Qt.DisplayRole)) + '.npy')
          if vidpath not in self.selected_videos and vidpath != 'None':
              self.selected_videos = self.selected_videos + [vidpath]
              #self.projects_selected_videos_are_from = self.projects_selected_videos_are_from + [project_from]
              self.shown_video_path = str(os.path.join(project_from.path,
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

    if not dirnames or os.path.normpath(dirnames[0]) == os.path.normpath(fd.directory().absolutePath()):
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
                self.project_at_ind = self.project_at_ind + [project]
            self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

  def shift_to_this(self):
      if not self.selected_videos:
          return
      progress_global = QProgressDialog('Total progress shifting all files', 'Abort', 0, 100, self)
      progress_global.setAutoClose(True)
      progress_global.setMinimumDuration(0)
      def callback_global(x):
          progress_global.setValue(x * 100)
          QApplication.processEvents()
      callback_global(0)
      manips = []
      for i, video_path in enumerate(self.selected_videos):
          callback_global(i / float(len(self.selected_videos)))
          progress = QProgressDialog('Shifting ' + video_path, 'Abort', 0, 100, self)
          progress.setAutoClose(True)
          progress.setMinimumDuration(0)
          def callback(x):
              progress.setValue(x * 100)
              QApplication.processEvents()
          project_from = Project(os.path.dirname(self.selected_videos[i]))
          frames = fileloader.load_file(video_path)
          [x_shift_from, y_shift_from] = project_from['origin']
          x_shift = self.x - x_shift_from
          y_shift = y_shift_from - self.y
          shift = [y_shift, x_shift]
          shifted_frames = self.apply_shift(frames, shift, callback)
          # and save to project
          pre_shifted_basename = os.path.splitext(os.path.basename(video_path))[0]
          manip = '_shift_from_' + project_from.name
          manips = manips + [manip]
          path_after = str(os.path.join(self.project.path, pre_shifted_basename+manip) + '.npy')
          fileloader.save_file(path_after, shifted_frames)
          name_after = os.path.splitext(os.path.basename(path_after))[0]
          if path_after in [f['path'] for f in self.project.files]:
              raise FileAlreadyInProjectError(path_after)
          self.project.files.append({
              'name': name_after,
              'path': path_after,
              'type': 'video',
              'manipulations': str([manip])
          })
          self.project.save()
          # self.save_project(path_after, self.project, shifted_frames, manip, 'video')
          self.refresh_all_list(self.project, self.list_shifted, manips)
      callback_global(1)

  def refresh_all_list(self, project, video_list, last_manips_to_display=['All']):
      video_list.model().clear()
      for f in project.files:
          if f['type'] != 'ref_frame':
              continue
          video_list.model().appendRow(QStandardItem(f['name']))
      for f in project.files:
          if f['type'] != 'video':
              continue
          if 'All' in last_manips_to_display:
              video_list.model().appendRow(QStandardItem(f['name']))
          elif f['manipulations'] != []:
              if ast.literal_eval(f['manipulations'])[-1] in last_manips_to_display:
                  video_list.model().appendRow(QStandardItem(f['name']))
      # video_list.setCurrentIndex(video_list.model().index(0, 0))

  def save_project(self, video_path, project, frames, manip, file_type):
      name_before, ext = os.path.splitext(os.path.basename(video_path))
      file_before = [files for files in project.files if files['name'] == name_before]
      assert (len(file_before) == 1)
      file_before = file_before[0]

      name_after = str(name_before + '_' + manip)
      path = str(os.path.join(project.path, name_after) + '.npy')
      if frames is not None:
          if os.path.isfile(path):
              os.remove(path)
          np.save(path, frames)
      if not file_before['manipulations'] == []:
          project.files.append({
              'path': path,
              'type': file_type,
              'source_video': video_path,
              'manipulations': str(ast.literal_eval(file_before['manipulations']) + [manip]),
              'name': name_after
          })
      else:
          project.files.append({
              'path': path,
              'type': file_type,
              'source_video': video_path,
              'manipulations': str([manip]),
              'name': name_after
          })
      project.save()

  def apply_shift(self, frames, shift, progress_callback):
      shifted_frames = []
      for frame_no, frame in enumerate(frames):
          progress_callback(frame_no / float(len(frames)))
          shifted_frames.append(ird.transform_img(frame, tvec=shift))
      progress_callback(1)
      return np.array(shifted_frames)

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
    def __init__(self, project, plugin_position):
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
