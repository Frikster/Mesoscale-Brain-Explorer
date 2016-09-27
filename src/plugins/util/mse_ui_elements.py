#!/usr/bin/env python3
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtCore
from . import fileloader

class Video_Selector:
    def __init__(self, project, view):
        self.project = project
        self.view = view

    def selected_video_changed(self, selection):
        if not selection.indexes():
            return
        self.video_path = str(os.path.join(self.project.path,
                                           selection.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)