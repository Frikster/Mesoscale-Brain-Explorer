#!/usr/bin/env python3

import os

import numpy as np
import psutil
import qtutil
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        pass

    class Defaults(WidgetDefault.Defaults):
        manip = 'evoked-avg'

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.avg_button = QPushButton('Generate Evoked Average')

        # self.plugin_position = plugin_position
        # self.project = project
        # self.setup_ui()
        # self.update_tables()
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        # vbox = QVBoxLayout()
        # self.table1 = FileTable()
        # self.table1.setSelectionMode(QAbstractItemView.MultiSelection)
        # vbox.addWidget(self.table1)
        self.vbox.addWidget(self.avg_button)
        # self.table2 = FileTable()
        # self.vbox.addWidget(self.table2)
        #self.setLayout(self.vbox)

    def setup_signals(self):
        super().setup_signals()
        self.avg_button.clicked.connect(self.execute_primary_function)


    # def update_tables(self):
    #     videos = [f for f in self.project.files if f['type'] == 'video']
    #     self.table1.setModel(FileTableModel(videos))
    #     videos = [
    #         f for f in self.project.files
    #         if 'manipulations' in f and 'trigger-avg' in f['manipulations']
    #         ]
    #     self.table2.setModel(FileTableModel(videos))

    def execute_primary_function(self, input_paths=None):
        if not input_paths:
            if not self.selected_videos:
                return
            else:
                selected_videos = self.selected_videos
        else:
            selected_videos = input_paths

        progress_global = QProgressDialog('Creating evoked average...', 'Abort', 0, 100, self)
        progress_global.setAutoClose(True)
        progress_global.setMinimumDuration(0)
        def global_callback(x):
            progress_global.setValue(x * 100)
            QApplication.processEvents()

        filenames = selected_videos
        if len(filenames) < 2:
            qtutil.warning('Select multiple files to average.')
            return
        stacks = [np.load(f, mmap_mode='r') for f in filenames]
        lens = [len(stacks[x]) for x in range(len(stacks))]
        min_lens = np.min(lens)

        breadth = stacks[0].shape[1]
        length = stacks[0].shape[2]

        trig_avg = np.empty([min_lens, length, breadth])
        for frame_index in range(min_lens):
            global_callback(frame_index / min_lens)
            frames_to_avg = [stacks[stack_index][frame_index]
                             for stack_index in range(len(stacks))]
            frames_to_avg = np.array(frames_to_avg)
            avg = np.mean(frames_to_avg, axis=0)
            trig_avg[frame_index] = avg
        global_callback(1)
        manip = self.Defaults.manip + '_' + str(len(filenames))
        output_path = pfs.save_project(filenames[0], self.project, trig_avg, manip, 'video')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])
        return output_path
        # self.update_tables()


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Evoked Average'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        self.summed_filesize = 0
        for path in self.widget.selected_videos:
            self.summed_filesize = self.summed_filesize + os.path.getsize(path)
        self.available = list(psutil.virtual_memory())[1]
        if self.summed_filesize > self.available:
            return False
        return True

    def automation_error_message(self):
        return "Not enough memory. All files to be averaged together are of size ~"+str(self.summed_filesize) +\
               " and available memory is: " + str(self.available)

