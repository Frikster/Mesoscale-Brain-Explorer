#!/usr/bin/env python3
import os

import imreg_dft as ird
import numpy as np
import qtutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        pass

    class Defaults(WidgetDefault.Defaults):
        list_display_type = ['ref_frame', 'video']
        manip = 'align'

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project

        # define widgets and data
        # self.selected_videos = []
        # self.shown_video_path = None
        # self.left = QFrame()
        # self.right = QFrame()
        # self.view = MyGraphicsView(self.project)
        # self.video_list = mue.Video_Selector()
        # list_of_manips = pfs.get_list_of_project_manips(self.project)
        # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        # self.video_list = MyListView()
        self.ref_no_min = QSpinBox()
        self.ref_no_max = QSpinBox()
        self.main_button = QPushButton('&Align')
        self.ref_button = QPushButton('&Compute Reference Frame')
        self.reference_frame = None
        WidgetDefault.__init__(self, project, plugin_position)

        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)

        # self.setup_ui()
        # if isinstance(plugin_position, int):
        #     self.params = project.pipeline[self.plugin_position]
        #     assert (self.params['name'] == 'alignment')
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
        # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        # vbox.addWidget(self.toolbutton)
        # vbox.addWidget(QLabel('Choose video:'))
        # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        # vbox.addWidget(self.video_list)

        def min_handler(max_of_min):
            self.ref_no_min.setMaximum(max_of_min)
        def max_handler(min_of_max):
            self.ref_no_max.setMinimum(min_of_max)
        self.ref_no_min.valueChanged[int].connect(max_handler)
        self.ref_no_max.valueChanged[int].connect(min_handler)
        hbox = QHBoxLayout()
        self.vbox.addWidget(QLabel('Set range averaged over to compute reference frame'))
        self.ref_no_min.setMinimum(0)
        self.ref_no_min.setMaximum(405)
        self.ref_no_min.setValue(400)
        hbox.addWidget(self.ref_no_min)
        to = QLabel('to')
        to.setAlignment(Qt.AlignCenter)
        hbox.addWidget(to)
        self.ref_no_max.setMaximum(100000)
        self.ref_no_max.setValue(405)
        hbox.addWidget(self.ref_no_max)
        self.vbox.addLayout(hbox)

        self.vbox.addWidget(self.main_button)
        self.vbox.addWidget(self.ref_button)
        # self.right.setLayout(self.vbox)

        # splitter = QSplitter(Qt.Horizontal)
        # splitter.setHandleWidth(3)
        # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        # splitter.addWidget(self.left)
        # splitter.addWidget(self.right)
        # hbox_global = QHBoxLayout()
        # hbox_global.addWidget(splitter)
        # self.setLayout(hbox_global)

        # hbox.addLayout(vbox)
        # hbox.setStretch(0, 1)
        # hbox.setStretch(1, 0)
        # self.setLayout(hbox)

    # def refresh_video_list_via_combo_box(self, trigger_item=None):
    #     pfs.refresh_video_list_via_combo_box(self, Defaults.list_display_type, trigger_item)
    #
    # def selected_video_changed(self, selected, deselected):
    #     pfs.selected_video_changed_multi(self, selected, deselected)

    # def setup_params(self, reset=False):
    #     if len(self.params) == 1 or reset:
    #         self.update_plugin_params(Labels.video_list_indices_label, Defaults.video_list_indices_default)
    #         self.update_plugin_params(Labels.last_manips_to_display_label, Defaults.last_manips_to_display_default)
    #     self.video_list_indices = self.params[Labels.video_list_indices_label]
    #     self.toolbutton_values = self.params[Labels.last_manips_to_display_label]
    #     manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
    #                               if self.toolbutton.itemText(i) in self.params[Labels.last_manips_to_display_label]]
    #     for item in manip_items:
    #         item.setCheckState(Qt.Checked)
    #     not_checked = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
    #                    if self.toolbutton.itemText(i) not in self.params[Labels.last_manips_to_display_label]]
    #     for item in not_checked:
    #         item.setCheckState(Qt.Unchecked)
            # The following works but doesn't set the brain image to pyqtgraph scene.
        #ref_frame_indices = self.params[Labels.reference_frame_index_label]
        # if len(ref_frame_indices) > 1:
        #     theQIndexObjects = [self.video_list.model().createIndex(rowIndex, 0) for rowIndex in
        #                         ref_frame_indices]
        #     for Qindex in theQIndexObjects:
        #         self.video_list.selectionModel().select(Qindex, QItemSelectionModel.Select)
        # else:
        #     self.video_list.setCurrentIndex(self.video_list.model().index(ref_frame_indices[0], 0))

    # self.video_list.currentChanged(self.video_list.model().index(
        #     self.params[Labels.reference_frame_index_label][0], 0), self.video_list.model().index(0, 0))
        #self.video_list.currentChanged()
        #self.video_list.setCurrentIndex(self.params[Labels.reference_frame_index_label])

    # def setup_param_signals(self):
    #     self.video_list.selectionModel().selectionChanged.connect(self.prepare_video_list_for_update)
    #     self.toolbutton.activated.connect(self.prepare_toolbutton_for_update)
        # This gets you the name and index connected to whatever function
        # self.video_list.active_vid_changed[str, int].connect(
        #     functools.partial(self.prepare_video_list_for_update, Labels.reference_frame_index_label))

    # def prepare_video_list_for_update(self, selected, deselected):
    #     val = [v.row() for v in self.video_list.selectedIndexes()]
    #     if not val:
    #         val = Defaults.video_list_indices_default
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
    #
    # def update_plugin_params(self, key, val):
    #     pfs.update_plugin_params(self, key, val)

    def setup_signals(self):
        super().setup_signals()
        self.main_button.clicked.connect(self.execute_primary_function)
        self.ref_button.clicked.connect(self.compute_ref_frame)


    def compute_ref_frame(self):
        if not self.selected_videos:
            qtutil.critical("No files selected")
            return

        if len(self.selected_videos) > 1:
            qtutil.critical("Select only one file to compute the reference frame from")
            return

        if 'ref_frame' in self.selected_videos[0]:
            qtutil.critical("Cannot compute reference frame of reference frame")
            return

        ref_no_min = self.ref_no_min.value()
        ref_no_max = self.ref_no_max.value()

        # find size, assuming all files in project have the same size
        frames_mmap = np.load(self.shown_video_path, mmap_mode='c')
        reference_frame_range = np.array(frames_mmap[ref_no_min:ref_no_max])
        self.reference_frame = np.mean(reference_frame_range, axis=0)

        frame_no, h, w = frames_mmap.shape
        # summed_reference_frame = np.zeros((h, w))
        # divide_frame = np.full((h, w), len(self.selected_videos))
        # for video_path in self.selected_videos:
        #     frames_mmap = np.load(video_path, mmap_mode='c')
        #     reference_frame = np.array(frames_mmap[ref_no])
        #     summed_reference_frame = np.add(summed_reference_frame, reference_frame)
        #
        # summed_reference_frame = np.divide(summed_reference_frame, divide_frame)
        self.reference_frame = np.reshape(self.reference_frame, (1, h, w))
        pfs.save_project(self.selected_videos[0], self.project, self.reference_frame, 'ref_frame', 'ref_frame')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])

    def execute_primary_function(self, input_files=None):
        if not input_files:
            filenames = self.selected_videos
            reference_frame_file = [file for file in filenames if file[-13:] == 'ref_frame.npy']
        else:
            filenames = input_files
            reference_frame_file = self.selected_videos
            if len([file for file in reference_frame_file if file[-13:] == 'ref_frame.npy']) != \
                    len(reference_frame_file):
                qtutil.critical("Please only select a single reference frame for each alignment plugin used."
                          "Automation will now close.")
                return

        if len(reference_frame_file) == 0:
            qtutil.critical("No reference frame selected")
            return
        if len(reference_frame_file) > 1:
            qtutil.critical("Multiple reference frames selected. Please only pick one")
            return
        assert(len(reference_frame_file) == 1)
        reference_frame_file = reference_frame_file[0]

        assert ('ref_frame' in reference_frame_file)
        reference_frame = np.load(reference_frame_file)[0]
        not_reference_frames = [file for file in filenames if file[-13:] != 'ref_frame.npy']
        return self.align_videos(not_reference_frames, reference_frame)

        # for filename in filenames:
        #     if filename in [f['path'] for f in self.project.files]:
        #         continue
        #     name, ext = os.path.splitext(os.path.basename(filename))
        #     f = {
        #         'name': name,
        #         'path': filename,
        #         'type': 'video',
        #         'manipulations': 'align'
        #     }
        #     self.project.files.append(f)
        # self.project.save()

    def compute_shifts(self, template_frame, frames, progress_shifts):
        def callback_shifts(x):
            progress_shifts.setValue(x * 100)
            QApplication.processEvents()
        results = []
        for i, frame in enumerate(frames):
            if progress_shifts.wasCanceled():
                return
            callback_shifts(i / float(len(frames)))
            results = results + [ird.similarity(template_frame, frame)['timg']]
        callback_shifts(1)
        return results

    def apply_shifts(self, frames, shifts, progress_callback):
        shifted_frames = []
        for frame_no, shift in enumerate(shifts):
            tvec = shift["tvec"]
            angle = shift["angle"]
            progress_callback(frame_no / float(len(shifts)))
            frame = frames[frame_no]
            shifted_frames.append(ird.transform_img(frame, tvec=tvec, angle=angle))
        progress_callback(1)
        return shifted_frames

    def align_videos(self, filenames, reference_frame):
        """Return filenames of generated videos"""
        progress_global = QProgressDialog('Total progress aligning all files', 'Abort', 0, 100, self)
        progress_global.setAutoClose(True)
        progress_global.setMinimumDuration(0)
        def callback_global(x):
            progress_global.setValue(x * 100)
            QApplication.processEvents()
        callback_global(0)
        ret_filenames = []

        for i, filename in enumerate(filenames):
            callback_global(i / float(len(filenames)))
            progress_shifts = QProgressDialog('Finding best shifts for ' + filename, 'Abort', 0, 100, self)
            progress_shifts.setAutoClose(True)
            progress_shifts.setMinimumDuration(0)
            progress_apply = QProgressDialog('Applying shifts for ' + filename, 'Abort', 0, 100, self)
            progress_apply.setAutoClose(True)
            progress_apply.setMinimumDuration(0)
            def callback_apply(x):
                progress_apply.setValue(x * 100)
                QApplication.processEvents()
            frames = fileloader.load_file(filename)
            shifted_frames = self.compute_shifts(reference_frame, frames, progress_shifts)
            if progress_shifts.wasCanceled():
                return
            #shifted_frames = self.apply_shifts(frames, shifts, callback_apply)
            pfs.save_project(filename, self.project, shifted_frames, self.Defaults.manip, 'video')
            pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                             self.Defaults.list_display_type, self.toolbutton_values)
            # path = os.path.join(os.path.dirname(filename), 'aligned_' + \
            #                     os.path.basename(filename))
            # np.save(path, shifted_frames)
            name_before, ext = os.path.splitext(os.path.basename(filename))
            name_after = fileloader.get_name_after_no_overwrite(name_before, self.Defaults.manip, self.project)
            path = str(os.path.join(self.project.path, name_after) + '.npy')
            ret_filenames.append(path)
        callback_global(1)
        return ret_filenames


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Alignment'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        filenames = self.widget.selected_videos
        reference_frame_file = [file for file in filenames if file[-13:] == 'ref_frame.npy']
        if len(reference_frame_file) == 1:
            return True
        else:
            return False

    def automation_error_message(self):
        return "Please select one reference frame for each alignment plugin used"


