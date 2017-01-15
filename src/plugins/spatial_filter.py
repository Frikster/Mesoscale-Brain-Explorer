#!/usr/bin/env python3

import os
import sys

import PyQt4
import numpy as np
from scipy import ndimage
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy import signal

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView


#import numba as nb
#from numba import cuda
#import parmap

# def temporal_filter_beams(frames):
#     frame_rate = 30
#     f_low = 0.3
#     f_high = 3.0
#     for i in range(frames.shape[1]):
#         for j in range(frames.shape[2]):
#             # print("i: " + str(i))
#             # print("j: " + str(j))
#             frames_beam = np.array(frames[:, i, j])
#             avg_beam = np.mean(frames_beam, axis=0)
#             nyq = frame_rate / 2.0
#             f_low = f_low / nyq
#             f_high = f_high / nyq
#             order = 4
#             rp = 0.1
#             Wn = [f_low, f_high]
#             b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
#             frames = signal.filtfilt(b, a, frames, axis=0)
#             frames_beam += avg_beam
#             frames[:, i, j] = frames_beam
#     return frames

# @cuda.jit(nb.void(nb.uint8[:,:,:],nb.uint8[:,:,:]))
# def temporal_filter_beams_nb(output, frames):
#     frame_rate = 30
#     f_low = 0.3
#     f_high = 3.0
#     i, j = cuda.grid(2)
#     if i < output.shape[1] and j < output.shape[2]:
#         frames_beam = frames[:, i, j]
#         avg_beam = (frames_beam) / float(len(frames_beam))
#         nyq = frame_rate / 2.0
#         f_low = f_low / nyq
#         f_high = f_high / nyq
#         order = 4
#         rp = 0.1
#         Wn = [f_low, f_high]
#         b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
#         frames_beam = signal.filtfilt(b, a, frames_beam, axis=0)
#         frames_beam += avg_beam
#         output[:, i, j] = frames_beam

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)

        # self.temporal_filter_beams_nb = nb.jit(nb.float64[:, :, :]
        #                                   (nb.float64[:, :, :]),
        #                                   nopython=True)(temporal_filter_beams)
        if not project:
            return
        if project == "standalone":
            filenames = QFileDialog.getOpenFileNames(
                self, 'Load data', str(QSettings().value('last_load_data_path')),
                'Video files (*.npy)')
            QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
            self.project = None
        else:
            self.project = project
            # for filename in filenames:
            #     self.project.files.append({
            #         'path': filename,
            #         'type': 'video',
            #         'manipulations': ['chebyshev']
            #     })

        # define ui components and global data
        self.left = QFrame()
        self.right = QFrame()
        self.view = MyGraphicsView(self.project)
        self.video_list = QListView()
        self.kernal_size = QSpinBox()
        self.spat_filter_pb = QPushButton('&Apply Filter')

        self.setup_ui()
        self.selected_videos = []
        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)

        if self.project:
            for f in self.project.files:
                if f['type'] != 'video':
                    continue
                self.video_list.model().appendRow(QStandardItem(f['name']))
        else:
            for f in filenames:
                self.video_list.model().appendRow(QStandardItem(f))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        self.spat_filter_pb.clicked.connect(self.filter_clicked)

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
        vbox.addWidget(QLabel('Kernal Size'))
        self.kernal_size.setMinimum(1)
        self.kernal_size.setValue(8)
        vbox.addWidget(self.kernal_size)
        vbox.addWidget(self.spat_filter_pb)

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

    def filter_clicked(self):
        # todo: other spatial filters could be defined here
        # progress = QProgressDialog('Filtering selection', 'Abort', 0, 100, self)
        # progress.setAutoClose(True)
        # progress.setMinimumDuration(0)
        #
        # def callback(x):
        #     progress.setValue(x * 100)
        #     QApplication.processEvents()
        self.spatial_filter()

    def generate_mean_filter_kernel(self, size):
        kernel = 1.0 / (size * size) * np.array([[1] * size] * size)
        return kernel

    def filter2_test_j(self, frame, kernal_size):
        kernel = self.generate_mean_filter_kernel(kernal_size)
        framek = ndimage.convolve(frame, kernel, mode='constant', cval=0.0)
        return framek

    def spatial_filter(self):
        global_progress = QProgressDialog('Total Progress Filtering Selection', 'Abort', 0, 100, self)
        global_progress.setAutoClose(True)
        global_progress.setMinimumDuration(0)

        def global_callback(x):
            global_progress.setValue(x * 100)
            QApplication.processEvents()

        kernal_size = self.kernal_size.value()
        total = len(self.selected_videos)
        for i, video_path in enumerate(self.selected_videos):
            global_callback(i / total)
            progress = QProgressDialog('Total Progress filtering for ' + video_path, 'Abort', 0, 100, self)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            def callback(x):
                progress.setValue(x * 100)
                QApplication.processEvents()
            frames = fileloader.load_file(video_path)
            self.kernal_size.setMaximum(np.sqrt(frames[0].size))
            for frame_no, frame in enumerate(frames):
                frames[frame_no] = self.filter2_test_j(frame, kernal_size)
                callback(frame_no / len(frames))
            if not self.project:
                filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self, 'Choose save location',
                                                                   str(QSettings().value('last_load_data_path')),
                                                                   filter='*.npy')
                np.save(str(filename), frames)
                msgBox = PyQt4.QtGui.QMessageBox()
                msgBox.setText(str(filename)+" saved")
                msgBox.addButton(PyQt4.QtGui.QMessageBox.Ok)
                msgBox.exec_()
            else:
                pfs.save_project(video_path, self.project, frames, 'spatial-filter', 'video')
                pfs.refresh_all_list(self.project, self.video_list)
            callback(1)
        global_callback(1)

class MyPlugin:
    def __init__(self, project=None):
        self.name = 'Spatial Filter'
        self.widget = Widget(project)

    def run(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget("standalone"))
    w.show()
    app.exec_()
    sys.exit()
