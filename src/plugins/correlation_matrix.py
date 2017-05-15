#!/usr/bin/env python3
from __future__ import print_function

import os
import sys

import pyqtgraph as pg
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import mse_ui_elements as mue
from .util.mygraphicsview import MyGraphicsView
sys.path.append('..')
import qtutil
import pickle
import numpy as np
from scipy import stats
import matplotlib
import uuid
import csv
from pyqtgraph.Qt import QtGui
from .util.plugin import WidgetDefault
from .util.plugin import PluginDefault
from .util.mse_ui_elements import RoiList
from .util.mse_ui_elements import RoiItemModel
import functools
import itertools
import matplotlib.pyplot as plt
import math
from .util.gradient import GradientLegend

def calc_avg(roi, frames, image):
    mask = roi.getROIMask(frames, image, axes=(1, 2))
    masksize = np.count_nonzero(mask)
    roiframes = frames * mask[np.newaxis, :, :]
    roiframes = np.ndarray.sum(np.ndarray.sum(roiframes, axis=1), axis=1)
    return roiframes / masksize

def calc_connectivity(video_path, image, rois):
    frames = fileloader.load_file(video_path)
    avgs = [calc_avg(roi, frames, image) for roi in rois]
    pearson = lambda x, y: stats.pearsonr(x, y)[0]
    return [[pearson(x, y) for x in avgs] for y in avgs]

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        colormap_index_label = "Choose Colormap:"

    class Defaults(WidgetDefault.Defaults):
        colormap_index_default = 1
        roi_list_types_displayed = ['auto_roi', 'roi']
        window_type = 'connectivity_matrix'

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)

        if not project or not isinstance(plugin_position, int):
            return
        self.project = project
        self.view = MyGraphicsView(self.project)
        self.video_list = QListView()
        self.roi_list = QListView()
        self.roi_list.setModel(RoiModel())
        # todo: there is a mismatch in type between RoiModel and RoiItemModel in mse_ui_elements. As such it was easier
        # to abandon the convention of not initializing UI paramaters in init to get it funcitonal. Nonetheless, these
        # next few lines really should be in a class somewhere for the roi_list item
        # for f in project.files:
        #     if f['type'] == self.Defaults.roi_list_types_displayed:
        #         item = QStandardItem(f['name'])
        #         item.setData(f['path'], Qt.UserRole)
        #         self.roi_list.model().appendRow(item)
        self.cm_comboBox = QtGui.QComboBox(self)
        self.save_pb = QPushButton("&Save matrix windows")
        self.load_pb = QPushButton("&Load project matrix windows")
        self.mask_checkbox = QCheckBox("Mask Symmetry")
        self.sem_checkbox = QCheckBox("Use SEM instead of SD")
        self.cm_pb = QPushButton('Correlation &Matrix')
        self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed, RoiModel())
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        self.vbox.addWidget(qtutil.separator())
        self.vbox.addWidget(mue.InfoWidget('Note that rois can be dragged and dropped in the list but that the order '
                                           'in which they are *selected* determines how the matrix is ordered. The '
                                           'first selected ROI is placed at the top of the matrix. '
                                           'Dragging and dropping is for convenience so you can organize your desired '
                                           'order and then shift select them from top to bottom to quickly have your '
                                           'desired matrix ordering.'))

        self.vbox.addWidget(QLabel('Select ROIs:'))
        self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.roi_list.setAcceptDrops(True)
        self.roi_list.setDragEnabled(True)
        self.roi_list.setDropIndicatorShown(True)
        self.roi_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.roi_list.setDefaultDropAction(Qt.MoveAction)
        self.roi_list.setDragDropOverwriteMode(False)
        self.vbox.addWidget(self.roi_list)
        self.vbox.addWidget(QLabel(self.Labels.colormap_index_label))
        # todo: colormap list should be dealt with in a separate script
        self.cm_comboBox.addItem("jet")
        self.cm_comboBox.addItem("viridis")
        self.cm_comboBox.addItem("inferno")
        self.cm_comboBox.addItem("plasma")
        self.cm_comboBox.addItem("magma")
        self.cm_comboBox.addItem("coolwarm")
        self.cm_comboBox.addItem("PRGn")
        self.cm_comboBox.addItem("seismic")
        self.vbox.addWidget(self.cm_comboBox)
        self.vbox.addWidget(self.save_pb)
        self.vbox.addWidget(self.load_pb)
        self.mask_checkbox.setChecked(True)
        self.sem_checkbox.setChecked(False)
        self.vbox.addWidget(self.mask_checkbox)
        self.vbox.addWidget(self.sem_checkbox)
        self.vbox.addWidget(self.cm_pb)

    def setup_signals(self):
        super().setup_signals()
        self.cm_pb.clicked.connect(self.connectivity_triggered)
        self.save_pb.clicked.connect(self.save_triggered)
        self.load_pb.clicked.connect(self.load_triggered)

    def setup_params(self, reset=False):
        super().setup_params(reset)
        self.roi_list.setup_params()
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.colormap_index_label, self.Defaults.colormap_index_default)
        self.cm_comboBox.setCurrentIndex(self.params[self.Labels.colormap_index_label])


    def setup_param_signals(self):
        super().setup_param_signals()
        self.roi_list.setup_param_signals()
        self.cm_comboBox.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.colormap_index_label))

    def selected_roi_changed(self, selected, deselected):
        # todo: how in the world did you know to do this? deselected.indexes only returns one object no matter what -
        # roiname also only ever has one value so this function must be being called multiple times for each
        # selection/deselection
        # todo: what's the point of the forloops?
        for index in deselected.indexes():
            roiname = str(index.data(Qt.DisplayRole))
            self.view.vb.removeRoi(roiname)
        for index in selected.indexes():
            roiname = str(index.data(Qt.DisplayRole))
            roipath = str(index.data(Qt.UserRole))
            self.view.vb.addRoi(roipath, roiname)

    def connectivity_triggered(self):
        cm_type = self.cm_comboBox.currentText()
        progress = QProgressDialog('Generating Correlation Matrix...', 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()

        indexes = self.roi_list.selectionModel().selectedIndexes()
        roinames = [index.data(Qt.DisplayRole) for index in indexes]
        rois = [self.view.vb.getRoi(roiname) for roiname in roinames]
        if not self.view.vb.img:
            qtutil.critical('Select video.')
        elif not rois:
            qtutil.critical('Select Roi(s).')
        else:
            win = ConnectivityDialog(self, roinames, cm_type, progress_callback=callback)
            win.resize(900, 900)
            callback(1)
            win.show()
            self.open_dialogs.append(win)
            self.save_open_dialogs_to_csv()

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

    def save_triggered(self):
        if not self.open_dialogs:
            qtutil.info('No correlation matrix windows are open. ')
            return

        continue_msg = "All Correlation Matrices will be closed after saving, *including* ones you have not saved. \n" \
                  "\n" \
                  "Continue?"
        reply = QMessageBox.question(self, 'Save All',
                                     continue_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        qtutil.info(
            'There are ' + str(len(self.open_dialogs)) + ' correlation matrices in memory. We will now choose a path '
                                                         'to save each one to. Simply don\'t save ones you have '
                                                         'purposefully closed. Though, good news, you now have '
                                                         'one last chance to save and recover any matrices you '
                                                         'accidentally closed')
        for dialog in self.open_dialogs:
            win_title = dialog.windowTitle()
            filters = {
                '.pkl': 'Python pickle file (*.pkl)'
            }
            default = win_title
            pickle_path = self.filedialog(default, filters)
            if pickle_path:
                self.project.files.append({
                    'path': pickle_path,
                    'type': self.Defaults.window_type,
                    'name': os.path.basename(pickle_path)
                })
                self.project.save()

                # for row in dialog.model._data:
                #     for cell in row:
                #         if math.isnan(cell[0]) or math.isnan(cell[0]):
                #             qtutil.warning("File might not save properly since it has nan values. Make sure all your "
                #                            "ROIs are inside your mask.")
                #             break

                # Now save the actual file
                title = os.path.basename(pickle_path)
                matrix_output_data = (title, dialog.model.roinames, dialog.model._data)
                try:
                    with open(pickle_path, 'wb') as output:
                        pickle.dump(matrix_output_data, output, -1)
                except:
                    qtutil.critical(
                        pickle_path + " could not be saved. Ensure MBE has write access to this location and "
                                      "that another program isn't using this file.")

        qtutil.info("All files have been saved")

        csv_msg = "Save csv files of all open Correlation Matrix windows as well?"
        reply = QMessageBox.question(self, 'Save All',
                                     csv_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_open_dialogs_to_csv()

        for dialog in self.open_dialogs:
            dialog.close()
        self.open_dialogs = []

    def load_triggered(self):
        paths = [p['path'] for p in self.project.files if p['type'] == self.Defaults.window_type]
        if not paths:
            qtutil.info("Your project has no correlation matrices. Make and save some!")
            return

        for pickle_path in paths:
            try:
                with open(pickle_path, 'rb') as input:
                    (title, roinames, dat) = pickle.load(input)
            except:
                del_msg = pickle_path + " could not be loaded. If this file exists, " \
                                        "ensure MBE has read access to this " \
                                        "location and that another program isn't using this file " \
                                        "" \
                                        "\n \nOtherwise, would you like to detatch this file from your project? "
                reply = QMessageBox.question(self, 'File Load Error',
                                             del_msg, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    norm_path = os.path.normpath(pickle_path)
                    self.project.files[:] = [f for f in self.project.files if
                                               os.path.normpath(f['path']) != norm_path]
                    self.project.save()
                    load_msg = pickle_path + " detatched from your project." \
                                             "" \
                                             "\n \n Would you like to continue loading the " \
                                             "remaining project matrices?"
                    reply = QMessageBox.question(self, 'Continue?',
                                                 load_msg, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                continue

            main_window = ConnectivityDialog(self, roinames, self.cm_comboBox.currentText(), dat)
            main_window.setWindowTitle(title)
            main_window.resize(900, 900)
            main_window.show()
            self.open_dialogs.append(main_window)

    def save_open_dialogs_to_csv(self):
        if not self.open_dialogs:
            qtutil.info('No correlation matrix windows are open. ')
            return

        for i, dialog in enumerate(self.open_dialogs):
            rois_names = [dialog.model.rois[x].name for x in range(len(dialog.model.rois))]
            file_name_avg = os.path.splitext(os.path.basename(dialog.windowTitle()))[0] + \
                            '_averaged_correlation_matrix.csv'
            file_name_stdev = os.path.splitext(os.path.basename(dialog.windowTitle()))[0] + \
                              '_stdev_correlation_matrix.csv'

            with open(os.path.join(self.project.path, file_name_avg), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(rois_names)
                for row_ind in range(len(dialog.model._data)):
                    row = dialog.model._data[row_ind]
                    row = [row[x][0] for x in range(len(row))]
                    writer.writerow(row)
                writer.writerow(['Selected videos:']+self.selected_videos)
            # Do the standard deviation
            with open(os.path.join(self.project.path, file_name_stdev), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(rois_names)
                for row_ind in range(len(dialog.model._data)):
                    row = dialog.model._data[row_ind]
                    row = [row[x][1] for x in range(len(row))]
                    writer.writerow(row)
                writer.writerow(['Selected videos:'] + self.selected_videos)

    def setup_whats_this(self):
        super().setup_whats_this()
        self.roi_list.setWhatsThis("Choose ROIs where the average value for each frame across frames is used for each "
                                   "selected ROI. This set of values is correlated with the average of all other ROIs "
                                   "to create the correlation matrix. ")
        self.cm_comboBox.setWhatsThis("Choose the colormap used to represent your matrices. Note that we "
                                      "discourage the use of jet. For a discussion on this please see "
                                      "'Why We Use Bad Color Maps and What You Can Do About It.' Kenneth Moreland. "
                                      "In Proceedings of Human Vision and Electronic Imaging")
        self.save_pb.setWhatsThis("Saves the data from all open matrix windows to file and the project. This includes "
                                  "the option to save to csv - one for standard deviation and one for correlation "
                                  "values for each matrix in view")
        self.load_pb.setWhatsThis("Loads all matrix windows associated with this plugin that have been saved. Click "
                                  "'Manage Data' to find each window associated with this project. Individual windows "
                                  "can be deleted from there. ")
        self.cm_pb.setWhatsThis("Creates a single correlation matrix where each correlation matrix from selected "
                                "image stacks are averaged to create a single correlation matrix that has a standard "
                                "deviation displaying how correlation deviates across selected image stacks for each "
                                "ROI. Correlation coefficient used = Pearson")


class ConnectivityModel(QAbstractTableModel):
    def __init__(self, widget, roinames, cm_type, loaded_data=None, progress_callback=None):
        super(ConnectivityModel, self).__init__()
        self.cm_type = cm_type
        self.roinames = roinames

        project = widget.project
        rois = widget.view.vb.rois[:]
        for roi in rois:
            widget.view.vb.removeRoi(roi.name)
        widget.view.vb.currentROIindex = 0
        roipaths = [os.path.join(project.path, roiname + '.roi') for roiname in roinames]
        widget.view.vb.loadROI(roipaths)
        self.rois = [widget.view.vb.getRoi(roiname) for roiname in roinames]

        if loaded_data:
            self._data = loaded_data
        else:
            selected_videos = widget.selected_videos
            image = widget.view.vb.img
            self.matrix_list = []
            avg_data = []
            tot_data = []
            dict_for_stdev = {}

            for key in [i for i in list(itertools.product(range(len(self.rois)), range(len(self.rois))))]:
                dict_for_stdev[key] = []

            for i, video_path in enumerate(selected_videos):
                if progress_callback:
                    progress_callback(i / len(selected_videos))
                self._data = calc_connectivity(video_path, image, self.rois)
                self.matrix_list = self.matrix_list + [self._data]
                if tot_data == []:
                    tot_data = self._data
                if avg_data == []:
                    avg_data = self._data
                for i in range(len(tot_data)):
                    for j in range(len(tot_data)):
                        dict_for_stdev[(i, j)] = dict_for_stdev[(i, j)] + [self._data[i][j]]
                        # ignore half of graph
                        if widget.mask_checkbox.isChecked() and i < j:
                            dict_for_stdev[(i, j)] = [0]
                        # Start above with self._data receiving= the first value before adding on the rest.
                        # don't add the first value twice
                        if os.path.normpath(video_path) != os.path.normpath(selected_videos[0]):
                            tot_data[i][j] = tot_data[i][j] + self._data[i][j]
            # Finally compute averages
            for i in range(len(tot_data)):
                for j in range(len(tot_data)):
                    if progress_callback:
                        progress_callback((i*j) / (len(tot_data)*len(tot_data)))
                    # ignore half of graph
                    if widget.mask_checkbox.isChecked() and i < j:
                        avg_data[i][j] = 0
                    else:
                        avg_data[i][j] = tot_data[i][j] / len(selected_videos)
            if widget.sem_checkbox.isChecked():
                stdev_dict = {k: stats.sem(v) for k, v in dict_for_stdev.items()}
            else:
                stdev_dict = {k: np.std(v) for k, v in dict_for_stdev.items()}
            assert(stdev_dict[(0, 0)] == 0 or math.isnan(stdev_dict[(0, 0)]))

            # combine stddev and avg data
            for i in range(len(avg_data)):
                for j in range(len(avg_data)):
                    if progress_callback:
                        progress_callback((i*j) / (len(avg_data) * len(avg_data)))
                    avg_data[i][j] = (avg_data[i][j], stdev_dict[(i, j)])

            self._data = avg_data
            assert(avg_data != [])

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data)

    def data(self, index, role):
        tup = self._data[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return str(round(tup[0], 2))+" +/- "+str(round(tup[1], 2))
        elif role == Qt.BackgroundRole:
            value = float(tup[0])

            gradient_range = matplotlib.colors.Normalize(-1.0, 1.0)
            cmap = matplotlib.cm.ScalarMappable(
                gradient_range, plt.get_cmap(self.cm_type))
            color = cmap.to_rgba(value, bytes=True)
            # color = plt.cm.jet(value)
            # color = [x * 255 for x in color]
            return QColor(*color)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.rois[section].name
        return

class ConnectivityTable(QTableView):
    def __init__(self, parent=None):
        super(ConnectivityTable, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setMaximumWidth(100)
        self.verticalHeader().setResizeMode(QHeaderView.Stretch)
        self.setMinimumSize(400, 300)

class ConnectivityDialog(QDialog):
    def __init__(self, widget, roinames, cm_type, loaded_data=None, progress_callback=None):
        super(ConnectivityDialog, self).__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('Correlation Matrix - ' + str(uuid.uuid4()))
        self.table = ConnectivityTable()
        self.setup_ui()
        self.model = ConnectivityModel(widget, roinames, cm_type, loaded_data, progress_callback)
        self.table.setModel(self.model)

        # view.setAspectLocked(True)
        win = pg.GraphicsWindow()
        l = GradientLegend(-1.0, 1.0, cm_type)
        win.setFixedSize(l.labelsize)
        view = win.addViewBox()
        l.setParentItem(view)
        win.setParent(self)

    def setup_ui(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.table)
        self.setLayout(vbox)

class RoiModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(RoiModel, self).__init__(parent)

  def supportedDropActions(self):
    return Qt.MoveAction

  def dropMimeData(self, data, action, row, column, parent):
    return super(RoiModel, self).dropMimeData(data, action, row, column, parent)

  def flags(self, index):
    if not index.isValid() or index.row() >= self.rowCount() or index.model() != self:
       return Qt.ItemIsDropEnabled # we allow drops outside the items
    return super(RoiModel, self).flags(index) & (~Qt.ItemIsDropEnabled)

  def removeRows(self, row, count, parent):
    return super(RoiModel, self).removeRows(row, count, parent)

  def insertRows(self, row, count, parent):
    return super(RoiModel, self).insertRows(row, count, parent)


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Correlation Matrix'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def run(self):
        pass
