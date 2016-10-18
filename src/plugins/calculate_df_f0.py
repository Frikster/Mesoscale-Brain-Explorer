#!/usr/bin/env python3

import os, sys
import numpy as np
from scipy import signal

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader

import uuid
import psutil

from .util import project_functions as pfs

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)

        if not project:
            return
        self.project = project
        self.setup_ui()

        self.listview.setModel(QStandardItemModel())
        self.listview.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_video_changed)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.listview.model().appendRow(QStandardItem(f['name']))
        self.listview.setCurrentIndex(self.listview.model().index(0, 0))
        self.df_d0_pb.clicked.connect(self.calculate_df_f0)


    def setup_ui(self):
        hbox = QHBoxLayout()

        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.listview = QListView()
        self.listview.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.listview)

        self.df_d0_pb = QPushButton('&Compute df over f0')
        vbox.addWidget(self.df_d0_pb)

        vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        hbox.addLayout(vbox)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

    def selected_video_changed(self, selection):
        if not selection.indexes():
            return
        self.video_path = str(os.path.join(self.project.path,
                                           selection.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)

    def calculate_df_f0(self):
        frames = fileloader.load_file(self.video_path)
        baseline = np.mean(frames, axis=0)
        frames = np.divide(np.subtract(frames, baseline), baseline)
        where_are_NaNs = np.isnan(frames)
        frames[where_are_NaNs] = 0
        pfs.save_project(self.video_path, self.project, frames, 'df_d0', 'video')

class MyPlugin:
    def __init__(self, project=None):
        self.name = 'Calculate df over f0'
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
