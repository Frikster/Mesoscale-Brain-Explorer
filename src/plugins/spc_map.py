#!/usr/bin/env python3

import csv
import os
from pyqtgraph.dockarea import *

from itertools import cycle
import uuid
import functools
import matplotlib
import numpy as np
import qtutil
import scipy.misc
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtGui
from pyqtgraph.graphicsItems.UIGraphicsItem import *

from .util import fileloader
from .util import filter_jeff
from .util import mse_ui_elements as mue
from .util import project_functions as pfs
from .util.gradient import GradientLegend
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView, MyProgressDialog
from .util.mse_ui_elements import RoiList

from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util.mse_ui_elements import RoiItemModel
import pickle

UUID_SIZE = len(str(uuid.uuid4()))

# def calc_spc(video_path, x, y, progress):
#     frame = fileloader.load_reference_frame(video_path)
#     width, height = frame.shape
#
#     x = int(x)
#     y = int(height - y)
#
#     frames = fileloader.load_file(video_path)
#     spc_map = filter_jeff.correlation_map(y, x, frames, progress)
#
#     # Make the location of the roi - self.image[y,x] - blatantly obvious
#     spc_map[y+1, x+1] = 1
#     spc_map[y+1, x] = 1
#     spc_map[y, x+1] = 1
#     spc_map[y-1, x-1] = 1
#     spc_map[y-1, x] = 1
#     spc_map[y, x-1] = 1
#     spc_map[y+1, x-1] = 1
#     spc_map[y-1, x+1] = 1
#
#     return spc_map


def calc_spc(frames, x, y, progress):
    width, height = frames[0].shape
    x = int(x)
    y = int(height - y)
    spc_map = filter_jeff.correlation_map(y, x, frames, progress)

    # Make the location of the roi - self.image[y,x] - blatantly obvious
    spc_map[y+1, x+1] = 1
    spc_map[y+1, x] = 1
    spc_map[y, x+1] = 1
    spc_map[y-1, x-1] = 1
    spc_map[y-1, x] = 1
    spc_map[y, x-1] = 1
    spc_map[y+1, x-1] = 1
    spc_map[y-1, x+1] = 1

    return spc_map

