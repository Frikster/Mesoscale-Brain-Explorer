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

# import numba as nb
# from numba import cuda
# import parmap

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

        # self.temporal_filter_beams_nb = nb.jit(nb.float64[:, :, :]
        #                                   (nb.float64[:, :, :]),
        #                                   nopython=True)(temporal_filter_beams)
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
        self.f_low = QDoubleSpinBox()
        self.f_high = QDoubleSpinBox()
        self.frame_rate = QSpinBox()
        self.temp_filter_pb = QPushButton('&Apply Filter')

        # self.setup_ui()
        # self.selected_videos = []
        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.selectionModel().selectionChanged[QItemSelection,
        #                                                   QItemSelection].connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)

        # todo: remake independent
        # if self.project:
        #     for f in self.project.files:
        #         if f['type'] != 'video':
        #             continue
        #         self.video_list.model().appendRow(QStandardItem(f['name']))
        # else:
        #     for f in filenames:
        #         self.video_list.model().appendRow(QStandardItem(f))

        # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        # self.temp_filter_pb.clicked.connect(self.filter_clicked)
        WidgetDefault.__init__(self, project, plugin_position)

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

        # self.right.setLayout(vbox)
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
    #     self.temporal_filter()

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
        #    frames[:, i] = 'signal.filtfilt(b, a, frames[:, i])
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
        #frames_mmap = np.load(self.video_path, mmap_mode='c')
        #out = np.empty([frames_mmap.shape[1], frames_mmap.shape[2]])
        #temporal_filter_beams_nb(out, frames_mmap)
        #frames = np.array(frames_mmap)
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
            avg_frames = np.mean(frames, axis=0)
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
            # name_before, ext = os.path.splitext(os.path.basename(video_path))
            # name_after = fileloader.get_name_after_no_overwrite(name_before, self.Defaults.manip, self.project)
            # path = str(os.path.join(self.project.path, name_after) + '.npy')
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
