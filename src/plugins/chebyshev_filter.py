#!/usr/bin/env python3

import os, sys
import numpy as np
from scipy import signal

import PyQt4
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util.mygraphicsview import MyGraphicsView
from .util import fileloader

#import numba as nb
#from numba import cuda
import uuid
import psutil


def cheby_filter(frames, low_limit, high_limit, frame_rate):
    nyq = frame_rate / 2.0
    low_limit = low_limit / nyq
    high_limit = high_limit / nyq
    order = 4
    rp = 0.1
    Wn = [low_limit, high_limit]

    b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
    print("Filtering...")
    frames = signal.filtfilt(b, a, frames, axis=0)
    # frames = parmap.map(filt, frames.T, b, a)
    # for i in range(frames.shape[-1]):
    #    frames[:, i] = 'signal.filtfilt(b, a, frames[:, i])
    print("Done!")
    return frames

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

        self.setup_ui()
        self.listview.setModel(QStandardItemModel())
        self.listview.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_video_changed)

        if self.project:
            for f in self.project.files:
                if f['type'] != 'video':
                    continue
                self.listview.model().appendRow(QStandardItem(f['path']))
        else:
            for f in filenames:
                self.listview.model().appendRow(QStandardItem(f))
        self.listview.setCurrentIndex(self.listview.model().index(0, 0))
        self.temp_filter_pb.clicked.connect(self.temporal_filter)


    def setup_ui(self):
        hbox = QHBoxLayout()

        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.listview = QListView()
        self.listview.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.listview)

        vbox.addWidget(QLabel('Low Bandpass (Hz)'))
        self.f_low = QDoubleSpinBox()
        self.f_low.setMinimum(0.0)
        self.f_low.setValue(0.3)
        vbox.addWidget(self.f_low)
        vbox.addWidget(QLabel('High Bandpass (Hz)'))
        self.f_high = QDoubleSpinBox()
        self.f_high.setMinimum(0.0)
        self.f_high.setValue(3.0)
        vbox.addWidget(self.f_high)

        vbox.addWidget(QLabel('Frame Rate (Hz)'))
        self.frame_rate = QSpinBox()
        self.frame_rate.setMinimum(0.0)
        self.frame_rate.setMaximum(1000)
        self.frame_rate.setValue(30)
        vbox.addWidget(self.frame_rate)

        self.temp_filter_pb = QPushButton('&Apply Filter')
        vbox.addWidget(self.temp_filter_pb)

        vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        hbox.addLayout(vbox)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

    def selected_video_changed(self, selection):
        if not selection.indexes():
            return
        self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole))
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)


    def temporal_filter(self):
        assert(self.f_low.value() < self.f_high.value())
        frame_rate = self.frame_rate.value()
        f_low = self.f_low.value()
        f_high = self.f_high.value()

        #frames_mmap = np.load(self.video_path, mmap_mode='c')
        #out = np.empty([frames_mmap.shape[1], frames_mmap.shape[2]])
        #temporal_filter_beams_nb(out, frames_mmap)
        #frames = np.array(frames_mmap)

        frames = fileloader.load_file(self.video_path)
        avg_frames = np.mean(frames, axis=0)
        frames = self.cheby_filter(frames, f_low, f_high, frame_rate)
        frames += avg_frames

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
            # todo: solve issue where rerunning this will overwrite any previous 'cheby.npy'
            #path = os.path.join(self.project.path, 'cheby' + '.npy')
            path = self.video_path + 'cheby' + '.npy'
            np.save(path, frames)
            self.project.files.append({
                'path': path,
                'type': 'video',
                'source_video': self.video_path,
                'manipulations': ['chebyshev']
            })
            self.project.save()

class MyPlugin:
    def __init__(self, project=None):
        self.name = 'Chebyshev fiflter'
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