# class SeedItemModel(QAbstractListModel):
#     textChanged = pyqtSignal(str, str)
#
#     # dataChanged = pyqtSignal(int, int)
#
#     def __init__(self, parent=None):
#         super(SeedItemModel, self).__init__(parent)
#         self.seeds = []
#
#     def appendseed(self, name):
#         self.seeds.append(name)
#         row = len(self.seeds) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def edit_seed_name(self, name, index):
#         self.seeds.append(name)
#         row = len(self.seeds) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def rowCount(self, parent):
#         return len(self.seeds)
#
#     def data(self, index, role):
#         if role == Qt.DisplayRole:
#             return self.seeds[index.row()]
#         return
#
#     def setData(self, index, value, role):
#         if role in [Qt.DisplayRole, Qt.EditRole]:
#             self.textChanged.emit(self.seeds[index.row()], value)
#             self.seeds[index.row()] = str(value)
#             return True
#         return super(SeedItemModel, self).setData(index, value, role)
#
#     def flags(self, index):
#         return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
#
#     def removeRow(self, seed_to_remove):
#         for seed in self.seeds:
#             if seed == seed_to_remove:
#                 del seed
#                 break

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        colormap_index_label = "Choose Colormap:"
        sb_min_label = "Min correlation value to display"
        sb_max_label = "Max correlation value to display"

    class Defaults(WidgetDefault.Defaults):
        colormap_index_default = 1
        roi_list_types_displayed = ['auto_roi']
        manip = "spc"
        sb_min_default = -1.00
        sb_max_default = 1.00

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.project = project

        # define Widgets and data
        self.view = MyGraphicsView(self.project)
        # self.video_list = MyListView()
        self.cm_comboBox = QtGui.QComboBox(self)
        self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed)
        self.save_pb = QPushButton("&Save spc windows")
        self.load_pb = QPushButton("&Load project spc windows")
        self.bulk_background_pb = QPushButton('Save all SPC maps from table ROIs to file')
        self.spc_from_rois_pb = QPushButton('Generate SPC maps')
        self.open_dialogs_data_dict = []
        self.min_sb = QDoubleSpinBox()
        self.max_sb = QDoubleSpinBox()

        # self.left = QFrame()
        # self.right = QFrame()

        # self.setup_ui()
        self.cm_type = self.cm_comboBox.itemText(0)

        # self.open_dialogs = []
        # self.selected_videos = []

        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)
        # for f in project.files:
        #   if f['type'] != 'video':
        #     continue
        #   self.video_list.model().appendRow(QStandardItem(f['name']))
        # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        # self.cm_comboBox.activated[str].connect(self.cm_choice)

        # setup ROI list widget
        # model = SeedItemModel()
        # self.roi_list.setModel(RoiItemModel())
        # self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # A flag to see whether selected_roi_changed is being entered for the first time
        # self.selected_roi_changed_flag = 0
        # roi_names = [f['name'] for f in project.files if f['type'] == 'auto_roi']
        # for roi_name in roi_names:
        #     if roi_name not in self.roi_list.model().rois:
        #         self.roi_list.model().appendRoi(roi_name)
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
        # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # vbox.addWidget(self.video_list)
        self.vbox.addWidget(QLabel('Choose colormap:'))
        # todo: colormap list should be dealt with in a seperate script
        self.cm_comboBox.addItem("jet")
        self.cm_comboBox.addItem("viridis")
        self.cm_comboBox.addItem("inferno")
        self.cm_comboBox.addItem("plasma")
        self.cm_comboBox.addItem("magma")
        self.cm_comboBox.addItem("coolwarm")
        self.cm_comboBox.addItem("PRGn")
        self.cm_comboBox.addItem("seismic")
        self.vbox.addWidget(self.cm_comboBox)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(self.Labels.sb_min_label))
        hbox.addWidget(QLabel(self.Labels.sb_max_label))
        self.vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(self.min_sb)
        hbox.addWidget(self.max_sb)
        def min_handler(max_of_min):
            self.min_sb.setMaximum(max_of_min)
        def max_handler(min_of_max):
            self.max_sb.setMinimum(min_of_max)
        self.min_sb.valueChanged[float].connect(max_handler)
        self.max_sb.valueChanged[float].connect(min_handler)
        self.min_sb.setMinimum(-1.0)
        self.max_sb.setMaximum(1.0)
        self.min_sb.setSingleStep(0.1)
        self.max_sb.setSingleStep(0.1)
        self.vbox.addLayout(hbox)

        # self.vbox.addWidget(qtutil.separator())
        self.vbox.addWidget(QLabel('Seeds'))
        self.vbox.addWidget(self.roi_list)
        # pb = QPushButton('Save all SPC maps from table seeds to file')
        self.vbox.addWidget(self.save_pb)
        self.vbox.addWidget(self.load_pb)
        # pb = QPushButton('Generate SPC maps from selected seeds (display windows and save to file)')
        self.vbox.addWidget(self.spc_from_rois_pb)
        self.vbox.addStretch()
        self.vbox.addWidget(mue.InfoWidget('Click on the image to generate custom SPC map.'))
        # self.right.setLayout(self.vbox)
        #
        # splitter = QSplitter(Qt.Horizontal)
        # splitter.setHandleWidth(3)
        # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        # splitter.addWidget(self.left)
        # splitter.addWidget(self.right)
        # hbox_global = QHBoxLayout()
        # hbox_global.addWidget(splitter)
        # self.setLayout(hbox_global)

    # def refresh_video_list_via_combo_box(self, trigger_item=None):
    #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
    #
    # def selected_video_changed(self, selected, deselected):
    #     pfs.selected_video_changed_multi(self, selected, deselected)

    def setup_signals(self):
        super().setup_signals()
        self.view.vb.clicked.connect(self.vbc_clicked)
        #self.bulk_background_pb.clicked.connect(self.spc_bulk_clicked)
        #self.spc_from_rois_pb.clicked.connect(self.spc_bulk_clicked_display)

        self.spc_from_rois_pb.clicked.connect(self.spc_triggered)
        self.save_pb.clicked.connect(self.save_dock_windows)
        self.load_pb.clicked.connect(self.load_dock_windows)
        # self.roi_list.selectionModel().selectionChanged[QItemSelection,
        #                                                 QItemSelection].connect(self.selected_roi_changed)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        self.roi_list.setup_params()
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.colormap_index_label, self.Defaults.colormap_index_default)
            self.update_plugin_params(self.Labels.sb_min_label, self.Defaults.sb_min_default)
            self.update_plugin_params(self.Labels.sb_max_label, self.Defaults.sb_max_default)
        self.cm_comboBox.setCurrentIndex(self.params[self.Labels.colormap_index_label])
        self.min_sb.setValue(self.params[self.Labels.sb_min_label])
        self.max_sb.setValue(self.params[self.Labels.sb_max_label])

    def setup_param_signals(self):
        super().setup_param_signals()
        self.roi_list.setup_param_signals()
        self.cm_comboBox.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.colormap_index_label))
        self.min_sb.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.sb_min_label))
        self.max_sb.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.sb_max_label))

    def get_video_path_to_spc_dict(self):
        # retrieve ROIs in view and their coordinates
        if 'roi_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
            qtutil.critical("There's no ROI table associated with this project. "
                            "ROIs coordinates are used as seeds to create seed pixel correlation maps")
            return
        text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
                          if self.project.files[x]['type'] == 'roi_table']
        assert (len(text_file_path) == 1)
        text_file_path = text_file_path[0]
        roi_table = []
        with open(text_file_path, 'rt', encoding='ascii') as csvfile:
            roi_table_it = csv.reader(csvfile, delimiter=',')
            for row in roi_table_it:
                roi_table = roi_table + [row]
        roi_table = np.array(roi_table)
        roi_table_range = range(len(roi_table))[1:]
        roi_names = [roi_table[x, 0] for x in roi_table_range]
        roi_coord_x = [float(roi_table[x, 2]) for x in roi_table_range]
        roi_coord_y = [float(roi_table[x, 3]) for x in roi_table_range]
        roi_coord_x = [self.convert_coord_to_numpy_reference(x, 'x') for x in roi_coord_x]
        roi_coord_y = [self.convert_coord_to_numpy_reference(y, 'y') for y in roi_coord_y]
        rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
        selected_videos = self.selected_videos
        if not rois_in_view:
            qtutil.critical("No ROI(s) selected as seed(s)")
            return
        if not selected_videos:
            qtutil.critical("No image stack selected")
            return

        # progress_load = QProgressDialog('Loading files and processing Seed Pixel Correlation maps. '
        #                                 'This may take a while for large files.', 'Abort', 0, 100)
        # progress_load.setAutoClose(True)
        # progress_load.setMinimumDuration(0)
        # def callback_load(x):
        #     progress_load.setValue(x * 100)
        #     QApplication.processEvents()

        progress_load = MyProgressDialog('Processing...', 'Loading files and processing Seed Pixel Correlation maps. '
                                    'This may take a while for large files.', parent=self)
        video_path_to_plots_dict = {}
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        for selected_vid_no, video_path in enumerate(selected_videos):
            frames = fileloader.load_file(video_path)
            roi_activity_dict = {}
            for i, roi_name in enumerate(roi_names):
                if progress_load.wasCanceled():
                    return
                progress_load.setValue((selected_vid_no * i) / (len(selected_videos) * len(roi_names)) * 100)
                if roi_name in rois_in_view:
                    x = roi_coord_x[i]
                    y = roi_coord_y[i]
                    spc = calc_spc(frames, x, y, progress)
                    roi_activity_dict[roi_name] = spc
            video_path_to_plots_dict[video_path] = roi_activity_dict
            progress.close()
        progress_load.close()
        return video_path_to_plots_dict

            # progress = QProgressDialog('Generating SPC Map(s) for ' + video_path, 'Abort', 0, 100, self)
            # progress.setAutoClose(True)
            # progress.setMinimumDuration(0)
            # def callback(x):
            #     progress.setValue(x * 100)
            #     QApplication.processEvents()

            # for roi in self.view.vb.rois:
            #     roi.print('')
            #     roi.getROIMask(frames, self.view.vb.img., axes=(1, 2))
            # roi_paths = [os.path.normpath(self.project.files[i]['path'])
            #              for i in range(len(self.project.files))
            #              if self.project.files[i]['type'] == 'roi']
            #
            # rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
            # rois_to_add = [x for x in rois_selected if x not in rois_in_view]
            # for roi_to_add in rois_to_add:
            #     self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])



        #     for i, roi_name in enumerate(roi_names):
        #         if roi_name in rois_in_view:
        #             callback(i / len(roi_names))
        #             x = roi_coord_x[i]
        #             y = roi_coord_y[i]
        #             roi_name = roi_names[i]
        #             self.spc_to_windows(x, y, roi_name, video_path)
        #     callback(1)
        # global_callback(1)


    def setup_docks(self):
        area = DockArea()
        d1 = Dock("d1", size=(500, 200), closable=True)
        d2 = Dock("d2", size=(500, 200), closable=True)
        d3 = Dock("d3", size=(500, 200), closable=True)
        d4 = Dock("d4", size=(500, 200), closable=True)
        d5 = Dock("d5", size=(500, 200), closable=True)
        d6 = Dock("d6", size=(500, 200), closable=True)
        area.addDock(d1)
        area.addDock(d2, 'bottom', d1)
        area.addDock(d3, 'right', d2)
        area.addDock(d4, 'right', d3)
        area.moveDock(d5, 'right', d1)
        area.moveDock(d6, 'left', d5)
        return area

    def plot_to_docks(self, video_path_to_spc_dict, area):
        if not video_path_to_spc_dict:
            return
        roi_names = list(list(video_path_to_spc_dict.values())[0].keys())
        video_paths = list(video_path_to_spc_dict.keys())

        spc_docks = [0, 1, 2, 3, 4, 5]
        spc_docs_cycle = cycle(spc_docks)
        for roi_name in roi_names:
            for video_path in video_paths:
                # put all plots from one ROI on a single plot and place on one of the 4 docs
                next_dock = next(spc_docs_cycle)
                d = Dock(roi_name, size=(500, 200), closable=True)
                area.addDock(d, 'above', area.docks['d' + str(next_dock + 1)])

                spc = video_path_to_spc_dict[video_path][roi_name]
                doc_window = SPCMapDialog(self.project, video_path, spc, self.cm_comboBox.currentText(),
                                          (round(self.min_sb.value(), 2), round(self.max_sb.value(), 2)), roi_name)
                root, ext = os.path.splitext(video_path)
                source_name = os.path.basename(root)
                doc_window.setWindowTitle(source_name)
                d.addWidget(doc_window)

                # save to file
                spc_col = doc_window.colorized_spc
                path_without_ext = os.path.join(self.project.path, video_path + "_" + roi_name)
                scipy.misc.toimage(spc_col).save(path_without_ext + "_" + self.cm_comboBox.currentText() + '.jpg')
                np.save(path_without_ext + '.npy', spc)
        # close placeholder docks
        for spc_dock in spc_docks:
            area.docks['d'+str(spc_dock+1)].close()

    def spc_triggered(self):
        main_window = QMainWindow()
        area = self.setup_docks()
        main_window.setCentralWidget(area)
        main_window.resize(2000, 900)
        main_window.setWindowTitle("Window ID - " + str(uuid.uuid4()) +
                                   ". Use Help -> What's This on this window for contextual tips")

        video_path_to_spc_dict = self.get_video_path_to_spc_dict()
        self.plot_to_docks(video_path_to_spc_dict, area)
        main_window.show()
        self.open_dialogs.append(main_window)
        self.open_dialogs_data_dict.append((main_window, video_path_to_spc_dict))

    def save_dock_windows(self):
        pfs.save_dock_windows(self, 'spc_window')

    def load_dock_windows(self):
        pfs.load_dock_windows(self, 'spc_window')

    def filedialog(self, name, filters):
        path = self.project.path
        dialog = QFileDialog(self)
        dialog.setWindowTitle('Export to')
        dialog.setDirectory(str(path))
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.selectFile(name)
        dialog.setFilter(';;'.join(filters.values()))
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        if not dialog.exec_():
            return None
        filename = str(dialog.selectedFiles()[0])
        QSettings().setValue('export_path', os.path.dirname(filename))
        filter_ = str(dialog.selectedNameFilter())
        ext = [f for f in filters if filters[f] == filter_][0]
        if not filename.endswith(ext):
            filename = filename + ext
        return filename

    # def prepare_roi_list_for_update(self, selected, deselected):
    #     val = [v.row() for v in self.roi_list.selectedIndexes()]
    #     self.update_plugin_params(self.Labels.roi_list_indices_label, val)

    # def selected_roi_changed(self, selection):
    #     if self.selected_roi_changed_flag == 0:
    #         self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
    #         return
    #     if not selection.indexes() or self.view.vb.drawROImode:
    #         return


    #     self.remove_all_rois()
    #     rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
    #                       for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
    #     rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
    #     rois_to_add = [x for x in rois_selected if x not in rois_in_view]
    #     for roi_to_add in rois_to_add:
    #         self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])

    # def remove_all_rois(self):
    #     rois = self.view.vb.rois[:]
    #     for roi in rois:
    #         if not roi.isSelected:
    #             self.view.vb.selectROI(roi)
    #         self.view.vb.removeROI()

    # def spc_bulk_clicked(self):
    #     global_progress = QProgressDialog('Saving all Requested Maps to Project Dir', 'Abort', 0, 100, self)
    #     global_progress.setAutoClose(True)
    #     global_progress.setMinimumDuration(0)
    #     def global_callback(x):
    #         global_progress.setValue(x * 100)
    #         QApplication.processEvents()
    #     total = len(self.selected_videos)
    #     for selected_vid_no, video_path in enumerate(self.selected_videos):
    #         global_callback(selected_vid_no / total)
    #         progress = QProgressDialog('Generating SPC Map(s) for ' + video_path, 'Abort', 0, 100, self)
    #         progress.setAutoClose(True)
    #         progress.setMinimumDuration(0)
    #         def callback(x):
    #             progress.setValue(x * 100)
    #             QApplication.processEvents()
    #         # setup roi table
    #         if 'roi_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
    #             qtutil.critical("There's no roi table associated with this project")
    #             return
    #         text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
    #                           if self.project.files[x]['type'] == 'roi_table']
    #         assert(len(text_file_path) == 1)
    #         text_file_path = text_file_path[0]
    #         roi_table = []
    #         with open(text_file_path, 'rt', encoding='ascii') as csvfile:
    #             roi_table_it = csv.reader(csvfile, delimiter=',')
    #             for row in roi_table_it:
    #                 roi_table = roi_table + [row]
    #         roi_table = np.array(roi_table)
    #         roi_table_range = range(len(roi_table))[1:]
    #         roi_names = [roi_table[x, 0] for x in roi_table_range]
    #         roi_coord_x = [float(roi_table[x, 2]) for x in roi_table_range]
    #         roi_coord_y = [float(roi_table[x, 3]) for x in roi_table_range]
    #         roi_coord_x = [self.convert_coord_to_numpy_reference(x, 'x') for x in roi_coord_x]
    #         roi_coord_y = [self.convert_coord_to_numpy_reference(y, 'y') for y in roi_coord_y]
    #         for i, ind in enumerate(range(len(roi_names))):
    #             callback(i / len(roi_names))
    #             x = roi_coord_x[ind]
    #             y = roi_coord_y[ind]
    #             roi_name = roi_names[ind]
    #             self.spc_to_file(x, y, roi_name, video_path)
    #         callback(1)
    #     global_callback(1)
    #
    # def spc_bulk_clicked_display(self):
    #     global_progress = QProgressDialog('Saving all Requested Maps to Project Dir', 'Abort', 0, 100, self)
    #     global_progress.setAutoClose(True)
    #     global_progress.setMinimumDuration(0)
    #     def global_callback(x):
    #         global_progress.setValue(x * 100)
    #         QApplication.processEvents()
    #     total = len(self.selected_videos)
    #     for selected_vid_no, video_path in enumerate(self.selected_videos):
    #         global_callback(selected_vid_no / total)
    #         progress = QProgressDialog('Generating SPC Map(s) for ' + video_path, 'Abort', 0, 100, self)
    #         progress.setAutoClose(True)
    #         progress.setMinimumDuration(0)
    #         def callback(x):
    #             progress.setValue(x * 100)
    #             QApplication.processEvents()
    #
    #         # for roi in self.view.vb.rois:
    #         #     roi.print('')
    #         #     roi.getROIMask(frames, self.view.vb.img., axes=(1, 2))
    #         # roi_paths = [os.path.normpath(self.project.files[i]['path'])
    #         #              for i in range(len(self.project.files))
    #         #              if self.project.files[i]['type'] == 'roi']
    #         #
    #         # rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
    #         # rois_to_add = [x for x in rois_selected if x not in rois_in_view]
    #         # for roi_to_add in rois_to_add:
    #         #     self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])
    #
    #
    #         # setup roi table
    #         if 'roi_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
    #             qtutil.critical("There's no ROI table associated with this project. "
    #                             "ROIs coordinates are used as seeds to create seed pixel correlation maps")
    #             return
    #         text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
    #                           if self.project.files[x]['type'] == 'roi_table']
    #         assert(len(text_file_path) == 1)
    #         text_file_path = text_file_path[0]
    #         roi_table = []
    #         with open(text_file_path, 'rt', encoding='ascii') as csvfile:
    #             roi_table_it = csv.reader(csvfile, delimiter=',')
    #             for row in roi_table_it:
    #                 roi_table = roi_table + [row]
    #         roi_table = np.array(roi_table)
    #         roi_table_range = range(len(roi_table))[1:]
    #         roi_names = [roi_table[x, 0] for x in roi_table_range]
    #         roi_coord_x = [float(roi_table[x, 2]) for x in roi_table_range]
    #         roi_coord_y = [float(roi_table[x, 3]) for x in roi_table_range]
    #         roi_coord_x = [self.convert_coord_to_numpy_reference(x, 'x') for x in roi_coord_x]
    #         roi_coord_y = [self.convert_coord_to_numpy_reference(y, 'y') for y in roi_coord_y]
    #         rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
    #         for i, roi_name in enumerate(roi_names):
    #             if roi_name in rois_in_view:
    #                 callback(i / len(roi_names))
    #                 x = roi_coord_x[i]
    #                 y = roi_coord_y[i]
    #                 roi_name = roi_names[i]
    #                 self.spc_to_windows(x, y, roi_name, video_path)
    #         callback(1)
    #     global_callback(1)

    def convert_coord_to_numpy_reference(self, coord, dim):
        assert(dim == 'x' or dim == 'y')
        if not self.project['origin']:
            qtutil.critical("No origin set for project")
            return
        pix_per_mm = 1 / self.project['unit_per_pixel']
        coord_pix = coord * pix_per_mm
        if dim == 'x':
            return self.project['origin'][0] + coord_pix
        else:
            return self.project['origin'][1] + coord_pix

    def cm_choice(self, cm_choice):
        self.cm_type = cm_choice

    def vbc_clicked(self, x, y):
        if not self.selected_videos:
            return

        progress_load = MyProgressDialog('Processing...', 'Loading files and processing Seed Pixel Correlation maps. '
                                    'This may take a while for large files.', self)
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        for i, selected in enumerate(self.selected_videos):
            progress_load.setValue((i / len(self.selected_videos)) * 100)
            frames = fileloader.load_npy(selected)
            progress.show()
            spc = calc_spc(frames, x, y, progress)
            progress.close()
            dialog = SPCMapDialog(self.project, selected, spc, self.cm_comboBox.currentText(),
                                  (round(self.min_sb.value(), 2), round(self.max_sb.value(), 2)))
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowStaysOnTopHint)
            dialog.show()
            self.open_dialogs.append(dialog)
        progress_load.close()

    # todo: NOT FINISHED
    def setup_whats_this(self):
        super().setup_whats_this()
        self.spc_from_rois_pb.setWhatsThis("Creates seed pixel correlation maps (SPC) from the seeds selected for each "
                                           "image stack selected. Seeds are taken from the coordinates imported "
                                           "through the import ROIs plugin. SPC maps are automatically saved to file "
                                           "as numpy arrays")

    # def spc_to_windows(self, x, y, name, vid_path):
    #     assert self.selected_videos
    #     # define base name
    #     vid_name = os.path.basename(vid_path)
    #     path_without_ext = os.path.join(self.project.path, vid_name + "_" + name)
    #     # compute spc
    #     progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
    #     spc = calc_spc(vid_path, x, y, progress)
    #     # save to npy
    #     np.save(path_without_ext + '.npy', spc)
    #     dialog_object = SPCMapDialog(self.project, vid_path, spc, self.cm_comboBox.currentText(), name)
    #     dialog_object.show()
    #     self.open_dialogs.append(dialog_object)
    #     spc_col = dialog_object.colorized_spc
    #     # Save as png and jpeg
    #     scipy.misc.toimage(spc_col).save(path_without_ext+'.jpg')


    def spc_to_file(self, spc, name, vid_path):
        assert self.selected_videos
        #define base name
        vid_name = os.path.basename(vid_path)
        path_without_ext = os.path.join(self.project.path, vid_name + "_" + name)
        # save to npy
        np.save(path_without_ext + '.npy', spc)
        dialog_object = SPCMapDialog(self.project, vid_path, spc, self.cm_comboBox.currentText())
        spc_col = dialog_object.colorized_spc
        #Save as png and jpeg
        scipy.misc.toimage(spc_col).save(path_without_ext+'.jpg')

    def spc_to_file(self, x, y, name, vid_path):
        assert self.selected_videos
        #define base name
        vid_name = os.path.basename(vid_path)
        path_without_ext = os.path.join(self.project.path, vid_name + "_" + name)
        # compute spc
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        spc = calc_spc(vid_path, x, y, progress)
        # save to npy
        np.save(path_without_ext + '.npy', spc)
        dialog_object = SPCMapDialog(self.project, vid_path, spc, self.cm_comboBox.currentText())
        spc_col = dialog_object.colorized_spc
        #Save as png and jpeg
        scipy.misc.toimage(spc_col).save(path_without_ext+'.jpg')
        #not working
        #png.from_array(spc_col, 'L').save(path_without_ext+".png")


