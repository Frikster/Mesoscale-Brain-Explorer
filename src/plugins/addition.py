#!/usr/bin/env python3

import functools
import sys

import qtutil
from PyQt4.QtGui import *

from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util import project_functions as pfs
from .util import fileloader
import numpy as np
import os
import psutil

class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    example_sb_label = "Example Spinbox"
    example_cb_label = "Example Checkbox"
    # todo: Define labels used as a key to save paramaters to file here

  class Defaults(WidgetDefault.Defaults):
    example_cb_default = True
    example_sb_default = 10
    manip = "addition"
    # todo: Define default values for this plugin and its UI components here

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    # todo: Define global attributes and UI components here
    # example: here a button and spin box are defined
    self.main_button = QPushButton('Addition')
    self.example_sb = QSpinBox()
    self.example_cb = QCheckBox()
    # note the call to WidgetDefault AFTER defining attributes
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    # todo: setup UI component layout and properties here
    # example: here the button is placed before the spinbox and the spinbox
    # is given a input max value of 1000
    # initially, before the spinbox a label is inserted which gets its text from Label class
    self.vbox.addWidget(self.main_button)
    self.example_sb.setMaximum(1000)
    hbox = QHBoxLayout()
    hbox.addWidget(QLabel(self.Labels.example_sb_label))
    hbox.addWidget(QLabel(self.Labels.example_cb_label))
    self.vbox.addLayout(hbox)
    hbox = QHBoxLayout()
    hbox.addWidget(self.example_sb)
    hbox.addWidget(self.example_cb)
    self.vbox.addLayout(hbox)
    self.vbox.addStretch()

  def setup_signals(self):
    super().setup_signals()
    # todo: Setup signals (i.e. what ui components do) here
    # example: main button that activates execute_primary_function when clicked
    self.main_button.clicked.connect(self.execute_primary_function)
    self.example_cb.stateChanged.connect(self.check_box_checker)

  def check_box_checker(self):
      if self.isActiveWindow():
          if self.example_cb.isChecked():
            qtutil.info("Checkbox checked")

  def setup_params(self, reset=False):
      super().setup_params(reset)
      if len(self.params) == 1 or reset:
        # todo: setup plugin paramaters (e.g. UI component starting values) initial values here
        # in this example the default value for the spinbox is associated with the label and saved to file
        self.update_plugin_params(self.Labels.example_sb_label, self.Defaults.example_sb_default)
        self.update_plugin_params(self.Labels.example_cb_label, self.Defaults.example_cb_default)
      # todo: setup where plugin paramaters get their values from
      # in this example the example spinbox gets its value from the param dictionary
      # which is used to access plugin paramaters saved to file
      self.example_sb.setValue(self.params[self.Labels.example_sb_label])
      self.example_cb.setChecked(self.params[self.Labels.example_cb_label])

  def setup_param_signals(self):
      super().setup_param_signals()
      # todo: setup how paramaters (e.g. UI component values) are stored
      # e.g. saving the value after a user changes the spinbox value, keeping it from resetting
      self.example_sb.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                    self.Labels.example_sb_label))
      self.example_cb.stateChanged.connect(self.prepare_cb_for_update)

  def prepare_cb_for_update(self):
      self.update_plugin_params(self.Labels.example_cb_label, self.example_cb.isChecked())

  def execute_primary_function(self, input_paths=None):
      '''Primary function of plugin'''
      if not input_paths:
          if not self.selected_videos:
              return
          else:
              selected_videos = self.selected_videos
      else:
          selected_videos = input_paths
      # use selected_videos which are the paths to stacks the user has selected or have been input from automation

      if not self.example_cb.isChecked():
          qtutil.info('This is only a template. Use it to code from. \n'
                      'Value of spinbox is: ' + str(self.example_sb.value()))
      # todo: insert functionality here

      sb_val = self.example_sb.value()
      two_stacks = []
      for path in selected_videos:
        frames = fileloader.load_npy(path)
        two_stacks = two_stacks + [frames]
        if len(two_stacks) == 2:
            two_stacks = [np.add(two_stacks[0][0:sb_val], two_stacks[1][0:sb_val])]
      frames_added = two_stacks


      output_path = pfs.save_project(selected_videos[0], self.project, frames_added[0], self.Defaults.manip, 'video')
      # refresh_list can be used to refresh an input list that will have particular indices selected,
      # specified content type shown as well as only showing content after a particular plugin manipulation
      pfs.refresh_list(self.project, self.video_list,
                       self.params[self.Labels.video_list_indices_label],
                       self.Defaults.list_display_type,
                       self.params[self.Labels.last_manips_to_display_label])
      # return the output path(s) of this function for automation
      return [output_path]

  def setup_whats_this(self):
      '''Setup custom help messages'''
      # todo: setup custom help messages to aid the user, each tied to one of your UI components.
      # See overridden method for an example
      super().setup_whats_this()
      self.example_sb.setWhatsThis("This does nothing")

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Addition' # Define plugin name here
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

    # todo: over-ride PluginDefault functions here to define custom behaviour
    # (required for automation)

  def check_ready_for_automation(self):
    if not self.widget.example_cb.isChecked():
        return False

    self.summed_filesize = 0
    for path in self.widget.selected_videos:
        self.summed_filesize = self.summed_filesize + os.path.getsize(path)
    self.available = list(psutil.virtual_memory())[1]
    if self.summed_filesize > self.available:
        return False
    return True

  def automation_error_message(self):
    return "Not enough memory or checkbox is unchecked"

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget(None, None))
  w.show()
  app.exec_()
  sys.exit()
