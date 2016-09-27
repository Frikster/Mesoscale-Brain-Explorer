#!/usr/bin/env python3

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util import filter_jeff
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView, MyProgressDialog
from .util.gradient import GradientLegend

from .util import fileloader

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math


class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
            return
        self.project = project
        self.setup_ui()

        self.video_path = None
        self.open_dialogs = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list.model().appendRow(QStandardItem(f['name']))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    def setup_ui(self):
        hbox = QHBoxLayout()
        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list = MyListView()
        vbox.addWidget(self.video_list)

        max_cut_off = 5000
        vbox.addWidget(QLabel('Cut off from start'))
        self.left_cut_off = QSpinBox()
        self.left_cut_off.setMinimum(0)
        self.left_cut_off.setMaximum(max_cut_off)
        self.left_cut_off.setValue(0)
        vbox.addWidget(self.left_cut_off)
        vbox.addWidget(QLabel('Cut off from end'))
        self.right_cut_off = QSpinBox()
        self.right_cut_off.setMinimum(0)
        self.right_cut_off.setMaximum(max_cut_off)
        self.right_cut_off.setValue(0)
        vbox.addWidget(self.right_cut_off)

        pb = QPushButton('Cut off frames')
        pb.clicked.connect(self.cut_off)
        vbox.addWidget(pb)

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

    def cut_off(self):
        if not self.video_path:
            return

        frames_mmap = np.load(self.video_path, mmap_mode='c')
        cut_off_start = self.left_cut_off.value()
        cut_off_end = self.right_cut_off.value()

        frames = np.array(frames_mmap[cut_off_start:len(frames_mmap)-cut_off_end])

        # todo: solve issue where rerunning this will overwrite any previous 'cut_off.npy'
        # path = os.path.join(self.project.path, 'roi' + '.npy')
        path = self.video_path + 'cut_off' + '.npy'
        np.save(path, frames)
        self.project.files.append({
            'path': path,
            'type': 'video',
            'source_video': self.video_path,
            'manipulations': ['cut_off']
        })
        self.project.save()


class MyPlugin:
    def __init__(self, project):
        self.name = 'Cut off'
        self.widget = Widget(project)

    def run(self):
        pass
