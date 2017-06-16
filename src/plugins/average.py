#!/usr/bin/env python3

import sys

import numpy as np
from PyQt4.QtGui import *

from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    pass

  class Defaults(WidgetDefault.Defaults):
    pass

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    self.main_button = QPushButton('Average stack into one frame')
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    self.vbox.addStretch()
    self.vbox.addWidget(self.main_button)

  def setup_signals(self):
    super().setup_signals()
    self.main_button.clicked.connect(self.execute_primary_function)


  def execute_primary_function(self, input_paths=None):
      '''Primary function of plugin'''
      if not input_paths:
          if not self.selected_videos:
              return
          else:
              selected_videos = self.selected_videos
      else:
          selected_videos = input_paths

      for i, video_path in enumerate(selected_videos):
          # find size, assuming all files in project have the same size
          frames_mmap = np.load(video_path, mmap_mode='c')
          frame = np.mean(frames_mmap, axis=0, dtype=np.float32)
          frame_no, h, w = frames_mmap.shape
          frame = np.reshape(frame, (1, h, w))
          pfs.save_project(video_path, self.project, frame, 'avg', 'video')
          pfs.refresh_list(self.project, self.video_list,
                           self.params[self.Labels.video_list_indices_label],
                           self.Defaults.list_display_type,
                           self.params[self.Labels.last_manips_to_display_label])

      # return the output path(s) of this function for automation
      # return output_paths

  def setup_whats_this(self):
      '''Setup custom help messages'''
      # todo: setup custom help messages to aid the user, each tied to one of your UI components.
      # See overridden method for an example
      super().setup_whats_this()

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Average' # Define plugin name here
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

    # todo: over-ride PluginDefault functions here to define custom behaviour
    # (required for automation)

if __name__=='__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget(None, None))
  w.show()
  app.exec_()
  sys.exit()
