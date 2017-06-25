#!/usr/bin/env python3
import functools
import os
import pickle
from itertools import cycle
from math import log10, floor

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import qtutil
import scipy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import *

from .util import file_io
from .util import project_functions as pfs
from .util.custom_pyqtgraph_items import GradientLegend
from .util.custom_qt_items import MyProgressDialog
from .util.mygraphicsview import MyGraphicsView
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util.visualization_window import DockWindow


# round_to_n = lambda x, n: round(x, -int(floor(log10(x))) + (n - 1))
def round_sig(x, sig=2):
    return round(x, sig-int(floor(log10(abs(x))))-1)

def calc_stddev(video_path, progress):
  progress.setValue(0)
  frames = file_io.load_file(video_path)
  stddev = np.std(frames, axis=0, dtype=np.float32)
  progress.setValue(100)
  return stddev

def prepare_image(stddev, max_stdev, cm_type):
  stddev[np.isnan(stddev)] = 0.0
  gradient_range = matplotlib.colors.Normalize(0.0, max_stdev)
  image = matplotlib.cm.ScalarMappable(
    gradient_range, cm_type).to_rgba(stddev, bytes=True)
  image = image.swapaxes(0, 1)
  if image.ndim == 2:
    image = image[:, ::-1]
  elif image.ndim == 3:
    image = image[:, ::-1, :]
  return image

