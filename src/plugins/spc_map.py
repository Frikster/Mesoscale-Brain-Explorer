#!/usr/bin/env python3

import csv
import functools
import os
import uuid
from itertools import cycle
from math import log10, floor

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import qtutil
import scipy.misc
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import *

from .util import file_io
from .util import filter_jeff
from .util import custom_qt_items as cqt
from .util import project_functions as pfs
from .util.custom_pyqtgraph_items import GradientLegend
from .util.custom_qt_items import RoiList
from .util.mygraphicsview import MyGraphicsView
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util.custom_qt_items import MyProgressDialog

# round_to_n = lambda x, n: round(x, -int(floor(log10(x))) + (n - 1))

def round_sig(x, sig=2):
    return round(x, sig-int(floor(log10(abs(x))))-1)

UUID_SIZE = len(str(uuid.uuid4()))


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

class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        colormap_index_label = "Choose Colormap:"
        sb_min_label = "Min correlation value to display"
        sb_max_label = "Max correlation value to display"
        avg_maps_label = "Average maps of selected stacks"

    class Defaults(WidgetDefault.Defaults):
        colormap_index_default = 1
        roi_list_types_displayed = ['auto_roi']
        manip = "spc"
        sb_min_default = -1.00
        sb_max_default = 1.00
        avg_maps_default = False

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)
        if not project or not isinstance(plugin_position, int):
            return
        self.project = project

        # define Widgets and data
        self.view = MyGraphicsView(self.project)
        self.cm_comboBox = QtGui.QComboBox(self)
        self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed)
        self.save_pb = QPushButton("&Save spc windows")
        self.load_pb = QPushButton("&Load project spc windows")
        self.bulk_background_pb = QPushButton('Save all SPC maps from table ROIs to file')
        self.spc_from_rois_pb = QPushButton('Generate SPC maps')
        self.open_dialogs_data_dict = []
        self.min_sb = QDoubleSpinBox()
        self.max_sb = QDoubleSpinBox()
        self.avg_maps_cb = QCheckBox(self.Labels.avg_maps_label)
        self.cm_type = self.cm_comboBox.itemText(0)
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        self.vbox.addWidget(QLabel(self.Labels.colormap_index_label))
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
        self.vbox.addWidget(QLabel('Seeds'))
        self.vbox.addWidget(self.roi_list)
        self.vbox.addWidget(self.save_pb)
        self.vbox.addWidget(self.load_pb)
        self.vbox.addWidget(self.avg_maps_cb)
        self.vbox.addWidget(self.spc_from_rois_pb)
        self.vbox.addStretch()
        self.vbox.addWidget(cqt.InfoWidget('You can also click on the image to right to generate custom SPC maps of '
                                           'all image stacks selected in the list above.'))

    def setup_signals(self):
        super().setup_signals()
        self.view.vb.clicked.connect(self.vbc_clicked)
        self.spc_from_rois_pb.clicked.connect(self.spc_triggered)
        self.save_pb.clicked.connect(self.save_dock_windows)
        self.load_pb.clicked.connect(self.load_dock_windows)

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

        progress_load = MyProgressDialog('Processing...', 'Loading files and processing Seed Pixel Correlation maps. '
                                    'This may take a while for large files.', parent=self)
        video_path_to_plots_dict = {}
        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        for selected_vid_no, video_path in enumerate(selected_videos):
            frames = file_io.load_file(video_path)
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
        # roi_names = list(list(video_path_to_spc_dict.values())[0].keys()) # same ROIs used for all stacks
        video_paths = list(video_path_to_spc_dict.keys())

        spc_docks = [0, 1, 2, 3, 4, 5]
        spc_docs_cycle = cycle(spc_docks)
        for video_path in video_paths:
            roi_names = video_path_to_spc_dict[video_path]
            for roi_name in roi_names:
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
                                   ". Click Shift+F1 for help")
        main_window.setWhatsThis("Click to recompute for another seed. Click and drag to move the map around "
                                 "and roll the mouse wheel to zoom in and out. Moving the map resets the "
                                 "position of the gradient legend. Right click to see further options. "
                                 "Use View All to rest a view.\n"
                                 "\n"
                                 "The blue tabs have the name of the seed for a particular map. These tabs can be "
                                 "dragged "
                                 "around to highlighted regions to the side of other tabs to split the dock or on "
                                 "top of "
                                 "other plots to place the tab in that dock. \n"
                                 "\n"
                                 "Use export to save a particular map's data to various image formats. "
                                 "Note that .jpg and numpy arrays of maps are automatically saved and can be found in "
                                 "your project directory")

        video_path_to_spc_dict = self.get_video_path_to_spc_dict()
        if self.avg_maps_cb.isChecked():
            roi_name_to_spcs_dict = {}
            for path in video_path_to_spc_dict.keys():
               for roi_name in video_path_to_spc_dict[path].keys():
                   try:
                       roi_name_to_spcs_dict[roi_name]
                   except:
                       roi_name_to_spcs_dict[roi_name] = [video_path_to_spc_dict[path][roi_name]]
                   else:
                       roi_name_to_spcs_dict[roi_name] = roi_name_to_spcs_dict[roi_name] + \
                                                         video_path_to_spc_dict[path][roi_name]
            roi_name_roi_name_to_spcs_dict = {}
            for roi_name in roi_name_to_spcs_dict.keys():
                roi_name_to_spcs_dict[roi_name] = roi_name_to_spcs_dict[roi_name] / len(video_path_to_spc_dict.keys())
                roi_name_roi_name_to_spcs_dict[roi_name] = {roi_name: roi_name_to_spcs_dict[roi_name][0]}
            self.plot_to_docks(roi_name_roi_name_to_spcs_dict, area)
        else:
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
            frames = file_io.load_npy(selected)
            progress.show()
            spc = calc_spc(frames, x, y, progress)
            progress.close()
            dialog = SPCMapDialog(self.project, selected, spc, self.cm_comboBox.currentText(),
                                  (round(self.min_sb.value(), 2), round(self.max_sb.value(), 2)))
            dialog.setWhatsThis("Click to recompute for another seed. Click and drag to move the map around and roll "
                                "the mouse wheel to zoom in and out. Moving the map resets the position of the "
                                "gradient legend. Right click to see further options. Use View All to reset the view. ")
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowStaysOnTopHint)
            dialog.show()
            self.open_dialogs.append(dialog)
        progress_load.close()

    # todo: NOT FINISHED
    def setup_whats_this(self):
        super().setup_whats_this()
        self.cm_comboBox.setWhatsThis("Choose the colormap used to represent your maps. Note that we "
                                      "discourage the use of jet. For a discussion on this please see "
                                      "'Why We Use Bad Color Maps and What You Can Do About It.' Kenneth Moreland. "
                                      "In Proceedings of Human Vision and Electronic Imaging")
        self.min_sb.setWhatsThis("Choose the correlation value at the lower end of your colormap range. Correlation "
                                 "values below this value will all be the same color")
        self.max_sb.setWhatsThis("Choose the correlation value at the upper end of your colormap range. Correlation "
                                 "values above this value will all be the same color")
        self.roi_list.setWhatsThis("Choose your square ROIs whose central coordinates will be used as seed pixels to "
                                   "create seed pixel correlation maps. Note that the ROIs in this list must be "
                                   "imported via csv that defines their coordinates. Ensure your pixel width is "
                                   "correct and that its units agree with the units of the coordinates of these ROIs")
        self.save_pb.setWhatsThis("Saves the data from all open plot windows to file and the project. Each window can "
                                  "receive a custom name allowing for sets of analysis to occur on different windows "
                                  "with different data plotted.")
        self.load_pb.setWhatsThis("Loads all spc windows associated with this plugin that have been saved. Click "
                                  "'Manage Data' to find each window associated with this project. Individual windows "
                                  "can be deleted from there. ")
        self.spc_from_rois_pb.setWhatsThis("Creates seed pixel correlation maps (SPC) from the seeds selected for each "
                                           "image stack selected. Seeds are taken from the coordinates imported "
                                           "through the import ROIs plugin. SPC maps are automatically saved to file "
                                           "as numpy arrays and jpegs")


