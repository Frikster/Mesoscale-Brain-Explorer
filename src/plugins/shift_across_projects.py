#!/usr/bin/env python3

import os
import sys
import traceback
import numpy as np
from shutil import copyfile
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

sys.path.append('..')
import qtutil
from project import Project
import tifffile as tiff

from .util.mygraphicsview import MyGraphicsView
from .util import mse_ui_elements as mue
from .util import project_functions as pfs

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
    self.list_all = QListView()
    self.list_shifted = QListView()
    self.origin_label = QLabel('Origin:')
    self.left = QFrame()
    self.right = QFrame()
    self.setup_ui()

    self.list_all.setModel(QStandardItemModel())
    self.list_shifted.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'shifted':
        self.list_all.model().appendRow(QStandardItem(f['path']))

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
    self.list_all.setStyleSheet('QListView::item { height: 26px; }')
    self.list_all.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.list_all)
    vbox.addWidget(qtutil.separator())
    pb = QPushButton('Align selected data to this project')
    pb.clicked.connect(self.new_json)
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

  def refresh_video_list_via_combo_box(self, trigger_item=None):
    pfs.refresh_video_list_via_combo_box(self, trigger_item)

  def selected_video_changed(self, selected, deselected):
    pfs.selected_video_changed_multi(self, selected, deselected)

  def new_json(self):
    filenames = QFileDialog.getExistingDirectory(
        self, 'Load images', QSettings().value('last_load_data_path'),
        'Video files (*.json)')
    if not filenames:
        return
    QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
    for json_path in filenames:
        if os.path.splitext(json_path)[1] != '.json':
            qtutil.critical(json_path + 'is not a json file. Skipping.')
            continue
        self.project_list = self.project_list + Project(json_path)
        print('loading...')
        #self.import_files(filenames)

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