class SPCMapDialog(QDialog):
    # video_player_scaled_signal = pyqtSignal()
    # video_player_unscaled_signal = pyqtSignal()
    # delete_signal = pyqtSignal()
    # detatch_signal = pyqtSignal()


    def __init__(self, project, video_path, spcmap, cm_type, corr_range, roi_name=None):
        super(SPCMapDialog, self).__init__()
        self.project = project
        self.video_path = video_path
        self.spc = spcmap
        self.cm_type = cm_type
        self.corr_min = corr_range[0]
        self.corr_max = corr_range[1]
        self.setup_ui()
        if roi_name:
            basename, ext = os.path.splitext(os.path.basename(video_path))
            display_name = basename + '_' + roi_name + ext
            self.setWindowTitle(display_name)
        else:
            self.setWindowTitle(os.path.basename(video_path))
        self.colorized_spc = self.colorize_spc(spcmap)
        self.view.show(self.colorized_spc)
        self.view.vb.clicked.connect(self.vbc_clicked)
        self.view.vb.hovering.connect(self.vbc_hovering)

        l = GradientLegend(self.corr_min, self.corr_max, cm_type)
        l.setParentItem(self.view.vb)

    def setup_ui(self):
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.the_label = QLabel()
        hbox.addWidget(self.the_label)
        # hbox.addWidget(QDoubleSpinBox())
        # hbox.addWidget(QDoubleSpinBox())

        vbox.addLayout(hbox)
        self.view = MyGraphicsView(self.project)
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def vbc_clicked(self, x, y):
        progress = MyProgressDialog('SPC Map', 'Recalculating...', self)
        progress.show()
        progress.setValue(0)
        frames = fileloader.load_npy(self.video_path)
        self.spc = calc_spc(frames, x, y, progress)
        self.view.show(self.colorize_spc(self.spc))

    def colorize_spc(self, spc_map):
        spc_map_with_nan = np.copy(spc_map)
        spc_map[np.isnan(spc_map)] = 0
        gradient_range = matplotlib.colors.Normalize(self.corr_min, self.corr_max)
        spc_map = np.ma.masked_where(spc_map == 0, spc_map)
        cmap = matplotlib.cm.ScalarMappable(
          gradient_range, self.cm_type)
        spc_map_color = cmap.to_rgba(spc_map, bytes=True)
        # turn areas outside mask black
        spc_map_color[np.isnan(spc_map_with_nan)] = np.array([0, 0, 0, 1])

        # make regions where RGB values are taken from 0, black. take the top left corner value...

        spc_map_color = spc_map_color.swapaxes(0, 1)
        if spc_map_color.ndim == 2:
          spc_map_color = spc_map_color[:, ::-1]
        elif spc_map_color.ndim == 3:
          spc_map_color = spc_map_color[:, ::-1, :]
        return spc_map_color

    def vbc_hovering(self, x, y):
        x_origin, y_origin = self.project['origin']
        unit_per_pixel = self.project['unit_per_pixel']
        x = x / unit_per_pixel
        y = y / unit_per_pixel
        spc = self.spc.swapaxes(0, 1)
        spc = spc[:, ::-1]
        try:
          value = str(spc[int(x)+int(x_origin), int(y)+int(y_origin)])
        except:
          value = '-'
        self.the_label.setText('Correlation value at crosshair: {}'.format(value))

    # def contextMenuEvent(self, event):
    #     menu = QMenu(self)
    #     submenu1 = menu.addMenu("Open Video Player")
    #     submenu2 = menu.addMenu("Remove Files")
    #     video_player_scaled_action = submenu1.addAction("Scaled (takes time to establish scale)")
    #     video_player_unscaled_action = submenu1.addAction("Unscaled (loads fast)")
    #     delete_action = submenu2.addAction("Delete Permanently")
    #     detatch_action = submenu2.addAction("Detatch from Project")
    #
    #     action = menu.exec_(self.mapToGlobal(event.pos()))
    #     if action == video_player_scaled_action:
    #         self.video_player_scaled_signal.emit()
    #     if action == video_player_unscaled_action:
    #         self.video_player_unscaled_signal.emit()
    #     if action == delete_action:
    #         self.delete_signal.emit()
    #     if action == detatch_action:
    #         self.detatch_signal.emit()



class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Seed pixel correlation map'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def run(self):
        pass
