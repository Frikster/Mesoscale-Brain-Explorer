#!/usr/bin/env python3

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.UIGraphicsItem import *

from .util import filter_jeff
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView, MyProgressDialog, InfoWidget
from .util.gradient import GradientLegend
from .util import mse_ui_elements as mue
from .util import project_functions as pfs

from .util import fileloader

import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import qtutil
import csv
import scipy.misc
import math
import multiprocessing

def calc_spc(video_path, x, y, progress):
    frame = fileloader.load_reference_frame(video_path)
    width, height = frame.shape

    x = int(x)
    y = int(height - y)

    frames = fileloader.load_file(video_path)

    spc_map = filter_jeff.correlation_map(y, x, frames, progress)

    # Make the location of the seed - self.image[y,x] - blatantly obvious
    spc_map[y+1, x+1] = 1
    spc_map[y+1, x] = 1
    spc_map[y, x+1] = 1
    spc_map[y-1, x-1] = 1
    spc_map[y-1, x] = 1
    spc_map[y, x-1] = 1
    spc_map[y+1, x-1] = 1
    spc_map[y-1, x+1] = 1

    return spc_map

class SeedItemModel(QAbstractListModel):
    textChanged = pyqtSignal(str, str)

    # dataChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(SeedItemModel, self).__init__(parent)
        self.seeds = []

    def appendseed(self, name):
        self.seeds.append(name)
        row = len(self.seeds) - 1
        self.dataChanged.emit(self.index(row), self.index(row))

    def edit_seed_name(self, name, index):
        self.seeds.append(name)
        row = len(self.seeds) - 1
        self.dataChanged.emit(self.index(row), self.index(row))

    def rowCount(self, parent):
        return len(self.seeds)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.seeds[index.row()]
        return

    def setData(self, index, value, role):
        if role in [Qt.DisplayRole, Qt.EditRole]:
            self.textChanged.emit(self.seeds[index.row()], value)
            self.seeds[index.row()] = str(value)
            return True
        return super(SeedItemModel, self).setData(index, value, role)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def removeRow(self, seed_to_remove):
        for seed in self.seeds:
            if seed == seed_to_remove:
                del seed
                break

