#!/usr/bin/env python

import os, sys
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
from scipy import signal

from pyqtgraph.Qt import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.viewboxcustom import MultiRoiViewBox, ImageAnalysisViewBox

import h5py
import psutil

class Widget(QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        hbox = QHBoxLayout()
        left = QVBoxLayout()
        right = QFrame()
        right.setFrameShadow(QFrame.Raised)
        right.setFrameShape(QFrame.Panel)
        right.setContentsMargins(10, 0, 1, 0)
        right.setMinimumWidth(200)

        lt_right = QVBoxLayout()
        lt_right.setContentsMargins(8, 8, 8, 8)

        lt_right.addWidget(QLabel('Low Bandpass (Hz)'))
        self.f_high = QDoubleSpinBox()
        self.f_high.setMinimum(0.0)
        self.f_high.setValue(0.3)
        lt_right.addWidget(self.f_high)
        lt_right.addWidget(QLabel('High Bandpass (Hz)'))
        self.f_low = QDoubleSpinBox()
        self.f_low.setMinimum(0.0)
        self.f_low.setValue(3.0)
        lt_right.addWidget(self.f_low)

        lt_right.addWidget(QLabel('Frame Rate (Hz)'))
        self.frame_rate = QSpinBox()
        self.frame_rate.setMinimum(0.0)
        self.frame_rate.setMaximum(1000)
        self.frame_rate.setValue(30)
        lt_right.addWidget(self.frame_rate)

        butt_file_load = QPushButton('&Load File')
        lt_right.addWidget(butt_file_load)

        temp_filter = QPushButton('&Apply Filter')
        lt_right.addWidget(temp_filter)

        lt_right.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        pb_done = QPushButton('&Done')
        lt_right.addWidget(pb_done)

        right.setLayout(lt_right)
        self.setup_left_interface(left)

        hbox.addLayout(left)
        hbox.addWidget(right)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

        # setup connections
        butt_file_load.clicked.connect(self.load_file)
        temp_filter.clicked.connect(self.temporal_filter)

        # define class variables
        self.reference_frames_dict = {}
        self.filename = None

    def setup_left_interface(self, left_frame_layout):
        """ Initialise the PyQtGraph Interface """

        # Left frame contents
        self.viewMain = pg.GraphicsView()
        self.viewMain.setMinimumSize(200, 200)
        left_frame_layout.addWidget(self.viewMain)

        l = QtGui.QGraphicsGridLayout()

        self.viewMain.centralWidget.setLayout(l)
        l.setHorizontalSpacing(0)
        l.setVerticalSpacing(0)

        self.vb = MultiRoiViewBox(lockAspect=True, enableMenu=True)

        l.addItem(self.vb, 0, 1)
        self.xScale = pg.AxisItem(orientation='bottom', linkView=self.vb)
        self.xScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>X</span> <i>Width</i>", units="mm")
        l.addItem(self.xScale, 1, 1)

        self.yScale = pg.AxisItem(orientation='left', linkView=self.vb)
        self.yScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>Y</span> <i>Height</i>", units='mm')
        l.addItem(self.yScale, 0, 0)

        self.vb.enableAutoRange()

    def load_file(self):
        file_names = QtGui.QFileDialog.getOpenFileNames(self, self.tr("Load images"), QtCore.QDir.currentPath())
        filename = str(file_names[0])
        self.filename = filename

        # todo: Complete HDF5 integration. Remove .npy
        frames = np.load(filename)
        h5f = h5py.File('C:/Users/Cornelis Dirk Haupt/Downloads/cheby_input.h5', 'w')
        h5f.create_dataset('default', data=frames, maxshape=(None, frames.shape[1], frames.shape[2]))
        h5f.close()

        h5f = h5py.File('C:/Users/Cornelis Dirk Haupt/Downloads/cheby_output.h5', 'w')
        h5f.create_dataset('default', data=frames, maxshape=(None, frames.shape[1], frames.shape[2]))
        h5f.close()

        img_arr = frames[0]
        img_arr = img_arr.swapaxes(0, 1)
        if img_arr.ndim == 2:
            img_arr = img_arr[:, ::-1]
        elif img_arr.ndim == 3:
            img_arr = img_arr[:, ::-1, :]

        self.vb.showImage(img_arr)

    def temporal_filter(self):
        # Collect all user-defined variables (and variables immediately inferred from user-selections)
        # fileName = str(self.sidePanel.imageFileList.currentItem().text())
        frame_rate = self.frame_rate.value()
        f_high = self.f_high.value()
        f_low = self.f_low.value()
        # dtype_string = str(self.sidePanel.dtypeValue.text())

        # todo: complete hdf5 integration
        h5f_in = h5py.File('C:/Users/Cornelis Dirk Haupt/Downloads/cheby_input.h5', 'r+')
        h5f_out = h5py.File('C:/Users/Cornelis Dirk Haupt/Downloads/cheby_output.h5', 'r+')

        for x in range(0, 256):
            for y in range(0, 256):
                frames = h5f_in['default'][:, x, y]

                # Compute df/d0 and save to file
                avg_frames = np.mean(frames, axis=0)
                frames = self.cheby_filter(frames, f_low, f_high, frame_rate)
                frames += avg_frames

                h5f_out['default'][:, x, y] = frames

        h5f_in.close()
        h5f_out.close()

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
    def __init__(self):
        self.name = 'Chebyshev filter'
        self.widget = Widget()

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
