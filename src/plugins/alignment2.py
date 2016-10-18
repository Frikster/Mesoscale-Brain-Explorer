#!/usr/bin/env python3

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .util import filter_jeff
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView, MyProgressDialog
from .util.gradient import GradientLegend
from .util import project_functions as pfs
from .util import fileloader

import os
import numpy as np
import imreg_dft as ird
import matplotlib
import matplotlib.pyplot as plt
import math

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
            return
        self.project = project
        self.setup_ui()

        self.open_dialogs = []
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        pfs.refresh_all_list(self.project, self.video_list)


    def setup_ui(self):
        hbox = QHBoxLayout()
        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list = MyListView()
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)

        max_cut_off = 5000
        vbox.addWidget(QLabel('Choose frame used for reference averaged across all selected  files'))
        self.ref_no = QSpinBox()
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

        hbox.addLayout(vbox)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

    def selected_video_changed(self, selected, deselected):
        if not selected.indexes():
            return

        for index in deselected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
            self.selected_videos = [x for x in self.selected_videos if x != vidpath]
        for index in selected.indexes():
            vidpath = str(os.path.join(self.project.path,
                                     index.data(Qt.DisplayRole))
                              + '.npy')
        if vidpath not in self.selected_videos and vidpath != 'None':
            self.selected_videos = self.selected_videos + [vidpath]

        self.shown_video_path = str(os.path.join(self.project.path,
                                           selected.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.shown_video_path)
        self.view.show(frame)

    def compute_ref_frame(self):
        if not self.selected_videos:
            qCritical("No files selected")
            return

        ref_no = self.ref_no.value()
        self.selected_videos

        # find size, assuming all files in project have the same size
        frames_mmap = np.load(self.selected_videos[0], mmap_mode='c')
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
        if not self.selected_videos:
            qCritical("No files selected")
            return
        if self.selected_videos[0][-13:] != 'ref_frame.npy':
            qCritical("No reference frame selected")
            return

        #selection = self.table1.selectionModel().selectedRows()
        filenames = self.selected_videos

        progress = QProgressDialog('Aligning file...', 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)

        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()
            # time.sleep(0.01)

        reference_frame = np.load(filenames[0])[0]
        filenames = self.align_videos(filenames, reference_frame, callback)

        for filename in filenames:
            if filename in [f['path'] for f in self.project.files]:
                continue
            name, ext = os.path.splitext(os.path.basename(filename))
            f = {
                'name': name,
                'path': filename,
                'type': 'video',
                'manipulations': 'align'
            }
            self.project.files.append(f)
        self.project.save()

    def compute_shifts(self, template_frame, frames, progress_callback):
        results = []
        for i, frame in enumerate(frames):
            progress_callback(i / float(len(frames)))
            results = results + [ird.translation(template_frame, frame)]
        return results

    def apply_shifts(self, frames, shifts, progress_callback):
        shifted_frames = []
        for frame_no, shift in enumerate(shifts):
            tvec = shift["tvec"]
            progress_callback(frame_no / float(len(shifts)))
            frame = frames[frame_no]
            shifted_frames.append(ird.transform_img(frame, tvec=tvec))
        return shifted_frames

    def align_videos(self, filenames, reference_frame, progress_callback):
        """Return filenames of generated videos"""
        progress_callback(0)
        ret_filenames = []
        reference_frame
        for filename in filenames:
            frames = np.load(filename)
            shifts = self.compute_shifts(reference_frame, frames, progress_callback)
            shifted_frames = self.apply_shifts(frames, shifts, progress_callback)
            path = os.path.join(os.path.dirname(filename), 'aligned_' + \
                                os.path.basename(filename))
            np.save(path, shifted_frames)
            ret_filenames.append(path)
        progress_callback(1)
        return ret_filenames


class MyPlugin:
    def __init__(self, project):
        self.name = 'Alignment2'
        self.widget = Widget(project)

    def run(self):
        pass