class SPCMapDialog(QDialog):
    def __init__(self, project, video_path, spcmap, cm_type, parent=None):
        super(SPCMapDialog, self).__init__(parent)
        self.project = project
        self.video_path = video_path
        self.spc = spcmap
        self.cm_type = cm_type
        self.setup_ui()
        self.setWindowTitle('SPC')
        self.colorized_spc = self.colorize_spc(spcmap)
        self.view.show(self.colorized_spc)
        self.view.vb.clicked.connect(self.vbc_clicked)
        self.view.vb.hovering.connect(self.vbc_hovering)

        l = GradientLegend(-1.0, 1.0, cm_type)
        l.setParentItem(self.view.vb)

    def setup_ui(self):
        vbox = QVBoxLayout()
        self.the_label = QLabel()
        vbox.addWidget(self.the_label)
        self.view = MyGraphicsView(self.project)
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def vbc_clicked(self, x, y):
        progress = MyProgressDialog('SPC Map', 'Recalculating...', self)
        self.spc = calc_spc(self.video_path, x, y, progress)
        self.view.show(self.colorize_spc(self.spc))

    def colorize_spc(self, spc_map):
        spc_map_with_nan = np.copy(spc_map)
        spc_map[np.isnan(spc_map)] = 0
        gradient_range = matplotlib.colors.Normalize(-1.0, 1.0)
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

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
          return
        self.project = project

        # define Widgets and data
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.cm_comboBox = QtGui.QComboBox(self)
        self.seed_list = QListView()
        self.left = QFrame()
        self.right = QFrame()

        self.setup_ui()
        self.cm_type = self.cm_comboBox.itemText(0)

        self.open_dialogs = []
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        for f in project.files:
          if f['type'] != 'video':
            continue
          self.video_list.model().appendRow(QStandardItem(f['name']))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        self.cm_comboBox.activated[str].connect(self.cm_choice)
        self.view.vb.clicked.connect(self.vbc_clicked)

        # setup ROI list widget
        model = SeedItemModel()
        self.seed_list.setModel(model)
        self.seed_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # A flag to see whether selected_seed_changed is being entered for the first time
        self.selected_seed_changed_flag = 0
        self.seed_list.selectionModel().selectionChanged[QItemSelection,
                                                        QItemSelection].connect(self.selected_seed_changed)
        seed_names = [f['name'] for f in project.files if f['type'] == 'seed']
        for seed_name in seed_names:
            if seed_name not in self.seed_list.model().seeds:
                model.appendseed(seed_name)
        self.seed_list.setCurrentIndex(model.index(0, 0))

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
        vbox.addWidget(self.video_list)
        vbox.addWidget(QLabel('Choose colormap:'))
        self.cm_comboBox.addItem("jet")
        self.cm_comboBox.addItem("viridis")
        self.cm_comboBox.addItem("inferno")
        self.cm_comboBox.addItem("plasma")
        self.cm_comboBox.addItem("magma")
        self.cm_comboBox.addItem("seismic")
        self.cm_comboBox.addItem("rainbow")
        vbox.addWidget(self.cm_comboBox)
        vbox.addWidget(qtutil.separator())
        vbox.addWidget(QLabel('seeds'))
        vbox.addWidget(self.seed_list)
        pb = QPushButton('Generate SPC maps from selected seeds')
        pb.clicked.connect(self.spc_bulk_clicked)
        vbox.addWidget(pb)
        vbox.addStretch()
        vbox.addWidget(mue.InfoWidget('Click on the image to generate custom SPC map.'))
        self.right.setLayout(vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item)

    def selected_seed_changed(self, selection):
        if self.selected_seed_changed_flag == 0:
            self.selected_seed_changed_flag = self.selected_seed_changed_flag + 1
            return
        if not selection.indexes() or self.view.vb.drawROImode:
            return

        self.remove_all_seeds()
        seeds_selected = [str(self.seed_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
                         for x in range(len(self.seed_list.selectionModel().selectedIndexes()))]
        seeds_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
        seeds_to_add = [x for x in seeds_selected if x not in seeds_in_view]
        for seed_to_add in seeds_to_add:
            self.view.vb.loadROI([self.project.path + '/' + seed_to_add + '.seed'])

    def remove_all_seeds(self):
        seeds = self.view.vb.rois[:]
        for seed in seeds:
            if not seed.isSelected:
                self.view.vb.selectROI(seed)
            self.view.vb.removeROI()

    def spc_bulk_clicked(self):
        global_progress = QProgressDialog('Saving all Requested Maps to Project Dir', 'Abort', 0, 100, self)
        global_progress.setAutoClose(True)
        global_progress.setMinimumDuration(0)
        def global_callback(x):
            global_progress.setValue(x * 100)
            QApplication.processEvents()

        for selected_vid_no, video_path in enumerate(self.selected_videos):
            global_callback(selected_vid_no / (len(self.selected_videos)))
            progress = QProgressDialog('Generating SPC Map(s) for ' + video_path, 'Abort', 0, 100, self)
            progress.setAutoClose(True)
            progress.setMinimumDuration(0)
            def callback(x):
                progress.setValue(x * 100)
                QApplication.processEvents()
            # setup seed table
            if 'seed_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
                qtutil.critical("There's no seed table associated with this project")
                return
            text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
                              if self.project.files[x]['type'] == 'seed_table']
            assert(len(text_file_path) == 1)
            text_file_path = text_file_path[0]
            seed_table = []
            with open(text_file_path, 'rt', encoding='ascii') as csvfile:
                seed_table_it = csv.reader(csvfile, delimiter=',')
                for row in seed_table_it:
                    seed_table = seed_table + [row]
            seed_table = np.array(seed_table)
            seed_table_range = range(len(seed_table))[1:]
            seed_names = [seed_table[x, 0] for x in seed_table_range]
            seed_coord_x = [float(seed_table[x, 1]) for x in seed_table_range]
            seed_coord_y = [float(seed_table[x, 2]) for x in seed_table_range]
            seed_coord_x = [self.convert_coord_to_numpy_reference(x, 'x') for x in seed_coord_x]
            seed_coord_y = [self.convert_coord_to_numpy_reference(y, 'y') for y in seed_coord_y]
            for i, ind in enumerate(range(len(seed_names))):
                callback(i / len(seed_names))
                x = seed_coord_x[ind]
                y = seed_coord_y[ind]
                seed_name = seed_names[ind]
                self.spc_to_file(x, y, seed_name, video_path)
            callback(1)
        global_callback(1)

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

    def selected_video_changed(self, selected, deselected):
        if not selected.indexes():
            return

        for index in deselected.indexes():
            vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
            self.selected_videos = [x for x in self.selected_videos if x != vidpath]
        for index in selected.indexes():
            vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
            if vidpath not in self.selected_videos and vidpath != 'None':
                self.selected_videos = self.selected_videos + [vidpath]

        self.shown_video_path = str(os.path.join(self.project.path,
                                           selected.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.shown_video_path)
        self.view.show(frame)

    def vbc_clicked(self, x, y):
        assert self.selected_videos
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        spc = calc_spc(self.selected_videos[0], x, y, progress)
        dialog = SPCMapDialog(self.project, self.shown_video_path, spc, self.cm_type, self)
        dialog.show()
        self.open_dialogs.append(dialog)

    def spc_to_file(self, x, y, name, vid_path):
        assert self.selected_videos
        #define base name
        vid_name = vid_name = os.path.basename(vid_path)
        path_without_ext = os.path.join(self.project.path, vid_name + "_" + name)
        # compute spc
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        spc = calc_spc(vid_path, x, y, progress)
        # save to npy
        np.save(path_without_ext + '.npy', spc)
        dialog_object = SPCMapDialog(self.project, vid_path, spc, self.cm_type, self)
        spc_col = dialog_object.colorized_spc
        #Save as png and jpeg
        scipy.misc.toimage(spc_col).save(path_without_ext+'.jpg')
        #not working
        #png.from_array(spc_col, 'L').save(path_without_ext+".png")


class MyPlugin:
    def __init__(self, project):
        self.name = 'SPC map'
        self.widget = Widget(project)

    def run(self):
        pass
