#!/usr/bin/env python3

import os
import sys
import functools

import PyQt4
import numpy as np
from scipy import ndimage
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy import signal

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

#import numba as nb
#from numba import cuda
#import parmap

# def temporal_filter_beams(frames):
#     frame_rate = 30
#     f_low = 0.3
#     f_high = 3.0
#     for i in range(frames.shape[1]):
#         for j in range(frames.shape[2]):
#             # print("i: " + str(i))
#             # print("j: " + str(j))
#             frames_beam = np.array(frames[:, i, j])
#             avg_beam = np.mean(frames_beam, axis=0)
#             nyq = frame_rate / 2.0
#             f_low = f_low / nyq
#             f_high = f_high / nyq
#             order = 4
#             rp = 0.1
#             Wn = [f_low, f_high]
#             b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
#             frames = signal.filtfilt(b, a, frames, axis=0)
#             frames_beam += avg_beam
#             frames[:, i, j] = frames_beam
#     return frames

# @cuda.jit(nb.void(nb.uint8[:,:,:],nb.uint8[:,:,:]))
# def temporal_filter_beams_nb(output, frames):
#     frame_rate = 30
#     f_low = 0.3
#     f_high = 3.0
#     i, j = cuda.grid(2)
#     if i < output.shape[1] and j < output.shape[2]:
#         frames_beam = frames[:, i, j]
#         avg_beam = (frames_beam) / float(len(frames_beam))
#         nyq = frame_rate / 2.0
#         f_low = f_low / nyq
#         f_high = f_high / nyq
#         order = 4
#         rp = 0.1
#         Wn = [f_low, f_high]
#         b, a = signal.cheby1(order, rp, Wn, 'bandpass', analog=False)
#         frames_beam = signal.filtfilt(b, a, frames_beam, axis=0)
#         frames_beam += avg_beam
#         output[:, i, j] = frames_beam



class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        kernal_size_label = "Kernal Size"

    class Defaults(WidgetDefault.Defaults):
        kernal_size_default = 8

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)

        # self.temporal_filter_beams_nb = nb.jit(nb.float64[:, :, :]
        #                                   (nb.float64[:, :, :]),
        #                                   nopython=True)(temporal_filter_beams)
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
            # for filename in filenames:
            #     self.project.files.append({
            #         'path': filename,
            #         'type': 'video',
            #         'manipulations': ['chebyshev']
            #     })

        # define ui components and global data
        # self.left = QFrame()
        # self.right = QFrame()
        # self.view = MyGraphicsView(self.project)
        # self.video_list = QListView()
        self.kernal_size = QSpinBox()
        self.spat_filter_pb = QPushButton('&Apply Filter')
        WidgetDefault.__init__(self, project, plugin_position)

        # self.video_list_indices = []
        # self.toolbutton_values = []
        # self.selected_videos = []
        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.selectionModel().selectionChanged[QItemSelection,
        #                                                   QItemSelection].connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)

        # if self.project:
        #     for f in self.project.files:
        #         if f['type'] != 'video':
        #             continue
        #         self.video_list.model().appendRow(QStandardItem(f['name']))
        # else:
        #     for f in filenames:
        #         self.video_list.model().appendRow(QStandardItem(f))

        # self.setup_ui()
        # if isinstance(plugin_position, int):
        #     self.params = project.pipeline[self.plugin_position]
        #     assert (self.params['name'] == 'spatial_filter')
        #     self.setup_param_signals()
        #     try:
        #         self.setup_params()
        #     except:
        #         self.setup_params(reset=True)
        #     pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
        #                      Defaults.list_display_type, self.toolbutton_values)


    # def video_triggered(self, index):
    #     pfs.video_triggered(self, index)

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
        self.vbox.addWidget(QLabel(self.Labels.kernal_size_label))
        self.kernal_size.setMinimum(1)
        self.kernal_size.setValue(8)
        self.vbox.addWidget(self.kernal_size)
        self.vbox.addWidget(self.spat_filter_pb)

        # self.right.setLayout(self.vbox)
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
        self.spat_filter_pb.clicked.connect(self.execute_primary_function)


    def setup_params(self, reset=False):
        super().setup_params()
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.kernal_size_label, self.Defaults.kernal_size_default)
        self.kernal_size.setValue(self.params[self.Labels.kernal_size_label])

        #     self.update_plugin_params(Labels.video_list_indices_label, Defaults.video_list_indices_default)
        #     self.update_plugin_params(Labels.last_manips_to_display_label, Defaults.last_manips_to_display_default)
        # self.video_list_indices = self.params[Labels.video_list_indices_label]
        # self.toolbutton_values = self.params[Labels.last_manips_to_display_label]
        # manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
        #                           if self.toolbutton.itemText(i) in self.params[Labels.last_manips_to_display_label]]
        # for item in manip_items:
        #     item.setCheckState(Qt.Checked)
        # not_checked = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
        #                if self.toolbutton.itemText(i) not in self.params[Labels.last_manips_to_display_label]]
        # for item in not_checked:
        #     item.setCheckState(Qt.Unchecked)


    def setup_param_signals(self):
        super().setup_param_signals()
        self.kernal_size.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.kernal_size_label))
        # self.video_list.selectionModel().selectionChanged.connect(self.prepare_video_list_for_update)
        # self.toolbutton.activated.connect(self.prepare_toolbutton_for_update)

    # def prepare_video_list_for_update(self, selected, deselected):
    #     val = [v.row() for v in self.video_list.selectedIndexes()]
    #     self.update_plugin_params(Labels.video_list_indices_label, val)
    #
    # def prepare_toolbutton_for_update(self, trigger_item):
    #     val = self.params[Labels.last_manips_to_display_label]
    #     selected = self.toolbutton.itemText(trigger_item)
    #     if selected not in val:
    #         val = val + [selected]
    #         if trigger_item != 0:
    #             val = [manip for manip in val if manip not in Defaults.last_manips_to_display_default]
    #     else:
    #         val = [manip for manip in val if manip != selected]
    #
    #     self.update_plugin_params(Labels.last_manips_to_display_label, val)


    # def update_plugin_params(self, key, val):
    #     pfs.update_plugin_params(self, key, val)



    # def refresh_video_list_via_combo_box(self, trigger_item=None):
    #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
    #
    # def selected_video_changed(self, selected, deselected):
    #     pfs.selected_video_changed_multi(self, selected, deselected)

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

    # def filter_clicked(self):
    #     # progress = QProgressDialog('Filtering selection', 'Abort', 0, 100, self)
    #     # progress.setAutoClose(True)
    #     # progress.setMinimumDuration(0)
    #     #
    #     # def callback(x):
    #     #     progress.setValue(x * 100)
    #     #     QApplication.processEvents()
    #     self.spatial_filter()

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
