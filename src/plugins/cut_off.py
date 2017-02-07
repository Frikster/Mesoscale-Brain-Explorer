#!/usr/bin/env python3

import functools
import os

import numpy as np
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        start_cut_off_label = 'Cut off from start'
        end_cut_off_label = 'Cut off from end'

    class Defaults(WidgetDefault.Defaults):
        start_cut_off_default = 0
        end_cut_off_default = 0
        manip = "cut-off"

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.left_cut_off = QSpinBox()
        self.right_cut_off = QSpinBox()
        self.main_button = QPushButton('Cut off frames')
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        max_cut_off = 50000
        self.vbox.addWidget(QLabel(self.Labels.start_cut_off_label))
        self.left_cut_off.setMinimum(0)
        self.left_cut_off.setMaximum(max_cut_off)
        self.left_cut_off.setValue(self.Defaults.start_cut_off_default)
        self.vbox.addWidget(self.left_cut_off)
        self.vbox.addWidget(QLabel(self.Labels.end_cut_off_label))
        self.right_cut_off.setMinimum(0)
        self.right_cut_off.setMaximum(max_cut_off)
        self.right_cut_off.setValue(self.Defaults.end_cut_off_default)
        self.vbox.addWidget(self.right_cut_off)
        self.vbox.addWidget(self.main_button)

    def setup_signals(self):
        super().setup_signals()
        self.main_button.clicked.connect(self.execute_primary_function)

    def setup_params(self, reset=False):
        super().setup_params()
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.start_cut_off_label, self.Defaults.start_cut_off_default)
            self.update_plugin_params(self.Labels.end_cut_off_label, self.Defaults.end_cut_off_default)
        self.left_cut_off.setValue(self.params[self.Labels.start_cut_off_label])
        self.right_cut_off.setValue(self.params[self.Labels.end_cut_off_label])

    def setup_param_signals(self):
        super().setup_param_signals()
        self.left_cut_off.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.start_cut_off_label))
        self.right_cut_off.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                       self.Labels.end_cut_off_label))

    def execute_primary_function(self, input_paths=None):
        if not input_paths:
            if not self.selected_videos:
                return
            else:
                selected_videos = self.selected_videos
        else:
            selected_videos = input_paths

        progress_global = QProgressDialog('Creating cut offs...', 'Abort', 0, 100, self)
        progress_global.setAutoClose(True)
        progress_global.setMinimumDuration(0)

        def global_callback(x):
            progress_global.setValue(x * 100)
            QApplication.processEvents()

        output_paths = []
        total = len(selected_videos)
        for global_i, video_path in enumerate(selected_videos):
            global_callback(global_i / total)
            frames_mmap = np.load(video_path, mmap_mode='c')
            cut_off_start = self.left_cut_off.value()
            cut_off_end = self.right_cut_off.value()

            progress = QProgressDialog('Creating cut off for ' + video_path, 'Abort', 0, 100, self)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)

            def callback(x):
                progress.setValue(x * 100)
                QApplication.processEvents()

            num_frames = len(frames_mmap)-cut_off_end-cut_off_start
            name_before, ext = os.path.splitext(os.path.basename(video_path))
            name_after = fileloader.get_name_after_no_overwrite(name_before, self.Defaults.manip, self.project)
            path = str(os.path.join(self.project.path, name_after) + '.npy')
            fileloader.save_file(path, np.empty((num_frames, len(frames_mmap[0]), len(frames_mmap[1]))))
            frames = np.load(path, mmap_mode='r+')
            for i, frame in enumerate(frames_mmap[cut_off_start:len(frames_mmap)-cut_off_end]):
                callback(i / float(len(frames_mmap)))
                frames[i] = frame[:, :]
            callback(1)
            output_paths = output_paths + [path]
            # frames = np.array(frames_mmap[cut_off_start:len(frames_mmap)-cut_off_end])
            pfs.save_project(video_path, self.project, None, self.Defaults.manip, 'video')
            pfs.refresh_list(self.project, self.video_list,
                             self.params[self.Labels.video_list_indices_label],
                             self.Defaults.list_display_type,
                             self.params[self.Labels.last_manips_to_display_label])
        global_callback(1)
        return output_paths

class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Cut off'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        lc = self.widget.left_cut_off.value()
        rc = self.widget.right_cut_off.value()
        return lc > 0 or rc > 0

    def automation_error_message(self):
        return "Cut off plugin cannot have both cut off paramaters set to 0."
