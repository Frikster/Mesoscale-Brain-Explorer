#!/usr/bin/env python3
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui, QtCore
from . import fileloader

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

class Dialog_01(QtGui.QMainWindow):
    def __init__(self):
        super(QtGui.QMainWindow,self).__init__()
        myQWidget = QtGui.QWidget()
        myBoxLayout = QtGui.QVBoxLayout()
        myQWidget.setLayout(myBoxLayout)
        self.setCentralWidget(myQWidget)
        self.ComboBox = CheckableComboBox()
        for i in range(3):
            self.ComboBox.addItem("Combobox Item " + str(i))
            item = self.ComboBox.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Unchecked)
        self.toolbutton = QtGui.QToolButton(self)
        self.toolbutton.setText('Select Categories ')
        self.toolmenu = QtGui.QMenu(self)
        for i in range(3):
            action = self.toolmenu.addAction("Category " + str(i))
            action.setCheckable(True)
        self.toolbutton.setMenu(self.toolmenu)
        self.toolbutton.setPopupMode(QtGui.QToolButton.InstantPopup)
        myBoxLayout.addWidget(self.toolbutton)
        myBoxLayout.addWidget(self.ComboBox)

