#!/usr/bin/env python3

import functools
import os
import sys

import PyQt4
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy import ndimage

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        kernal_size_label = "Kernel Size"

    class Defaults(WidgetDefault.Defaults):
        kernal_size_default = 8

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        if project == "standalone":
            filenames = QFileDialog.getOpenFileNames(
                self, 'Load data', str(QSettings().value('last_load_data_path')),
                'Video files (*.npy)')
            QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
            self.project = None
        else:
            self.project = project
        self.kernal_size = QSpinBox()
        self.spat_filter_pb = QPushButton('&Apply Filter')
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        self.vbox.addWidget(QLabel(self.Labels.kernal_size_label))
        self.kernal_size.setMinimum(1)
        self.kernal_size.setValue(8)
        self.vbox.addWidget(self.kernal_size)
        self.vbox.addWidget(self.spat_filter_pb)

    def setup_signals(self):
        super().setup_signals()
        self.spat_filter_pb.clicked.connect(self.execute_primary_function)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.kernal_size_label, self.Defaults.kernal_size_default)
        self.kernal_size.setValue(self.params[self.Labels.kernal_size_label])

    def setup_param_signals(self):
        super().setup_param_signals()
        self.kernal_size.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.kernal_size_label))

    def generate_mean_filter_kernel(self, size):
        kernel = 1.0 / (size * size) * np.array([[1] * size] * size)
        return kernel

    def filter2_test_j(self, frame, kernal_size):
        kernel = self.generate_mean_filter_kernel(kernal_size)
        framek = ndimage.convolve(frame, kernel, mode='constant', cval=0.0)
        return framek

    def execute_primary_function(self):
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
            frames_original = fileloader.load_file(video_path)
            frames = np.zeros((frames_original.shape[0], frames_original.shape[1], frames_original.shape[2]))
            self.kernal_size.setMaximum(np.sqrt(frames[0].size))
            for frame_no, frame_original in enumerate(frames_original):
                frames[frame_no] = self.filter2_test_j(frame_original, kernal_size)
                callback(frame_no / len(frames))
            frames = frames_original - frames

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
                pfs.refresh_list(self.project, self.video_list,
                                 self.params[self.Labels.video_list_indices_label],
                                 self.Defaults.list_display_type,
                                 self.params[self.Labels.last_manips_to_display_label])
            callback(1)
        global_callback(1)

    def setup_whats_this(self):
        super().setup_whats_this()
        self.kernal_size.setWhatsThis("The size (in pixels) of the square mean filter that wil be convolved "
                                      "with each selected image stack for spatial filtering. A larger kernel size "
                                      "entails more blurring and therefore filtering to emphasize larger features"
                                      "and de-emphasize smaller ones. "
                                      "\nNote that we have "
                                      "found a kernel size of 8 highlights blood vessels in Ai94 mice well enough "
                                      "such that a frame in the spatially filtered stack can be used as the reference "
                                      "frame in the alignment plugin in 256x256 image stacks so as to align all image "
                                      "stacks to the blood vessels. "
                                      "Kernel size 4 can be used for 128x128 image stacks.")

class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Spatial Filter'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

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
