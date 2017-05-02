#!/usr/bin/env python3

import functools
import os
import sys

import PyQt4
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy import signal

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        f_low_label = 'Low Bandpass (Hz)'
        f_high_label = 'High Bandpass (Hz)'
        frame_rate_label = 'Frame Rate (Hz)'

    class Defaults(WidgetDefault.Defaults):
        f_low_default = 0.3
        f_high_default = 3.0
        frame_rate_default = 30
        manip = "temporal-filter"

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        if project == "standalone":
            filenames = QFileDialog.getOpenFileNames(
                self, 'Load data', str(QSettings().value('last_load_data_path')),
                'Video files (*.npy)')
            QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))
            self.project = None
        else:
            self.project = project
        self.f_low = QDoubleSpinBox()
        self.f_high = QDoubleSpinBox()
        self.frame_rate = QSpinBox()
        self.temp_filter_pb = QPushButton('&Apply Filter')
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        def min_handler(max_of_min):
            self.f_low.setMaximum(max_of_min)
        def max_handler(min_of_max):
            self.f_high.setMinimum(min_of_max)
        self.f_low.valueChanged[float].connect(max_handler)
        self.f_high.valueChanged[float].connect(min_handler)
        self.vbox.addWidget(QLabel(self.Labels.f_low_label))
        self.f_low.setMinimum(0.0)
        self.f_low.setValue(self.Defaults.f_low_default)
        self.vbox.addWidget(self.f_low)
        self.vbox.addWidget(QLabel(self.Labels.f_high_label))
        self.f_high.setMinimum(0.0)
        self.f_high.setValue(self.Defaults.f_high_default)
        self.vbox.addWidget(self.f_high)
        self.vbox.addWidget(QLabel(self.Labels.frame_rate_label))
        self.frame_rate.setMinimum(0.0)
        self.frame_rate.setMaximum(100000)
        self.frame_rate.setValue(30)
        self.vbox.addWidget(self.frame_rate)
        self.vbox.addWidget(self.temp_filter_pb)

    def setup_signals(self):
        super().setup_signals()
        self.temp_filter_pb.clicked.connect(self.execute_primary_function)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.f_low_label, self.Defaults.f_low_default)
            self.update_plugin_params(self.Labels.f_high_label, self.Defaults.f_high_default)
            self.update_plugin_params(self.Labels.frame_rate_label, self.Defaults.frame_rate_default)
        self.f_low.setValue(self.params[self.Labels.f_low_label])
        self.f_high.setValue(self.params[self.Labels.f_high_label])
        self.frame_rate.setValue(self.params[self.Labels.frame_rate_label])

    def setup_param_signals(self):
        super().setup_param_signals()
        self.f_low.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.f_low_label))
        self.f_high.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.f_high_label))
        self.frame_rate.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.frame_rate_label))

    def cheby_filter(self, frames, low_limit, high_limit, frame_rate):
        nyq = frame_rate / 2.0
        low_limit = low_limit / nyq
        high_limit = high_limit / nyq
        order = 4
        rp = 0.1 # Ripple in the passband. Maximum allowable ripple
        Wn = [low_limit, high_limit]

        b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
        print("Filtering...")
        frames = signal.filtfilt(b, a, frames, axis=0)
        # non-working parallized version
        # def filt(pixel, b, a):
        #     return signal.filtfilt(b, a, pixel)
        # frames = parmap.map(filt, frames.T, b, a)
        # for i in range(frames.shape[-1]):
        #    frames[:, i] = signal.filtfilt(b, a, frames[:, i])
        print("Done!")
        return frames

    def execute_primary_function(self, input_paths=None):
        if not input_paths:
            if not self.selected_videos:
                return
            else:
                selected_videos = self.selected_videos
        else:
            selected_videos = input_paths

        global_progress = QProgressDialog('Total Progress Filtering Selection', 'Abort', 0, 100, self)
        global_progress.setAutoClose(True)
        global_progress.setMinimumDuration(0)

        def global_callback(x):
            global_progress.setValue(x * 100)
            QApplication.processEvents()
        assert(self.f_low.value() < self.f_high.value())
        frame_rate = self.frame_rate.value()
        f_low = self.f_low.value()
        f_high = self.f_high.value()
        output_paths = []
        total = len(selected_videos)
        for i, video_path in enumerate(selected_videos):
            global_callback(i / total)
            progress = QProgressDialog('Total Progress filtering for ' + video_path, 'Abort', 0, 100, self)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            def callback(x):
                progress.setValue(x * 100)
                QApplication.processEvents()
            callback(0.01)
            frames = fileloader.load_file(video_path)
            callback(0.1)
            avg_frames = np.mean(frames, axis=0, dtype=frames.dtype)
            callback(0.2)
            frames = self.cheby_filter(frames, f_low, f_high, frame_rate)
            callback(0.9)
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
                path = pfs.save_project(video_path, self.project, frames, 'temporal-filter', 'video')
                pfs.refresh_list(self.project, self.video_list,
                                 self.params[self.Labels.video_list_indices_label],
                                 self.Defaults.list_display_type,
                                 self.params[self.Labels.last_manips_to_display_label])
            callback(1)
            output_paths = output_paths + [path]
        global_callback(1)
        return output_paths

    def setup_whats_this(self):
        super().setup_whats_this()
        self.temp_filter_pb.setWhatsThis("A forward-backward filter with Chebyshev type I digital and "
                                                          "analog filter design, and maximum of 0.1 allowable ripple "
                                                          "in the passband is applied using the parameters above."
                                                          "\n"
                                                          "Select multiple image stacks to apply the same filter to "
                                                          "all selected image stacks.")

class MyPlugin(PluginDefault):
    def __init__(self, project=None, plugin_position=None):
        self.name = 'Temporal Filter'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        return True

    def automation_error_message(self):
        return "YOU SHOULD NOT BE ABLE TO SEE THIS MESSAGE"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget("standalone"))
    w.show()
    app.exec_()
    sys.exit()