class DockWindowSTD(DockWindow):
    def __init__(self, video_path_to_plots_dict, parent, state=None, area=None, title=None):
        super(DockWindowSTD, self).__init__(None, area, title, parent)
        self.state = state
        self.video_path_to_plots_dict = video_path_to_plots_dict
        self.setWhatsThis("Click to recompute for another seed. Click and drag to move the map around "
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
        self.parent = parent
        self.plot_to_docks(self.video_path_to_plots_dict, self.area)
        if state:
            self.area.restoreState(self.state)

    def save_state(self):
        save_loc = super().save_state()
        with open(save_loc, 'rb') as input:
            state = pickle.load(input)
        try:
            with open(save_loc, 'wb') as output:
                pickle.dump([self.video_path_to_plots_dict, state], output, -1)
        except:
            qtutil.critical(save_loc + " failed to save.")
            return

    def load_state(self):
        filenames = QFileDialog.getOpenFileNames(
          self, 'Load images', QSettings().value('last_vis_path'),
          'visualization window pickle (*.pkl)')
        if not filenames:
            return
        QSettings().setValue('last_vis_path', os.path.dirname(filenames[0]))
        for filename in filenames:
            try:
                with open(filename, 'rb') as input:
                    [video_path_to_plots_dict, state] = pickle.load(input)
                    new_dw = DockWindowSTD(video_path_to_plots_dict, parent=self.parent,
                                           state=state, title=os.path.basename(filename))
                    self.parent.open_dialogs.append(new_dw)
                    new_dw.show()
                    new_dw.saving_state[str].connect(functools.partial(pfs.save_dock_window_to_project, self.parent,
                                                                       self.parent.Labels.window_type))
            except:
                qtutil.critical(filename + " failed to open. Aborting.")
                return

    def plot_to_docks(self, video_path_to_spc_dict, area):
        if not video_path_to_spc_dict:
            return
        # roi_names = list(list(video_path_to_spc_dict.values())[0].keys()) # same ROIs used for all stacks
        video_paths = list(video_path_to_spc_dict.keys())

        spc_docks = range(len([i for i in self.area.docks.keys()]))
        spc_docs_cycle = cycle(spc_docks)
        for video_path in video_paths:
            roi_names = video_path_to_spc_dict[video_path]
            for roi_name in roi_names:
                # put all plots from one ROI on a single plot and place on one of the 4 docs
                next_dock = next(spc_docs_cycle)
                d = Dock(roi_name, size=(500, 200), closable=True)
                area.addDock(d, 'above', area.docks['d' + str(next_dock + 1)])

                spc = video_path_to_spc_dict[video_path][roi_name]
                doc_window = StdDevDialog(self.parent.project, video_path, spc, self.parent.cm_comboBox.currentText(),
                                          (round(self.parent.min_sb.value(), 2), round(self.parent.max_sb.value(), 2)),
                                          roi_name)
                root, ext = os.path.splitext(video_path)
                source_name = os.path.basename(root)
                doc_window.setWindowTitle(source_name)
                d.addWidget(doc_window)

                # save to file
                spc_col = doc_window.colorized_spc
                path_without_ext = os.path.join(self.parent.project.path, video_path + "_" + roi_name)
                scipy.misc.toimage(spc_col).save(path_without_ext + "_" + self.parent.cm_comboBox.currentText() +
                                                 '.jpg')
                np.save(path_without_ext + '.npy', spc)
        # close placeholder docks
        for spc_dock in spc_docks:
            area.docks['d'+str(spc_dock+1)].close()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.parent.open_dialogs.remove(self)

class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    colormap_index_label = "Choose Colormap:"
    max_checkbox_label = "Select maximum value of image stack as upper limit"
    colormap_upper_limit_label = "Choose upper limit of colormap:"

  class Defaults(WidgetDefault.Defaults):
    colormap_index_default = 1
    max_checkbox_default = True
    colormap_upper_limit_default = 1.0
    manip = "stdev"

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    self.project = project
    self.view = MyGraphicsView(self.project)
    self.cm_comboBox = QtGui.QComboBox(self)
    self.max_checkbox = QCheckBox("Select maximum value of image stack as upper limit")
    self.log_mode = QCheckBox("Use log scale")
    self.max_stdev_cb = QDoubleSpinBox(decimals=4)
    self.execute_primary_function_button = QPushButton('Generate Std. Dev. Map')
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
    self.vbox.addWidget(self.max_checkbox)
    self.vbox.addWidget(self.log_mode)
    self.vbox.addWidget(QLabel(self.Labels.colormap_upper_limit_label))
    self.max_stdev_cb.setMinimum(0.0000)
    self.max_stdev_cb.setValue(1.0000)
    self.vbox.addWidget(self.max_stdev_cb)
    self.vbox.addWidget(self.execute_primary_function_button)

  def setup_signals(self):
      super().setup_signals()
      self.execute_primary_function_button.clicked.connect(self.execute_primary_function)
      #self.cm_comboBox.activated[str].connect(self.cm_choice)

  def setup_params(self, reset=False):
      super().setup_params(reset)
      if len(self.params) == 1 or reset:
          self.update_plugin_params(self.Labels.colormap_index_label, self.Defaults.colormap_index_default)
          self.update_plugin_params(self.Labels.colormap_upper_limit_label, self.Defaults.colormap_upper_limit_default)
          self.update_plugin_params(self.Labels.max_checkbox_label, self.Defaults.max_checkbox_default)
      self.cm_comboBox.setCurrentIndex(self.params[self.Labels.colormap_index_label])
      self.max_checkbox.setChecked(self.params[self.Labels.max_checkbox_label])
      self.max_stdev_cb.setValue(self.params[self.Labels.colormap_upper_limit_label])

  def setup_param_signals(self):
      super().setup_param_signals()
      self.cm_comboBox.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                          self.Labels.colormap_index_label))
      self.max_stdev_cb.valueChanged[float].connect(functools.partial(self.update_plugin_params,
                                                                self.Labels.colormap_upper_limit_label))
      self.max_checkbox.stateChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                      self.Labels.max_checkbox_label))

  def execute_primary_function(self, input_paths=None):
    cm_type = self.cm_comboBox.currentText()

    global_progress = QProgressDialog('Generating Requested Standard Deviation Maps', 'Abort', 0, 100, self)
    global_progress.setAutoClose(True)
    global_progress.setMinimumDuration(0)
    def global_callback(x):
        global_progress.setValue(x * 100)
        QApplication.processEvents()
    total = len(self.selected_videos)
    for selected_vid_no, video_path in enumerate(self.selected_videos):
        global_callback(selected_vid_no / total)
        progress = MyProgressDialog('Standard Deviation Map', 'Generating map...', self)
        stddev = calc_stddev(video_path, progress)
        if self.log_mode.isChecked():
            stddev = stddev + 1 # log10(1.0) = 0
            stddev = np.log10(stddev)
        if self.max_checkbox.isChecked():
            max_val = str(np.max(stddev))
            dialog = StdDevDialog(self.project, video_path, stddev, np.max(stddev), cm_type, self)
            # stddev_col = dialog.colorized_spc
        else:
            max_val = str(self.max_stdev_cb.value())
            dialog = StdDevDialog(self.project, video_path, stddev, self.max_stdev_cb.value(), cm_type, self)
            dialog.setWhatsThis("Click and drag to move the map around and roll "
                                "the mouse wheel to zoom in and out. Moving the map resets the position of the "
                                "gradient legend. Right click to see further options. Use View All to reset the view. ")
            # stddev_col = dialog.colorized_spc
        self.stdev_to_file(max_val, video_path, dialog.colorized_spc, stddev)
        dialog.show()
        self.open_dialogs.append(dialog)
    global_callback(1)

  def stdev_to_file(self, max_val, vid_path, stddev_col, stddev):
      assert self.selected_videos
      # define base name
      vid_name = os.path.basename(vid_path)
      path_without_ext = os.path.join(self.project.path, vid_name + "_" + 'stdev_with_max_'+max_val)
      # save to npy
      np.save(path_without_ext + '.npy', stddev)
      # Save as png and jpeg
      scipy.misc.toimage(stddev_col).save(path_without_ext + '.jpg')

  def setup_whats_this(self):
      super().setup_whats_this()
      self.cm_comboBox.setWhatsThis("Choose the colormap used to represent your maps. Note that we "
                                    "discourage the use of jet. For a discussion on this please see "
                                    "'Why We Use Bad Color Maps and What You Can Do About It.' Kenneth Moreland. "
                                    "In Proceedings of Human Vision and Electronic Imaging")
      self.max_checkbox.setWhatsThis("If checked the highest standard deviation value found for a particular plot "
                                     "will be used as the upper limit in the range. This will be reflected in the "
                                     "gradient legend")
      self.max_stdev_cb.setWhatsThis("Set the highest standard deviation that will be represented on your map and "
                                     "therefore the upper limit of the gradient range. standard deviations above this "
                                     "value will all have the same colour")
      self.execute_primary_function_button.setWhatsThis("Create standard deviation map of selected image stacks with "
                                                        "upper")

