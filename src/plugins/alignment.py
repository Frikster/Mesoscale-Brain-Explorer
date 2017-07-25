#!/usr/bin/env python3

import functools
import math
import os

import imreg_dft as ird
import numpy as np
import qtutil
from PyQt4.QtCore import *
from PyQt4.QtCore import QPointF
from PyQt4.QtGui import *
from scipy import ndimage

from .util import file_io
from .util import project_functions as pfs
from .util.custom_qt_items import ImageStackListView
from .util.custom_qt_items import MyTableWidget
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        kernal_size_label = "Kernel Size"
        crop_percentage_sb_label = "Crop Percentage"
        shift_table_col1 = "1) "
        window_name = "Crop Window"

    class Defaults(WidgetDefault.Defaults):
        list_display_type = ['ref_frame', 'video']
        manip = 'align'
        secondary_manip = 'ref_frame'
        apply_scaling_default = True
        apply_rotation_default = False
        x_shift_default = 0.0
        y_shift_default = 0.0
        rotation_shift_default = 0.0
        scale_shift_default = 1.0
        crop_percentage_sb_default = 20

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project

        self.kernal_size = QSpinBox()
        self.crop_percentage_sb = QSpinBox()
        self.ref_no_min = QSpinBox()
        self.ref_no_max = QSpinBox()
        self.ref_button = QPushButton('Compute &Reference Frame')

        self.ref_no = QSpinBox()
        self.rotation_checkbox = QCheckBox("Apply Rotation")
        self.scaling_checkbox = QCheckBox("Apply Scaling")
        self.shift_btn = QPushButton('Compute &Shift')

        self.list_to_apply_shifts_to = ImageStackListView()
        self.list_to_apply_shifts_to.setModel(QStandardItemModel())
        pfs.refresh_list(self.project, self.list_to_apply_shifts_to, [],
                         ['video'])
        self.shift_table_data = {}
        self.shift_table = MyTableWidget()
        self.shift_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.tvec_x_sb = QDoubleSpinBox()
        # self.tvec_y_sb = QDoubleSpinBox()
        # self.rotation_sb = QDoubleSpinBox()
        # self.scale_sb = QDoubleSpinBox()
        # self.use_shift_checkbox = QCheckBox("Use This Shift for Alignment")
        # self.reference_frame = None
        self.align_btn = QPushButton('&Align')
        WidgetDefault.__init__(self, project, plugin_position)
        self.shift_table_col1 = [os.path.splitext(os.path.basename(x))[0] for x in self.selected_videos if
                                 self.Defaults.secondary_manip not in x]
        self.update_crop_border()


    def setup_ui(self):
        super().setup_ui()
        self.vbox.addStretch()
        # self.vbox.addWidget(qtutil.separator())

        self.vbox.addWidget(QLabel(self.Labels.kernal_size_label))
        self.kernal_size.setMinimum(1)
        self.kernal_size.setValue(8)
        self.vbox.addWidget(self.kernal_size)
        self.crop_percentage_sb.setMaximum(50)
        self.vbox.addWidget(QLabel(self.Labels.crop_percentage_sb_label))
        self.vbox.addWidget(self.crop_percentage_sb)
        def min_handler(max_of_min):
            self.ref_no_min.setMaximum(max_of_min)
        def max_handler(min_of_max):
            self.ref_no_max.setMinimum(min_of_max)
        self.ref_no_min.valueChanged[int].connect(max_handler)
        self.ref_no_max.valueChanged[int].connect(min_handler)
        hbox = QHBoxLayout()
        self.vbox.addWidget(QLabel('Set range averaged over to compute reference frame'))
        self.ref_no_min.setMinimum(0)
        self.ref_no_min.setMaximum(1400)
        self.ref_no_min.setValue(0)
        hbox.addWidget(self.ref_no_min)
        to = QLabel('to')
        to.setAlignment(Qt.AlignCenter)
        hbox.addWidget(to)
        self.ref_no_max.setMaximum(1000000)
        self.ref_no_max.setValue(1000)
        hbox.addWidget(self.ref_no_max)
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.ref_button)
        # self.vbox.addWidget(qtutil.separator())

        max_cut_off = 100000
        self.vbox.addWidget(QLabel('Choose single frame in stack that is matched with reference frame'))
        self.ref_no.setMinimum(0)
        self.ref_no.setMaximum(max_cut_off)
        self.ref_no.setValue(400)
        self.vbox.addWidget(self.ref_no)
        hbox = QHBoxLayout()
        self.scaling_checkbox.setChecked(False)
        hbox.addWidget(self.scaling_checkbox)
        self.rotation_checkbox.setChecked(True)
        hbox.addWidget(self.rotation_checkbox)
        self.vbox.addLayout(hbox)

        self.list_to_apply_shifts_to.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_to_apply_shifts_to.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.vbox.addWidget(self.list_to_apply_shifts_to)
        self.vbox.addWidget(self.shift_table)
        self.vbox.addWidget(self.align_btn)

        # self.vbox.addWidget(self.shift_btn)
        # self.vbox.addWidget(QLabel('translation vector, rotation angle (in degrees) and isotropic scale factor'))
        # # self.vbox.addWidget(self.shift_table)
        #
        # hbox = QHBoxLayout()
        # hbox.addWidget(QLabel(self.Labels.x_shift_label))
        # hbox.addWidget(QLabel(self.Labels.y_shift_label))
        # hbox.addWidget(QLabel(self.Labels.rotation_shift_label))
        # hbox.addWidget(QLabel(self.Labels.scale_shift_label))
        # self.vbox.addLayout(hbox)
        # hbox = QHBoxLayout()
        # hbox.addWidget(self.tvec_x_sb)
        # hbox.addWidget(self.tvec_y_sb)
        # hbox.addWidget(self.rotation_sb)
        # hbox.addWidget(self.scale_sb)
        # self.tvec_x_sb.setDecimals(16)
        # self.tvec_x_sb.setRange(-1000000, 1000000)
        # self.tvec_y_sb.setDecimals(16)
        # self.tvec_y_sb.setRange(-1000000, 1000000)
        # self.rotation_sb.setDecimals(16)
        # self.rotation_sb.setRange(-1000000, 1000000)
        # self.scale_sb.setDecimals(16)
        # self.scale_sb.setRange(-1000000, 1000000)
        # self.vbox.addLayout(hbox)
        # self.vbox.addWidget(self.use_shift_checkbox)
        # self.use_shift_checkbox.setChecked(False)
        # self.vbox.addWidget(qtutil.separator())
        #
        # self.vbox.addWidget(self.main_button)

    def setup_signals(self):
        super().setup_signals()
        self.list_to_apply_shifts_to.selectionModel().selectionChanged.connect(self.update_shift_table)
        self.crop_percentage_sb.valueChanged[int].connect(self.update_crop_border)
        self.ref_button.clicked.connect(self.compute_ref_frame)
        self.align_btn.clicked.connect(self.execute_primary_function)
        # self.main_button.clicked.connect(self.execute_primary_function)
        # self.ref_button.clicked.connect(self.compute_ref_frame)
        # self.shift_btn.clicked.connect(self.set_shifts)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.crop_percentage_sb_label, self.Defaults.crop_percentage_sb_default)
        self.crop_percentage_sb.setValue(self.params[self.Labels.crop_percentage_sb_label])
        #     self.update_plugin_params(self.Labels.apply_rotation_label, self.Defaults.apply_rotation_default)
        #     self.update_plugin_params(self.Labels.apply_scaling_label, self.Defaults.apply_scaling_default)
        # self.rotation_checkbox.setChecked(self.params[self.Labels.apply_rotation_label])
        # self.scaling_checkbox.setChecked(self.params[self.Labels.apply_scaling_label])

    def setup_param_signals(self):
        super().setup_param_signals()
        self.crop_percentage_sb.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                            self.Labels.crop_percentage_sb_label))
        # self.rotation_checkbox.stateChanged[int].connect(functools.partial(self.update_plugin_params,
        #                                                                    self.Labels.apply_rotation_label))
        # self.scaling_checkbox.stateChanged[int].connect(functools.partial(self.update_plugin_params,
        #                                                                   self.Labels.apply_scaling_label))

    def selected_video_changed(self, selected, deselected):
        super().selected_video_changed(selected, deselected)
        self.shift_table_col1 = [os.path.splitext(os.path.basename(x))[0] for x in self.selected_videos if
                                 self.Defaults.secondary_manip not in x]
        self.update_shift_table()


    def update_shift_table(self):
        num_rows = len(self.shift_table_col1)
        if not num_rows:
            self.shift_table.clear()
            self.shift_table.setRowCount(len(self.shift_table_col1))
            self.shift_table.setColumnCount(0)
            return
        # collect list_to_apply_shifts selected
        selected_list_to_apply_shifts_to = []
        for index in self.list_to_apply_shifts_to.selectedIndexes():
            selected_list_to_apply_shifts_to = selected_list_to_apply_shifts_to + [str(index.data(Qt.DisplayRole))]
        if self.list_to_apply_shifts_to.selectedIndexes():
            num_additional_cols = int(math.ceil(len(self.list_to_apply_shifts_to.selectedIndexes()) /
                                      len(self.shift_table_col1)))
        else:
            num_additional_cols = 0
        # Function for splitting selected_list_to_apply_shifts_to
        lol = lambda lst, sz: [lst[i:i + sz] for i in range(0, len(lst), sz)]
        if num_rows:
            selected_list_to_apply_shifts_to = lol(selected_list_to_apply_shifts_to, num_rows)
        else:
            self.shift_table.clear()
            return
        assert(len(selected_list_to_apply_shifts_to) == num_additional_cols)

        headers = []
        dat = {}
        dat[self.Labels.shift_table_col1] = self.shift_table_col1
        for i in range(num_additional_cols):
            header = "col" + str(i + 2)
            dat[header] = selected_list_to_apply_shifts_to[i]
            headers = headers + [header]

        self.shift_table.clear()
        self.shift_table.setRowCount(len(self.shift_table_col1))
        self.shift_table.setColumnCount(num_additional_cols + 1)
        self.shift_table.update(dat)
        self.shift_table_data = dat

    def update_crop_border(self):
        # remove all rois
        rois = self.view.vb.rois[:]
        for roi in rois:
            if not roi.isSelected:
                self.view.vb.selectROI(roi)
            self.view.vb.removeROI()

        per = self.crop_percentage_sb.value() / 100
        pixel_width, pixel_height = self.view.shape
        tot_width = pixel_width * self.project['unit_per_pixel']
        tot_height = pixel_height * self.project['unit_per_pixel']
        per_width = per * tot_width
        per_height = per * tot_height
        origin_x = self.project['origin'][0] * self.project['unit_per_pixel']
        origin_y = self.project['origin'][1] * self.project['unit_per_pixel']
        x1 = per_width - origin_x
        y1 = per_height - origin_y
        x2 = tot_width - per_width - origin_x
        y2 = per_height - origin_y
        x3 = tot_width - per_width - origin_x
        y3 = tot_height - per_height - origin_y
        x4 = per_width - origin_x
        y4 = tot_height - per_height - origin_y
        self.view.vb.addPolyRoiRequest()
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, pos=QPointF(x1, y1))
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, pos=QPointF(x2, y2))
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, pos=QPointF(x3, y3))
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, pos=QPointF(x4, y4))
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, pos=QPointF(x4, y4))
        self.view.vb.autoDrawPolygonRoi(self.Labels.window_name, finished=True)

    def cancel_progress_dialog(self, dialog):
        abort_msg = "Are you sure?"
        reply = QMessageBox.question(self, 'Abort Process', abort_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            dialog.close()
            raise InterruptedError('Progress Halted')
        else:
            return

    def generate_mean_filter_kernel(self, size):
        kernel = 1.0 / (size * size) * np.array([[1] * size] * size)
        return kernel

    def filter2_test_j(self, frame, kernal_size):
        kernel = self.generate_mean_filter_kernel(kernal_size)
        framek = ndimage.convolve(frame, kernel, mode='constant', cval=0.0)
        return framek

    def spatial_filter(self):
        kernal_size = self.kernal_size.value()
        ref_no_min = self.ref_no_min.value()
        ref_no_max = self.ref_no_max.value()
        progress = QProgressDialog('Spatial filtering...', 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()
        progress.canceled.connect(functools.partial(self.cancel_progress_dialog, progress))

        frames_mmap = np.load(self.shown_video_path, mmap_mode='c')
        reference_frame_range = np.array(frames_mmap[ref_no_min:ref_no_max])
        frames = np.empty((reference_frame_range.shape[0], reference_frame_range.shape[1],
                           reference_frame_range.shape[2]), dtype=np.float32)
        for frame_no, frame_original in enumerate(reference_frame_range):
            frames[frame_no] = self.filter2_test_j(frame_original, kernal_size)
            callback(frame_no / len(frames))
        frames = reference_frame_range - frames
        callback(1)
        return frames

    def crop_border(self, frames):
        if not frames.any():
            return
        progress = QProgressDialog('Cropping to window...', 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()
        progress.canceled.connect(functools.partial(self.cancel_progress_dialog, progress))

        percentage = self.crop_percentage_sb.value() / 100
        # frames_cropped = np.empty((frames.shape[0], frames.shape[1], frames.shape[2]),
        #               dtype=frames.dtype)
        cropped_y = round(percentage * frames.shape[1])
        cropped_x = round(percentage * frames.shape[2])
        for frame_no in range(len(frames)):
            for y in range(len(frames[frame_no])):
                for x in range(len(frames[frame_no][y])):
                    if (x < cropped_x or x > frames.shape[2] - cropped_x) or \
                            (y < cropped_y or y > frames.shape[1] - cropped_y):
                        frames[frame_no][y][x] = 0
                    if frame_no % 20 == 0:
                        callback(frame_no / len(frames))
        callback(1)
        return frames

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
        # find size, assuming all files in project have the same size
        ref_frames = self.spatial_filter()
        ref_frames = self.crop_border(ref_frames)
        if not ref_frames.any():
            return
        self.reference_frame = np.mean(ref_frames, axis=0, dtype=np.float32)

        frames_mmap = np.load(self.shown_video_path, mmap_mode='c')
        frame_no, h, w = frames_mmap.shape
        self.reference_frame = np.reshape(self.reference_frame, (1, h, w))
        pfs.save_project(self.selected_videos[0], self.project, self.reference_frame, 'ref_frame', 'ref_frame')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])

    def get_alignment_inputs(self, input_files=None):
        if not input_files:
            filenames = self.selected_videos
            reference_frame_file = [path for path in filenames if self.Defaults.secondary_manip in path]
        else:
            filenames = input_files
            reference_frame_file = self.selected_videos
            if len(reference_frame_file) != 1:
                qtutil.critical("Please only select a single reference frame for each alignment plugin used."
                          " Automation will now close.")
                raise ValueError("Please only select a single reference frame for each alignment plugin used")

        if len(reference_frame_file) == 0:
            qtutil.critical("No reference frame selected")
            raise ValueError("No reference frame selected")
        if len(reference_frame_file) > 1:
            qtutil.critical("Multiple reference frames selected. Please only pick one")
            raise ValueError("Multiple reference frames selected. Please only pick one")
        assert(len(reference_frame_file) == 1)
        reference_frame_file = reference_frame_file[0]

        assert ('ref_frame' in reference_frame_file)
        reference_frame = np.load(reference_frame_file)[0]
        not_reference_frames = [path for path in filenames if self.Defaults.secondary_manip not in path]
        return [reference_frame, not_reference_frames]


    def apply_shifts(self, frames, shift, progress_callback):
        # shifted_frames = []
        tvec = shift["tvec"]
        angle = shift["angle"]
        if "scale" in shift.keys():
            scale = shift["scale"]
        else:
            scale = 1.0
        for frame_no, frame in enumerate(frames):
            progress_callback(frame_no / float(len(frames)))
            # frame = frames[frame_no]
            # shifted_frames.append(ird.transform_img(frame, tvec=tvec, angle=angle, scale=scale))
            frames[frame_no] = ird.transform_img(frame, tvec=tvec, angle=angle, scale=scale)
        progress_callback(1)
        return frames

    def execute_primary_function(self, input_paths=None):
        """Return filenames of generated videos"""
        [reference_frame, to_align_paths] = self.get_alignment_inputs(input_paths)
        assert([os.path.splitext(os.path.basename(path))[0] for path in to_align_paths] ==
               self.shift_table_data[self.Labels.shift_table_col1])

        progress_global = QProgressDialog('Total progress aligning all files', 'Abort', 0, 100, self)
        progress_global.setAutoClose(True)
        progress_global.setMinimumDuration(0)
        def callback_global(x):
            progress_global.setValue(x * 100)
            QApplication.processEvents()
        callback_global(0)
        progress_global.canceled.connect(functools.partial(self.cancel_progress_dialog, progress_global))

        ret_filenames = []
        shifts = {}
        for i, filename in enumerate(to_align_paths):
            callback_global(i / float(len(to_align_paths)))
            progress_shifts = QProgressDialog('Finding best shifts for ' + filename, 'Abort', 0, 100, self)
            progress_shifts.setAutoClose(True)
            progress_shifts.setMinimumDuration(0)
            progress_shifts.canceled.connect(functools.partial(self.cancel_progress_dialog, progress_shifts))

            progress_load = QProgressDialog('Loading ' + filename, 'Abort', 0, 100, self)
            progress_load.setAutoClose(True)
            progress_load.setMinimumDuration(0)
            def callback_load(x):
                progress_load.setValue(x * 100)
                QApplication.processEvents()
            frames = file_io.load_file(filename, callback_load)
            callback_load(1)

            to_align_frame = frames[self.ref_no.value()]
            if self.scaling_checkbox.isChecked() or self.rotation_checkbox.isChecked():
                shift = ird.similarity(reference_frame, to_align_frame)
                if not self.rotation_checkbox.isChecked():
                    shift['angle'] = 0.0
                if not self.scaling_checkbox.isChecked():
                    shift['scale'] = 1.0
            else:
                shift = ird.translation(reference_frame, to_align_frame)
            # if not self.use_shift_checkbox.isChecked():
            # else:
            #     shift = {'tvec': [self.tvec_y_sb.value(), self.tvec_x_sb.value()], 'angle': self.rotation_sb.value(),
            #              'scale': self.scale_sb.value()}
            shifts[filename] = shift

            for col_key in self.shift_table_data.keys():
                # i = row
                filename = os.path.normpath(os.path.join(self.project.path, self.shift_table_data[col_key][i])) + '.npy'
                frames = file_io.load_file(filename, callback_load)
                callback_load(1)

                progress_apply = QProgressDialog('Applying shifts for ' + filename, 'Abort', 0, 100, self)
                progress_apply.setAutoClose(True)
                progress_apply.setMinimumDuration(0)
                def callback_apply(x):
                    progress_apply.setValue(x * 100)
                    QApplication.processEvents()
                progress_apply.canceled.connect(functools.partial(self.cancel_progress_dialog, progress_apply))

                shifted_frames = self.apply_shifts(frames, shift, callback_apply)
                path = pfs.save_project(filename, self.project, shifted_frames, self.Defaults.manip, 'video')
                pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                                 self.Defaults.list_display_type, self.toolbutton_values)
                ret_filenames.append(path)
        callback_global(1)
        return ret_filenames


    # def get_alignment_inputs(self, input_files=None):
    #     if not input_files:
    #         filenames = self.selected_videos
    #         reference_frame_file = [path for path in filenames if self.Defaults.secondary_manip in path]
    #     else:
    #         filenames = input_files
    #         reference_frame_file = self.selected_videos
    #         if len(reference_frame_file) != 1:
    #             qtutil.critical("Please only select a single reference frame for each alignment plugin used."
    #                             " Automation will now close.")
    #             raise ValueError("Please only select a single reference frame for each alignment plugin used")
    #
    #     if len(reference_frame_file) == 0:
    #         qtutil.critical("No reference frame selected")
    #         raise ValueError("No reference frame selected")
    #     if len(reference_frame_file) > 1:
    #         qtutil.critical("Multiple reference frames selected. Please only pick one")
    #         raise ValueError("Multiple reference frames selected. Please only pick one")
    #     assert (len(reference_frame_file) == 1)
    #     reference_frame_file = reference_frame_file[0]
    #
    #     assert ('ref_frame' in reference_frame_file)
    #     reference_frame = np.load(reference_frame_file)[0]
    #     not_reference_frames = [path for path in filenames if self.Defaults.secondary_manip not in path]
    #     return [reference_frame, not_reference_frames]
    #
    # def compute_ref_frame(self):
    #     if not self.selected_videos:
    #         qtutil.critical("No files selected")
    #         return
    #
    #     if len(self.selected_videos) > 1:
    #         qtutil.critical("Select only one file to compute the reference frame from")
    #         return
    #
    #     if 'ref_frame' in self.selected_videos[0]:
    #         qtutil.critical("Cannot compute reference frame of reference frame")
    #         return
    #
    #     ref_no_min = self.ref_no_min.value()
    #     ref_no_max = self.ref_no_max.value()
    #
    #     # find size, assuming all files in project have the same size
    #     frames_mmap = np.load(self.shown_video_path, mmap_mode='c')
    #     reference_frame_range = np.array(frames_mmap[ref_no_min:ref_no_max])
    #     self.reference_frame = np.mean(reference_frame_range, axis=0, dtype=np.float32)
    #
    #     frame_no, h, w = frames_mmap.shape
    #     self.reference_frame = np.reshape(self.reference_frame, (1, h, w))
    #     pfs.save_project(self.selected_videos[0], self.project, self.reference_frame, 'ref_frame', 'ref_frame')
    #     pfs.refresh_list(self.project, self.video_list,
    #                      self.params[self.Labels.video_list_indices_label],
    #                      self.Defaults.list_display_type,
    #                      self.params[self.Labels.last_manips_to_display_label])
    #
    # def set_shifts(self):
    #     [reference_frame, not_reference_frames] = self.get_alignment_inputs()
    #     if len(not_reference_frames) != 1:
    #         qtutil.critical("Please select only one file to align to the reference frame to set the shift. Only one "
    #                         "file for setting shifts is supported for now")
    #         return
    #     frame_to_shift = file_io.load_file(not_reference_frames[0],
    #                                        segment=[self.ref_no.value(), self.ref_no.value() + 1])
    #     shift = self.compute_shift(reference_frame, frame_to_shift[0])
    #     self.tvec_x_sb.setValue(shift['tvec'][1])  # [Y,X] not [X,Y]
    #     self.tvec_y_sb.setValue(shift['tvec'][0])
    #     self.rotation_sb.setValue(shift['angle'])
    #     self.scale_sb.setValue(shift['scale'])
    #
    # def compute_shift(self, ref_frame, frame):
    #     if self.scaling_checkbox.isChecked() or self.rotation_checkbox.isChecked():
    #         shift = ird.similarity(ref_frame, frame)
    #         if not self.rotation_checkbox.isChecked():
    #             shift['angle'] = 0.0
    #         if not self.scaling_checkbox.isChecked():
    #             shift['scale'] = 1.0
    #     else:
    #         shift = ird.translation(ref_frame, frame)
    #         shift['scale'] = 1.0
    #     return shift
    #
    # def execute_primary_function(self, input_files=None):
    #     [reference_frame, not_reference_frames] = self.get_alignment_inputs(input_files)
    #     return self.align_videos(not_reference_frames, reference_frame)
    #
    # # def compute_shifts(self, template_frame, frames, progress_shifts):
    # #     def callback_shifts(x):
    # #         progress_shifts.setValue(x * 100)
    # #         QApplication.processEvents()
    # #     results = []
    # #     for i, frame in enumerate(frames):
    # #         if progress_shifts.wasCanceled():
    # #             return
    # #         callback_shifts(i / float(len(frames)))
    # #         results = results + [ird.translation(template_frame, frame)]
    # #     callback_shifts(1)
    # #     return results
    # def compute_shifts(self, template_frame, frames, progress_shifts):
    #     def callback_shifts(x):
    #         progress_shifts.setValue(x * 100)
    #         QApplication.processEvents()
    #
    #     results = []
    #     for i, frame in enumerate(frames):
    #         if progress_shifts.wasCanceled():
    #             return
    #         callback_shifts(i / float(len(frames)))
    #         results = results + [ird.translation(template_frame, frame)]
    #     callback_shifts(1)
    #     return results
    #
    # def apply_shifts(self, frames, shift, progress_callback):
    #     # shifted_frames = []
    #     tvec = shift["tvec"]
    #     angle = shift["angle"]
    #     if "scale" in shift.keys():
    #         scale = shift["scale"]
    #     else:
    #         scale = 1.0
    #     for frame_no, frame in enumerate(frames):
    #         progress_callback(frame_no / float(len(frames)))
    #         # frame = frames[frame_no]
    #         # shifted_frames.append(ird.transform_img(frame, tvec=tvec, angle=angle, scale=scale))
    #         frames[frame_no] = ird.transform_img(frame, tvec=tvec, angle=angle, scale=scale)
    #     progress_callback(1)
    #     return frames
    #
    # def align_videos(self, filenames, template_frame):
    #     """Return filenames of generated videos"""
    #     progress_global = QProgressDialog('Total progress aligning all files', 'Abort', 0, 100, self)
    #     progress_global.setAutoClose(True)
    #     progress_global.setMinimumDuration(0)
    #
    #     def callback_global(x):
    #         progress_global.setValue(x * 100)
    #         QApplication.processEvents()
    #
    #     callback_global(0)
    #     ret_filenames = []
    #
    #     for i, filename in enumerate(filenames):
    #         callback_global(i / float(len(filenames)))
    #         progress_shifts = QProgressDialog('Finding best shifts for ' + filename, 'Abort', 0, 100, self)
    #         progress_shifts.setAutoClose(True)
    #         progress_shifts.setMinimumDuration(0)
    #         progress_apply = QProgressDialog('Applying shifts for ' + filename, 'Abort', 0, 100, self)
    #         progress_apply.setAutoClose(True)
    #         progress_apply.setMinimumDuration(0)
    #
    #         def callback_apply(x):
    #             progress_apply.setValue(x * 100)
    #             QApplication.processEvents()
    #
    #         progress_load = QProgressDialog('Loading ' + filename, 'Abort', 0, 100, self)
    #         progress_load.setAutoClose(True)
    #         progress_load.setMinimumDuration(0)
    #
    #         def callback_load(x):
    #             progress_load.setValue(x * 100)
    #             QApplication.processEvents()
    #
    #         frames = file_io.load_file(filename, callback_load)
    #         callback_load(1)
    #
    #         reference_frame = frames[
    #             self.ref_no.value()]  # todo: this needs to be renamed... reference frame is already established as something else
    #
    #         if not self.use_shift_checkbox.isChecked():
    #             if self.scaling_checkbox.isChecked() or self.rotation_checkbox.isChecked():
    #                 shift = ird.similarity(template_frame, reference_frame)
    #                 if not self.rotation_checkbox.isChecked():
    #                     shift['angle'] = 0.0
    #                 if not self.scaling_checkbox.isChecked():
    #                     shift['scale'] = 1.0
    #             else:
    #                 shift = ird.translation(template_frame, reference_frame)
    #             if progress_shifts.wasCanceled():
    #                 return
    #         else:
    #             shift = {'tvec': [self.tvec_y_sb.value(), self.tvec_x_sb.value()], 'angle': self.rotation_sb.value(),
    #                      'scale': self.scale_sb.value()}
    #
    #         shifted_frames = self.apply_shifts(frames, shift, callback_apply)
    #         path = pfs.save_project(filename, self.project, shifted_frames, self.Defaults.manip, 'video')
    #         pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
    #                          self.Defaults.list_display_type, self.toolbutton_values)
    #         ret_filenames.append(path)
    #     callback_global(1)
    #     return ret_filenames
    #
    # def setup_whats_this(self):
    #     super().setup_whats_this()
    #     self.ref_no_min.setWhatsThis("All image stacks are aligned to a single reference frame. Here you can select "
    #                                  "a single image stack above and choose which single frame is used by setting the "
    #                                  "min = max. However, you can also average over a range of frames which may "
    #                                  "improve noise-signal ratio and thereby emphasize consistent features suitable "
    #                                  "for alignment (e.g. blood veins). Typically a single spatially filtered image "
    #                                  "stack is used to compute the reference frame to emphasize features such as blood"
    #                                  "veins ever further")
    #     self.ref_no_max.setWhatsThis("All image stacks are aligned to a single reference frame. Here you can select "
    #                                  "a single image stack above and choose which single frame is used by setting the "
    #                                  "min = max. However, you can also average over a range of frames which may "
    #                                  "improve noise-signal ratio and thereby emphasize consistent features suitable "
    #                                  "for alignment (e.g. blood veins). Typically a single spatially filtered image "
    #                                  "stack is used to compute the reference frame to emphasize features such as blood"
    #                                  "veins ever further")
    #     self.ref_button.setWhatsThis("Click to compute your reference frame using the single selected image stack and "
    #                                  "the parameters above. The reference frame can afterwards be found at the top of "
    #                                  "the video list to be used with the parameters below\n"
    #                                  "Note that for automation, a reference frame must be selected")
    #     self.ref_no.setWhatsThis("During alignment a single frame is selected from each image stack. This frame is "
    #                              "aligned to the reference frame you have previously computed. The shift required "
    #                              "(translation, rotation and scaling) to attain alignment between these two frames is "
    #                              "then applied to all frames in that image stack. Here the 400th frame is arbitrarily "
    #                              "the default because in our experience this is typically far enough so as to avoid "
    #                              "any potential artifacts at the start of the stack if these were not cut off")
    #     self.scaling_checkbox.setWhatsThis("Set if scaling is performed to find the best alignment.")
    #     self.rotation_checkbox.setWhatsThis("Set if rotation is performed to find the best alignment")
    #     self.main_button.setWhatsThis("Note that without either rotation or scaling checked, only x-y translation is "
    #                                   "performed")


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Alignment'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self, expected_input_number):
        return False
        # filenames = self.get_input_paths()
        # reference_frame_file = [path for path in filenames if self.widget.Defaults.secondary_manip in path]
        # if len(reference_frame_file) == 1:
        #     return True
        # else:
        #     return False

    def automation_error_message(self):
        return "Please select one reference frame for each alignment plugin used"


