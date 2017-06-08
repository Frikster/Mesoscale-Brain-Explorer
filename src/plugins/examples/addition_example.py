#!/usr/bin/env python3

import csv
import os
import sys
from shutil import copyfile

import qtutil
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import *

from src.plugins.util import file_io
from src.plugins.util import project_functions as pfs
from src.plugins.util.plugin import PluginDefault
from src.plugins.util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    add_list_path_label = 'add_list_path'
    add_list_index_label = 'Select Additions'
    # todo: Define labels used as a key to save paramaters to file here

  class Defaults(WidgetDefault.Defaults):
    add_list_path_default = QSettings().value('last_load_text_path')
    add_list_index_default = [0]
    list_display_type = ['video', 'tutorial_stack']
    # todo: Define default values for this plugin and its UI components here

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    # todo: Define global attributes and UI components here
    # example: here a button and spin box are defined
    self.add_btn = QPushButton('Perform Addition')
    self.import_additions_btn = QPushButton('Import List of Additions')
    self.add_list = QListWidget()
    self.selected_videos_list = QListWidget()
    self.selected_add_list = QListWidget()
    self.text_file_path = self.Defaults.add_list_path_default
    # note the call to WidgetDefault AFTER defining attributes
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    # todo: setup UI component layout and properties here
    hbox = QHBoxLayout()
    hbox.addWidget(QLabel(self.Labels.add_list_index_label))
    hbox.addWidget(QLabel('Selected Stacks'))
    hbox.addWidget(QLabel('Selected Additions'))
    self.vbox.addLayout(hbox)
    hbox = QHBoxLayout()
    hbox.addWidget(self.add_list)
    hbox.addWidget(self.selected_videos_list)
    hbox.addWidget(self.selected_add_list)
    self.vbox.addLayout(hbox)
    self.add_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.vbox.addWidget(self.import_additions_btn)
    self.vbox.addStretch()
    self.vbox.addWidget(self.add_btn)

  def setup_signals(self):
    super().setup_signals()
    # todo: Setup signals (i.e. what ui components do) here
    self.add_btn.clicked.connect(self.execute_primary_function)
    self.import_additions_btn.clicked.connect(self.import_additions)
    self.add_list.selectionModel().selectionChanged.connect(self.add_selection_to_selected_add_list)
    self.video_list.selectionModel().selectionChanged.connect(self.add_selection_to_selected_video_list)

  def setup_params(self, reset=False):
      super().setup_params(reset)
      if len(self.params) == 1 or reset:
        # todo: setup plugin parameter (e.g. UI component starting values) initial values here
        self.update_plugin_params(self.Labels.add_list_index_label, self.Defaults.add_list_index_default)
        self.update_plugin_params(self.Labels.add_list_path_label, self.Defaults.add_list_path_default)
      # todo: setup where plugin parameters get their values from
      self.import_additions(self.params[self.Labels.add_list_path_label])
      add_list_indices = self.params[self.Labels.add_list_index_label]
      pfs.refresh_list(self.project, self.add_list, add_list_indices)

  def setup_param_signals(self):
      super().setup_param_signals()
      # todo: setup how UI component interaction triggers paramater storing
      self.add_list.selectionModel().selectionChanged.connect(self.update_add_list_index)

  def update_add_list_index(self, selected, deselected):
      val = [v.row() for v in self.add_list.selectedIndexes()]
      self.update_plugin_params(self.Labels.add_list_index_label, val)

  def add_selection_to_selected_add_list(self, selected, deselected):
      self.selected_add_list.clear()
      self.selected_add_list.addItems([index.data() for index in self.add_list.selectedIndexes()])

  def add_selection_to_selected_video_list(self, selected, deselected):
      self.selected_videos_list.clear()
      self.selected_videos_list.addItems([index.data() for index in self.video_list.selectedIndexes()])

  def import_additions(self, text_file_path=None):
      if not text_file_path:
          text_file_path = QFileDialog.getOpenFileName(
              self, 'Load images', QSettings().value('last_load_text_path'),
              'Video files (*.csv *.txt)')
          if not text_file_path:
              return
          QSettings().setValue('last_load_text_path', os.path.dirname(text_file_path))
          copyfile(text_file_path, os.path.join(self.project.path, os.path.basename(text_file_path)))
          text_file_path = os.path.join(self.project.path, text_file_path)
          self.update_plugin_params(self.Labels.add_list_path_label, text_file_path)

      if text_file_path.endswith('csv') or text_file_path.endswith('txt'):
          add_list = []
          with open(text_file_path, 'rt', encoding='ascii') as csvfile:
             add_list_it = csv.reader(csvfile)
             for row in add_list_it:
                add_list = add_list + row
          self.add_list.addItems(add_list)

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
      # todo: insert functionality here
      if not len(self.add_list.selectedIndexes()) == len(selected_videos):
          qtutil.info('Select the same number of image stacks and additions to apply')
          return
      output_paths = []
      for add_num_item, video_path in zip(self.add_list.selectedIndexes(), selected_videos):
          frames = file_io.load_file(video_path)
          frames = frames + int(add_num_item.data())  # note that memory mapping is recommended for large files.
          path = pfs.save_project(video_path, self.project, frames, 'custom-addition-'+add_num_item.data(),
                                  'video')
          output_paths = output_paths + [path]

      # refresh_list can be used to refresh an input list that will have particular indices selected,
      # specified content type shown as well as only showing content after a particular plugin manipulation
      pfs.refresh_list(self.project, self.video_list,
                       self.params[self.Labels.video_list_indices_label],
                       self.Defaults.list_display_type,
                       self.params[self.Labels.last_manips_to_display_label])
      # return the output path(s) of this function for automation
      return output_paths

  def setup_whats_this(self):
      '''Setup custom help messages'''
      # todo: setup custom help messages to aid the user, each tied to one of your UI components.
      # See overridden method for an example
      super().setup_whats_this()
      self.selected_add_list.setWhatsThis("Additions in this list will be applied to the matching stack in the center "
                                          "list")

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Addition Plugin' # Define plugin name here
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  # todo: over-ride PluginDefault functions here to define custom behaviour
  # (required for automation)
  def check_ready_for_automation(self, expected_input_number):
     if len(self.widget.add_list.selectedIndexes()) == expected_input_number:
         return True
     else:
         return False

  def automation_error_message(self):
     return "Plugin " + self.name + " cannot work if the number of selected additions do not equal the number of " \
                                    "selected image stacks"

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget(None, None))
  w.show()
  app.exec_()
  sys.exit()