class StdDevDialog(QDialog):
  def __init__(self, project, video_path, stddevmap, max_stdev, cm_type, parent=None):
    super(StdDevDialog, self).__init__(parent)
    self.project = project
    self.display_name = os.path.basename(video_path)
    self.video_path = video_path
    self.stddev = stddevmap
    self.max_stdev = max_stdev
    self.cm_type = cm_type
    self.setup_ui()
    l = GradientLegend(0.0, max_stdev, cm_type)
    l.setParentItem(self.view.vb)
    self.setWindowTitle('Standard Deviation Map')
    self.colorized_spc = self.colorize_spc(stddevmap)
    self.view.show(self.colorize_spc(stddevmap))

    # self.view.show(prepare_image(stddevmap, max_stdev, cm_type))
    self.view.vb.hovering.connect(self.vbc_hovering)

  def setup_ui(self):
    vbox = QVBoxLayout()
    # hbox = QHBoxLayout()
    self.the_label = QLabel()
    self.coords_label = QLabel()
    vbox.addWidget(QLabel(self.display_name))
    vbox.addWidget(self.the_label)
    vbox.addWidget(self.coords_label)
    # vbox.addLayout(hbox)
    self.view = MyGraphicsView(self.project)
    vbox.addWidget(self.view)
    self.setLayout(vbox)

  def vbc_hovering(self, x, y):
    coords = str((format(x, '.4f'), format(y, '.4f')))
    x_origin, y_origin = self.project['origin']
    unit_per_pixel = self.project['unit_per_pixel']
    x = x / unit_per_pixel
    y = y / unit_per_pixel
    stddev = self.stddev.swapaxes(0, 1)
    stddev = stddev[:, ::-1]
    try:
        # value = str(round_sig(stddev[int(x) + int(x_origin), int(y) + int(y_origin)], 4))
        value = str(format(stddev[int(x)+int(x_origin), int(y)+int(y_origin)], '.8f'))
        # value = str(stddev[int(x)+int(x_origin), int(y)+int(y_origin)])
    except:
        value = '-'
    self.the_label.setText('Standard deviation at crosshair: {}'.format(value))
    self.coords_label.setText('(x,y): {}'.format(coords))

  # copy-pasted from spc_map
  def colorize_spc(self, spc_map):
      spc_map_with_nan = np.copy(spc_map)
      spc_map[np.isnan(spc_map)] = 0
      gradient_range = matplotlib.colors.Normalize(0, self.max_stdev)
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

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Standard deviation map'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def run(self):
    pass
