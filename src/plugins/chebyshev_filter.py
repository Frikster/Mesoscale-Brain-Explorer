#!/usr/bin/env python

import os, sys
import numpy as np
from scipy import signal

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView
from util import fileloader

import uuid
import psutil

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
            self.listview.model().appendRow(QStandardItem(f['path']))
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
        self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)

    def temporal_filter(self):
        import matplotlib.pylab as plt
        frames = fileloader.load_file(self.video_path)
        frame_rate = self.frame_rate.value()
        f_high = self.f_low.value()
        f_low = self.f_high.value()

        avg_frames = np.mean(frames, axis=0)
        frames = self.cheby_filter(frames, f_low, f_high, frame_rate)
        frames += avg_frames

        # todo: solve issue where rerunning this will overwrite any previous 'cheby.npy'
        path = os.path.join(self.project.path, 'cheby' + '.npy')
        np.save(path, frames)
        self.project.files.append({
            'path': path,
            'type': 'video',
            'source_video': self.video_path,
            'manipulations': ['chebyshev']
        })

    def cheby_filter(self, frames, low_limit, high_limit, frame_rate):
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
        #    frames[:, i] = signal.filtfilt(b, a, frames[:, i])
        print("Done!")
        return frames

class MyPlugin:
    def __init__(self, project=None):
        self.name = 'Chebyshev filter'
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
