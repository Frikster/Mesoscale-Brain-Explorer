#!/usr/bin/env python3

import os
import sys
import time

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        f0_source_index_label = 'f0 Source Index'

    class Defaults(WidgetDefault.Defaults):
        f0_source_index_default = []
        manip = 'df-f0'

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)

        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project
        self.video_list2 = QListView()
        self.df_d0_pb = QPushButton('&Compute df over f0')
        self.temp_filter_pb = QPushButton('&Apply Filter')
        self.video_list2_vidpath = ''
        self.video_list2_index = None

        self.video_list2.setModel(QStandardItemModel())
        self.clear()

        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list2.model().appendRow(QStandardItem(f['name']))
        WidgetDefault.__init__(self, project, plugin_position)


    def clear(self):
        self.video_list2.clearSelection()

    def setup_ui(self):
        super().setup_ui()
        self.vbox.addWidget(QLabel('Only if needed: Choose f0 source'))
        self.vbox.addWidget(QLabel('Double click to deselect all'))
        self.video_list2.setStyleSheet('QListView::item { height: 26px; }')
        self.video_list2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.vbox.addWidget(self.video_list2)
        self.vbox.addWidget(self.df_d0_pb)

    def setup_signals(self):
        super().setup_signals()
        self.video_list2.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_f0_video_changed)
        self.video_list2.doubleClicked.connect(self.video_list2.clearSelection)
        self.df_d0_pb.clicked.connect(self.execute_primary_function)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.f0_source_index_label, self.Defaults.f0_source_index_default)
        self.video_list2_index = self.params[self.Labels.f0_source_index_label]
        pfs.refresh_list(self.project, self.video_list2, self.video_list2_index,
                         self.Defaults.list_display_type, self.toolbutton_values)

    def setup_param_signals(self):
        super().setup_param_signals()
        self.video_list2.selectionModel().selectionChanged.connect(self.prepare_video_list2_for_update)

    def prepare_video_list2_for_update(self, selected, deselected):
        val = [v.row() for v in self.video_list2.selectedIndexes()]
        self.update_plugin_params(self.Labels.f0_source_index_label, val)

    def selected_f0_video_changed(self, selected, deselected):
        if len(self.video_list2.selectedIndexes()) < 1:
            return
        index = self.video_list2.selectedIndexes()[0]
        self.video_list2_vidpath = str(os.path.normpath(os.path.join(self.project.path, index.data(Qt.DisplayRole))
                                                        + '.npy'))

    def progress_dialog_abort(self):
        self.global_progress.cancel()
        self.progress.cancel()
        print('ABORT')

    def execute_primary_function(self, input_paths=None):
        if not input_paths:
            if not self.selected_videos:
                return
            else:
                selected_videos = self.selected_videos
        else:
            selected_videos = input_paths

        self.global_progress = QProgressDialog('Total Progress Computing df/f0 for Selection', 'Abort', 0, 100, self)
        self.global_progress.canceled.connect(self.progress_dialog_abort)
        self.global_progress.setAutoClose(True)
        self.global_progress.setMinimumDuration(0)
        def global_callback(x):
            self.global_progress.setValue(x * 100)
            QApplication.processEvents()
        output_paths = []
        total = len(selected_videos)
        for i, video_path in enumerate(selected_videos):
            global_callback(i / total)
            self.progress = QProgressDialog('Total Progress Computing df/f0 for ' + video_path, 'Abort', 0, 100, self)
            self.progress.canceled.connect(self.progress_dialog_abort)
            self.progress.setAutoClose(True)
            self.progress.setMinimumDuration(0)
            def callback(x):
                self.progress.setValue(x * 100)
                QApplication.processEvents()
                print(self.progress.wasCanceled())

            start = time.time()
            frames = fileloader.load_file(video_path)
            elapsed_fileloader = (time.time() - start)
            time.time()
            callback(0.01)
            if len(self.video_list2.selectedIndexes()) == 0:
                start = time.time()
                baseline = np.mean(frames, axis=0)
                elapsed_mean = (time.time() - start)
            else:
                start = time.time()
                baseline = np.mean(fileloader.load_file(self.video_list2_vidpath), axis=0)
                elapsed_mean = (time.time() - start)
            callback(0.05)
            start = time.time()
            frames = np.divide(np.subtract(frames, baseline), baseline)
            elapsed_divide = (time.time() - start)
            callback(0.15)
            start = time.time()
            where_are_NaNs = np.isnan(frames)
            elapsed_NaN = (time.time() - start)
            callback(0.19)
            start = time.time()
            frames[where_are_NaNs] = 0
            elapsed_where_are_NaNs = (time.time() - start)
            callback(0.2)
            start = time.time()
            path = pfs.save_project(video_path, self.project, frames, self.Defaults.manip, 'video')
            output_paths = output_paths + [path]
            elapsed_save_project = (time.time() - start)
            callback(0.99)
            start = time.time()
            pfs.refresh_list(self.project, self.video_list,
                             self.params[self.Labels.video_list_indices_label],
                             self.Defaults.list_display_type,
                             self.params[self.Labels.last_manips_to_display_label])
            elapsed_refresh_all_list = (time.time() - start)
            callback(1)
        global_callback(1)
        return output_paths

    def setup_whats_this(self):
        super().setup_whats_this()
        self.video_list2.setWhatsThis("The change in signal from an averaged baseline across frames for each pixel can "
                                      "be computed for all selected image stacks. When calculating dF/F0 you may "
                                      "want the averaged baseline to be computed from a different image stack than for "
                                      "the image stack you are computing dF/F0 for. Typically this will be desired if "
                                      "global signal regression (GSR) is applied before computing dF/F0")
        self.df_d0_pb.setWhatsThis("Click and dF/F0 is computed for all image stacks in the first list, using an "
                                   "averaged baseline from the second list. If no image stack is selected in the "
                                   "second list then the averaged baseline is computed using each individual image "
                                   "stack selected in the first list")

class MyPlugin(PluginDefault):
    def __init__(self, project=None, plugin_position=None):
        self.name = 'Calculate df over f0'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        return True

    def automation_error_message(self):
        return "YOU SHOULD NOT BE ABLE TO SEE THIS"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget())
    w.show()
    app.exec_()
    sys.exit()