class SPCMapDialog(QDialog):
    def __init__(self, project, video_path, spcmap, cm_type, corr_range, roi_name=None):
        super(SPCMapDialog, self).__init__()
        if roi_name:
            basename, ext = os.path.splitext(os.path.basename(video_path))
            self.display_name = basename + '_' + roi_name + ext
            # self.setWindowTitle(display_name)
        else:
            self.display_name = os.path.basename(video_path)
            # self.setWindowTitle(os.path.basename(video_path))

        self.project = project
        self.video_path = video_path
        self.spc = spcmap
        self.cm_type = cm_type
        self.corr_min = corr_range[0]
        self.corr_max = corr_range[1]
        self.setup_ui()
        # self.title = pg.LabelItem(text=display_name, parent=self.view.vb)
        # self.view.vb.addItem(self.title)
        # todo: add self.display_name to viewbox title not windowTitle
        self.colorized_spc = self.colorize_spc(spcmap)
        self.view.show(self.colorized_spc)
        self.view.vb.clicked.connect(self.vbc_clicked)
        self.view.vb.hovering.connect(self.vbc_hovering)

        l = GradientLegend(self.corr_min, self.corr_max, cm_type)
        l.setParentItem(self.view.vb)

    def setup_ui(self):
        vbox = QVBoxLayout()
        # hbox = QHBoxLayout()
        self.the_label = QLabel()
        self.coords_label = QLabel()
        vbox.addWidget(QLabel(self.display_name))
        vbox.addWidget(self.the_label)
        vbox.addWidget(self.coords_label)

        image_view_on = True
        parent = None
        self.view = MyGraphicsView(self.project, parent, image_view_on)
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def vbc_clicked(self, x, y):
        progress = MyProgressDialog('SPC Map', 'Recalculating...', self)
        progress.show()
        progress.setValue(0)
        frames = file_io.load_npy(self.video_path)
        self.spc = calc_spc(frames, x, y, progress)
        self.view.show(self.colorize_spc(self.spc))

    def colorize_spc(self, spc_map):
        spc_map_with_nan = np.copy(spc_map)
        spc_map[np.isnan(spc_map)] = 0
        gradient_range = matplotlib.colors.Normalize(self.corr_min, self.corr_max)
        spc_map = np.ma.masked_where(spc_map == 0, spc_map)
        cmap = matplotlib.cm.ScalarMappable(
          gradient_range, plt.get_cmap(self.cm_type))
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
        coords = str((format(x, '.4f'), format(y, '.4f')))
        x_origin, y_origin = self.project['origin']
        unit_per_pixel = self.project['unit_per_pixel']
        x = x / unit_per_pixel
        y = y / unit_per_pixel
        spc = self.spc.swapaxes(0, 1)
        spc = spc[:, ::-1]
        try:
          # value = str(round_sig(spc[int(x)+int(x_origin), int(y)+int(y_origin)], 4))
          value = str(format(spc[int(x)+int(x_origin), int(y)+int(y_origin)], '.4f'))
          # value = str(round(spc[int(x)+int(x_origin), int(y)+int(y_origin)], 4))
        except:
          value = '-'
          coords = '(-,-)'
        self.the_label.setText('Correlation value at crosshair: {}'.format(value))
        self.coords_label.setText('(x,y): {}'.format(coords))


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Seed pixel correlation map'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def run(self):
        pass
