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
import tifffile as tiff

from .util import fileloader, fileconverter
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
    self.origin_label = QLabel('Origin:')
    self.setup_ui()

    self.listview.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'video':
        self.listview.model().appendRow(QStandardItem(f['path']))

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    self.listview.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.listview)

    self.setLayout(vbox)
    #
    # hbox = QVBoxLayout()
    # hbox.addWidget(mue.WarningWidget('Warning. This application has not yet been memory optimized for conversion.'
    #                                  ' We advise you only import files no larger than 1/4 of your memory'))
    # pb = QPushButton('New Video')
    # pb.clicked.connect(self.new_video)
    # hbox.addWidget(pb)
    #
    # vbox.addLayout(hbox)
    # vbox.addStretch()


    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def custom_butt_clicked(self):
        print('Do custom stuff. Coding required.')

    def new_video(self):
        filenames = QFileDialog.getOpenFileNames(
            self, 'Load images', QSettings().value('last_load_data_path'),
            'Video files (*.npy *.tif *.raw)')
        if not filenames:
            return
        QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
        self.import_files(filenames)

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
