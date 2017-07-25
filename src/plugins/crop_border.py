#!/usr/bin/env python3

import functools
import sys

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import file_io
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    crop_percentage_sb_label = "Crop Percentage"

  class Defaults(WidgetDefault.Defaults):
      crop_percentage_sb_default = 25

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    self.main_button = QPushButton('Crop')
    self.crop_percentage_sb = QSpinBox()
    self.left_frame_range = QSpinBox()
    self.right_frame_range = QSpinBox()
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    self.crop_percentage_sb.setMaximum(99)
    self.vbox.addWidget(QLabel(self.Labels.crop_percentage_sb_label))
    self.vbox.addWidget(self.crop_percentage_sb)

    def min_handler(max_of_min):
        self.left_frame_range.setMaximum(max_of_min)
    def max_handler(min_of_max):
        self.right_frame_range.setMinimum(min_of_max)
    self.left_frame_range.valueChanged[int].connect(max_handler)
    self.right_frame_range.valueChanged[int].connect(min_handler)
    hbox = QHBoxLayout()
    self.vbox.addWidget(QLabel('Set range of frames cropped'))
    self.left_frame_range.setMinimum(0)
    self.left_frame_range.setMaximum(1400)
    self.left_frame_range.setValue(400)
    hbox.addWidget(self.left_frame_range)
    to = QLabel('to')
    to.setAlignment(Qt.AlignCenter)
    hbox.addWidget(to)
    self.right_frame_range.setMaximum(1000000)
    self.right_frame_range.setValue(1400)
    hbox.addWidget(self.right_frame_range)
    self.vbox.addLayout(hbox)

    self.vbox.addStretch()
    self.vbox.addWidget(self.main_button)

  def setup_signals(self):
    super().setup_signals()
    self.main_button.clicked.connect(self.execute_primary_function)

  def setup_params(self, reset=False):
      super().setup_params(reset)
      if len(self.params) == 1 or reset:
        self.update_plugin_params(self.Labels.crop_percentage_sb_label, self.Defaults.crop_percentage_sb_default)
      self.crop_percentage_sb.setValue(self.params[self.Labels.crop_percentage_sb_label])

  def setup_param_signals(self):
      super().setup_param_signals()
      self.crop_percentage_sb.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                    self.Labels.crop_percentage_sb_label))


  def execute_primary_function(self, input_paths=None):
      '''Primary function of plugin'''
      if not input_paths:
          if not self.selected_videos:
              return
          else:
              selected_videos = self.selected_videos
      else:
          selected_videos = input_paths
      # def crop_center(img, cropx, cropy):
      #     """Function to crop center of an image file. Output is of size (cropx, cropy)"""
      #     y, x = img.shape
      #     startx = x // 2 - (cropx // 2)
      #     starty = y // 2 - (cropy // 2)
      #     return img[starty:starty + cropy, startx:startx + cropx]
      output_paths = []
      for path in selected_videos:
          frames = file_io.load_file(path, segment=[self.left_frame_range.value(), self.right_frame_range.value()])
          percentage = self.crop_percentage_sb.value() / 100
          # frames_cropped = np.empty((frames.shape[0], frames.shape[1], frames.shape[2]),
          #               dtype=frames.dtype)
          cropped_y = round(percentage * frames.shape[1])
          cropped_x = round(percentage * frames.shape[2])
          for frame_no in range(len(frames)):
              for y in range(len(frames[frame_no])):
                  for x in range(len(frames[frame_no][y])):
                      if (x < cropped_x or x > frames.shape[2] - cropped_x) or\
                              (y < cropped_y or y > frames.shape[1] - cropped_y):
                          frames[frame_no][y][x] = 0
          output_paths = output_paths + [path]
          pfs.save_project(path, self.project, frames, 'crop-border', 'video')
          pfs.refresh_list(self.project, self.video_list,
                           self.params[self.Labels.video_list_indices_label],
                           self.Defaults.list_display_type,
                           self.params[self.Labels.last_manips_to_display_label])
      return output_paths

  def setup_whats_this(self):
      '''Setup custom help messages'''
      # todo: setup custom help messages to aid the user, each tied to one of your UI components.
      super().setup_whats_this()

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Crop Border' # Define plugin name here
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
