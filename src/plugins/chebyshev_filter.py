#!/usr/bin/env python

import os, sys
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt

from pyqtgraph.Qt import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.ViewBoxCustom import MultiRoiViewBox, ImageAnalysisViewBox


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

        lt_right.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        pb_done = QPushButton('&Done')
        lt_right.addWidget(pb_done)

        right.setLayout(lt_right)
        self.setup_left_interface(left)

        # self.pixmap = QPixmap('../data/flower2.jpg')
        # self.pic = QLabel()
        # self.pic.setStyleSheet('background-color: black')
        # self.pic.setPixmap(self.pixmap)
        # left.addWidget(self.pic)

        hbox.addLayout(left)
        hbox.addWidget(right)

        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)

        self.setLayout(hbox)

        # setup connections
        butt_file_load.clicked.connect(self.load_file)

        # define class variables
        self.reference_frames_dict = {}

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
        frames = np.load(filename)




class MyPlugin:
    def __init__(self):
        self.name = 'Plugin'
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