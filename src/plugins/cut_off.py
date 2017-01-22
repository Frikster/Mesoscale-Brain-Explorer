#!/usr/bin/env python3

import os

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView


class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
            return
        self.project = project

        # define ui components and global data
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.left = QFrame()
        self.right = QFrame()
        self.left_cut_off = QSpinBox()
        self.right_cut_off = QSpinBox()

        self.setup_ui()

        self.open_dialogs = []
        self.selected_videos = []
        self.shown_video_path = None

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list.model().appendRow(QStandardItem(f['name']))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    def video_triggered(self, index):
        pfs.video_triggered(self, index)

    def setup_ui(self):
        vbox_view = QVBoxLayout()
        vbox_view.addWidget(self.view)
        self.left.setLayout(vbox_view)

        vbox = QVBoxLayout()
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        vbox.addWidget(self.toolbutton)
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)
        max_cut_off = 5000
        vbox.addWidget(QLabel('Cut off from start'))
        self.left_cut_off.setMinimum(0)
        self.left_cut_off.setMaximum(max_cut_off)
        self.left_cut_off.setValue(0)
        vbox.addWidget(self.left_cut_off)
        vbox.addWidget(QLabel('Cut off from end'))
        self.right_cut_off.setMinimum(0)
        self.right_cut_off.setMaximum(max_cut_off)
        self.right_cut_off.setValue(0)
        vbox.addWidget(self.right_cut_off)
        pb = QPushButton('Cut off frames')
        pb.clicked.connect(self.cut_off)
        vbox.addWidget(pb)
        self.right.setLayout(vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

    # def selected_video_changed(self, selection):
    #     if not selection.indexes():
    #         return
    #     self.video_path = str(os.path.join(self.project.path,
    #                                        selection.indexes()[0].data(Qt.DisplayRole))
    #                           + '.npy')
    #     frame = fileloader.load_reference_frame(self.video_path)
    #     self.view.show(frame)
    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    # def selected_video_changed(self, selected, deselected):
    #     if not selected.indexes():
    #         return
    #
    #     for index in deselected.indexes():
    #         vidpath = str(os.path.join(self.project.path,
    #                                  index.data(Qt.DisplayRole))
    #                           + '.npy')
    #         self.selected_videos = [x for x in self.selected_videos if x != vidpath]
    #     for index in selected.indexes():
    #         vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
    #         if vidpath not in self.selected_videos and vidpath != 'None':
    #             self.selected_videos = self.selected_videos + [vidpath]
    #
    #     self.shown_video_path = str(os.path.join(self.project.path,
    #                                        selected.indexes()[0].data(Qt.DisplayRole))
    #                           + '.npy')
    #     frame = fileloader.load_reference_frame(self.shown_video_path)
    #     self.view.show(frame)

    def cut_off(self):
        if not self.selected_videos:
            return

        progress_global = QProgressDialog('Creating cut offs...', 'Abort', 0, 100, self)
        progress_global.setAutoClose(True)
        progress_global.setMinimumDuration(0)

        def global_callback(x):
            progress_global.setValue(x * 100)
            QApplication.processEvents()

        total = len(self.selected_videos)
        for global_i, video_path in enumerate(self.selected_videos):
            global_callback(global_i / total)
            frames_mmap = np.load(video_path, mmap_mode='c')
            cut_off_start = self.left_cut_off.value()
            cut_off_end = self.right_cut_off.value()

            progress = QProgressDialog('Creating cut off for ' + video_path, 'Abort', 0, 100, self)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)

            def callback(x):
                progress.setValue(x * 100)
                QApplication.processEvents()

            num_frames = len(frames_mmap)-cut_off_end-cut_off_start
            name_before, ext = os.path.splitext(os.path.basename(video_path))
            name_after = str(name_before + '_' + 'cut-off')
            path = str(os.path.join(self.project.path, name_after) + '.npy')
            fileloader.save_file(path, np.empty((num_frames, len(frames_mmap[0]), len(frames_mmap[1]))))
            frames = np.load(path, mmap_mode='r+')
            for i, frame in enumerate(frames_mmap[cut_off_start:len(frames_mmap)-cut_off_end]):
                callback(i / float(len(frames_mmap)))
                frames[i] = frame[:, :]
            callback(1)
            # frames = np.array(frames_mmap[cut_off_start:len(frames_mmap)-cut_off_end])
            pfs.save_project(video_path, self.project, None, 'cut-off', 'video')
            pfs.refresh_all_list(self.project, self.video_list)
        global_callback(1)


class MyPlugin:
    def __init__(self, project, plugin_position):
        self.name = 'Cut off'
        self.widget = Widget(project)

    def run(self):
        pass
