#!/usr/bin/env python3

import sys, os, time

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        f0_source_index_label = 'f0 Source Index'

    class Defaults(WidgetDefault.Defaults):
        f0_source_index_default = None
        manip = 'df_f0'

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)

        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project

        # define ui components and global data
        # self.left = QFrame()
        # self.right = QFrame()
        # self.view = MyGraphicsView(self.project)
        # self.video_list = QListView()
        self.video_list2 = QListView()
        self.df_d0_pb = QPushButton('&Compute df over f0')
        self.temp_filter_pb = QPushButton('&Apply Filter')
        self.video_list2_vidpath = ''
        self.video_list2_index = None

        # self.setup_ui()
        # self.selected_videos = []
        #
        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.selectionModel().selectionChanged[QItemSelection,
        #                                                   QItemSelection].connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)
        # for f in project.files:
        #     if f['type'] != 'video':
        #         continue
        #     self.video_list.model().appendRow(QStandardItem(f['name']))
        # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

        self.video_list2.setModel(QStandardItemModel())
        self.clear()

        for f in project.files:
            if f['type'] != 'video':
                continue
            self.video_list2.model().appendRow(QStandardItem(f['name']))
        WidgetDefault.__init__(self, project, plugin_position)


    def clear(self):
        self.video_list2.clearSelection()
        # listwidget.setSelected(False)
        # for i in range(listwidget.count()):
        #     item = listwidget.item(i)
        #     listwidget.setItemSelected(item, False)

    def setup_ui(self):
        super().setup_ui()
        # vbox_view = QVBoxLayout()
        # vbox_view.addWidget(self.view)
        # self.left.setLayout(vbox_view)
        #
        # vbox = QVBoxLayout()
        # list_of_manips = pfs.get_list_of_project_manips(self.project)
        # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        # vbox.addWidget(self.toolbutton)
        # vbox.addWidget(QLabel('Choose video:'))
        # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # vbox.addWidget(self.video_list)
        self.vbox.addWidget(QLabel('Only if needed: Choose f0 source'))
        self.vbox.addWidget(QLabel('Double click to deselect all'))
        self.video_list2.setStyleSheet('QListView::item { height: 26px; }')
        self.video_list2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.vbox.addWidget(self.video_list2)
        self.vbox.addWidget(self.df_d0_pb)
        # self.right.setLayout(vbox)
        #
        # splitter = QSplitter(Qt.Horizontal)
        # splitter.setHandleWidth(3)
        # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        # splitter.addWidget(self.left)
        # splitter.addWidget(self.right)
        # hbox_global = QHBoxLayout()
        # hbox_global.addWidget(splitter)
        # self.setLayout(hbox_global)

    def setup_signals(self):
        super().setup_signals()
        self.video_list2.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_f0_video_changed)
        self.video_list2.doubleClicked.connect(self.video_list2.clearSelection)
        self.df_d0_pb.clicked.connect(self.execute_primary_function)

    def setup_params(self, reset=False):
        super().setup_params()
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

    # def selected_video_changed(self, selected, deselected):
    #     if not selected.indexes():
    #         return
    #
    #     for index in deselected.indexes():
    #         vidpath = str(os.path.join(self.project.path,
    #                                  index.data(Qt.DisplayRole))
    #                           + '.npy')
    #         self.selected_videos = [x for x in self.selected_videos if x != vidpath]
    #     for index in selected.indexes():
    #         vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
    #         if vidpath not in self.selected_videos and vidpath != 'None':
    #             self.selected_videos = self.selected_videos + [vidpath]
    #
    #     self.shown_video_path = str(os.path.join(self.project.path,
    #                                        selected.indexes()[0].data(Qt.DisplayRole))
    #                           + '.npy')
    #     frame = fileloader.load_reference_frame(self.shown_video_path)
    #     self.view.show(frame)

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
