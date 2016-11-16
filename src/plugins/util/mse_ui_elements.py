#!/usr/bin/env python3
import os

import numpy as np
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import fileloader
from .mygraphicsview import MyGraphicsView


class Video_Selector:
    def __init__(self, project, view):
        self.project = project
        self.view = view

    def selected_video_changed(self, selected, deselected):
        if not selected.indexes():
            return

        for index in deselected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
            self.selected_videos = [x for x in self.selected_videos if x != vidpath]
        for index in selected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
        if vidpath not in self.selected_videos and vidpath != 'None':
            self.selected_videos = self.selected_videos + [vidpath]

        self.shown_video_path = str(os.path.join(self.project.path,
                                           selected.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.shown_video_path)
        self.view.show(frame)


class InfoWidget(QFrame):
    def __init__(self, text, parent=None):
        super(InfoWidget, self).__init__(parent)
        self.setup_ui(text)

    def setup_ui(self, text):
        hbox = QHBoxLayout()
        icon = QLabel()
        image = QImage('pics/info.png')
        icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
        hbox.addWidget(icon)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        hbox.addWidget(self.label)
        hbox.addStretch()
        self.setLayout(hbox)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class WarningWidget(QFrame):
    def __init__(self, text, parent=None):
        super(WarningWidget, self).__init__(parent)
        self.setup_ui(text)

    def setup_ui(self, text):
        hbox = QHBoxLayout()
        icon = QLabel()
        image = QImage('pics/delete.png')
        icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
        hbox.addWidget(icon)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        hbox.addWidget(self.label)
        hbox.addStretch()
        self.setLayout(hbox)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class CheckableComboBox(QtGui.QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

class PlayerDialog(QDialog):
  def __init__(self, project, filename, parent=None):
    super(PlayerDialog, self).__init__(parent)
    self.project = project
    self.setup_ui()

    self.fp = np.load(filename, mmap_mode='r')
    self.slider.setMaximum(len(self.fp)-1)
    self.show_frame(0)

  def show_frame(self, frame_num):
    frame = self.fp[frame_num]
    self.label_frame.setText(str(frame_num) + ' / ' + str(len(self.fp)-1))
    self.view.show(frame)

  def setup_ui(self):
    vbox = QVBoxLayout()
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    hbox = QHBoxLayout()
    self.slider = QSlider(Qt.Horizontal)
    self.slider.valueChanged.connect(self.slider_moved)
    hbox.addWidget(self.slider)
    self.label_frame = QLabel('- / -')
    hbox.addWidget(self.label_frame)
    vbox.addLayout(hbox)
    self.setLayout(vbox)

  def slider_moved(self, value):
    self.show_frame(value)