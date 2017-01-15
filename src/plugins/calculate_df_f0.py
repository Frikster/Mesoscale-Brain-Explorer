#!/usr/bin/env python3

import sys, os, time

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView


class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)

        if not project:
            return
        self.project = project

        # define ui components and global data
        self.left = QFrame()
        self.right = QFrame()
        self.view = MyGraphicsView(self.project)
        self.video_list = QListView()
        self.video_list2 = QListView()
        self.df_d0_pb = QPushButton('&Compute df over f0')
        self.temp_filter_pb = QPushButton('&Apply Filter')

        self.setup_ui()
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list.model().appendRow(QStandardItem(f['name']))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

        self.video_list2.setModel(QStandardItemModel())
        self.video_list2.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_f0_video_changed)
        self.video_list2.doubleClicked.connect(self.video_list2.clearSelection)
        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list2.model().appendRow(QStandardItem(f['name']))
        self.video_list2.setCurrentIndex(self.video_list2.model().index(0, 0))
        self.df_d0_pb.clicked.connect(self.calculate_df_f0)

    def clear(self):
        self.video_list2.clearSelection()
        # listwidget.setSelected(False)
        # for i in range(listwidget.count()):
        #     item = listwidget.item(i)
        #     listwidget.setItemSelected(item, False)

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
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        vbox.addWidget(self.video_list)
        vbox.addWidget(QLabel('Only if needed: Choose f0 source'))
        vbox.addWidget(QLabel('Double click to deselect all'))
        self.video_list2.setStyleSheet('QListView::item { height: 26px; }')
        self.video_list2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        vbox.addWidget(self.video_list2)
        vbox.addWidget(self.df_d0_pb)
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

    def selected_f0_video_changed(self, selected, deselected):
        if len(self.video_list2.selectedIndexes()) < 1:
            return
        index = self.video_list2.selectedIndexes()[0]
        self.video_list2_vidpath = str(os.path.normpath(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy'))
        print('')

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

    def progress_dialog_abort(self):
        self.global_progress.cancel()
        self.progress.cancel()
        print('ABORT')

    def calculate_df_f0(self):
        self.global_progress = QProgressDialog('Total Progress Computing df/f0 for Selection', 'Abort', 0, 100, self)
        self.global_progress.canceled.connect(self.progress_dialog_abort)
        self.global_progress.setAutoClose(True)
        self.global_progress.setMinimumDuration(0)
        def global_callback(x):
            self.global_progress.setValue(x * 100)
            QApplication.processEvents()
        total = len(self.selected_videos)
        for i, video_path in enumerate(self.selected_videos):
            global_callback(i / total)
            self.progress = QProgressDialog('Total Progress Computing df/f0 for ' + video_path, 'Abort', 0, 100, self)
            self.progress.canceled.connect(self.progress_dialog_abort)
            self.progress.setAutoClose(True)
            self.progress.setMinimumDuration(0)
            def callback(x):
                self.progress.setValue(x * 100)
                QApplication.processEvents()
                print(self.progress.wasCanceled())

            start = time.time()
            frames = fileloader.load_file(video_path)
            elapsed_fileloader = (time.time() - start)
            time.time()
            callback(0.01)
            if len(self.video_list2.selectedIndexes()) == 0:
                start = time.time()
                baseline = np.mean(frames, axis=0)
                elapsed_mean = (time.time() - start)
            else:
                start = time.time()
                baseline = np.mean(fileloader.load_file(self.video_list2_vidpath), axis=0)
                elapsed_mean = (time.time() - start)
            callback(0.05)
            start = time.time()
            frames = np.divide(np.subtract(frames, baseline), baseline)
            elapsed_divide = (time.time() - start)
            callback(0.15)
            start = time.time()
            where_are_NaNs = np.isnan(frames)
            elapsed_NaN = (time.time() - start)
            callback(0.19)
            start = time.time()
            frames[where_are_NaNs] = 0
            elapsed_where_are_NaNs = (time.time() - start)
            callback(0.2)
            start = time.time()
            pfs.save_project(video_path, self.project, frames, 'df-f0', 'video')
            elapsed_save_project = (time.time() - start)
            callback(0.99)
            start = time.time()
            pfs.refresh_all_list(self.project, self.video_list)
            elapsed_refresh_all_list = (time.time() - start)
            callback(1)
        global_callback(1)

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
