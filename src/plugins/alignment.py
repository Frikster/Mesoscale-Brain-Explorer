#!/usr/bin/env python3

import imreg_dft as ird
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView


class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
            return
        self.project = project

        # define widgets and data
        self.left = QFrame()
        self.right = QFrame()
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.ref_no = QSpinBox()

        self.setup_ui()

        self.selected_videos = []
        self.shown_video_path = None

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        pfs.refresh_all_list(self.project, self.video_list)

    def video_triggered(self, index):
        pfs.video_triggered(self, index)

    def setup_ui(self):
        vbox_view = QVBoxLayout()
        vbox_view.addWidget(self.view)
        self.left.setLayout(vbox_view)

        vbox = QVBoxLayout()
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        vbox.addWidget(self.toolbutton)
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)
        max_cut_off = 5000
        vbox.addWidget(QLabel('Choose frame used for reference averaged across all selected  files'))
        self.ref_no.setMinimum(0)
        self.ref_no.setMaximum(max_cut_off)
        self.ref_no.setValue(400)
        vbox.addWidget(self.ref_no)
        pb = QPushButton('&Compute Reference Frame')
        pb.clicked.connect(self.compute_ref_frame)
        vbox.addWidget(pb)
        pb = QPushButton('&Align')
        pb.clicked.connect(self.align_clicked)
        vbox.addWidget(pb)
        self.right.setLayout(vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

        # hbox.addLayout(vbox)
        # hbox.setStretch(0, 1)
        # hbox.setStretch(1, 0)
        # self.setLayout(hbox)

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item, ref_version=True)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def compute_ref_frame(self):
        if not self.selected_videos:
            qCritical("No files selected")
            return

        ref_no = self.ref_no.value()

        # find size, assuming all files in project have the same size
        frames_mmap = np.load(self.shown_video_path, mmap_mode='c')
        frame_no, h, w = frames_mmap.shape

        summed_reference_frame = np.zeros((h, w))
        divide_frame = np.full((h, w), len(self.selected_videos))
        for video_path in self.selected_videos:
            frames_mmap = np.load(video_path, mmap_mode='c')
            reference_frame = np.array(frames_mmap[ref_no])
            summed_reference_frame = np.add(summed_reference_frame, reference_frame)

        summed_reference_frame = np.divide(summed_reference_frame, divide_frame)
        self.reference_frame = np.reshape(summed_reference_frame, (1, h, w))
        pfs.save_project(video_path, self.project, self.reference_frame, 'ref_frame', 'ref_frame')

        # Refresh showing reference_frame
        pfs.refresh_all_list(self.project, self.video_list)

    def align_clicked(self):
        filenames = self.selected_videos
        reference_frame_file = [file for file in filenames if file[-13:] == 'ref_frame.npy']
        if len(reference_frame_file) == 0:
            qCritical("No reference frame selected")
            return
        if len(reference_frame_file) > 1:
            qCritical("Multiple reference frames selected. Please only pick one")
            return
        assert(len(reference_frame_file) == 1)
        reference_frame_file = reference_frame_file[0]

        assert ('ref_frame' in reference_frame_file)
        reference_frame = np.load(reference_frame_file)[0]
        not_reference_frames = [file for file in filenames if file[-13:] != 'ref_frame.npy']
        self.align_videos(not_reference_frames, reference_frame)

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
            results = results + [ird.translation(template_frame, frame)]
        callback_shifts(1)
        return results

    def apply_shifts(self, frames, shifts, progress_callback):
        shifted_frames = []
        for frame_no, shift in enumerate(shifts):
            tvec = shift["tvec"]
            progress_callback(frame_no / float(len(shifts)))
            frame = frames[frame_no]
            shifted_frames.append(ird.transform_img(frame, tvec=tvec))
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
            shifts = self.compute_shifts(reference_frame, frames, progress_shifts)
            if progress_shifts.wasCanceled():
                return
            shifted_frames = self.apply_shifts(frames, shifts, callback_apply)
            pfs.save_project(filename, self.project, shifted_frames, 'align', 'video')
            pfs.refresh_all_list(self.project, self.video_list)
            # path = os.path.join(os.path.dirname(filename), 'aligned_' + \
            #                     os.path.basename(filename))
            # np.save(path, shifted_frames)
            # ret_filenames.append(path)
        callback_global(1)
        return ret_filenames


class MyPlugin:
    def __init__(self, project, plugin_position):
        self.name = 'Alignment'
        self.widget = Widget(project)

    def run(self):
        pass