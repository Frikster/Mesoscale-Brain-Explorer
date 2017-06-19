#!/usr/bin/env python3

import numpy as np
from PyQt4.QtGui import *

from .util import file_io
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


def gsr(frames, width, height, progress_callback):
    frames[np.isnan(frames)] = 0
    progress_callback(0.2)
    # Reshape into time and space
    frames = np.reshape(frames, (frames.shape[0], width*height))
    progress_callback(0.3)
    mean_g = np.mean(frames, axis=1, dtype=np.float32)
    progress_callback(0.4)
    g_plus = np.squeeze(np.linalg.pinv([mean_g]))
    progress_callback(0.5)
    beta_g = np.dot(g_plus, frames)
    progress_callback(0.6)
    # print('mean_g = '+str(np.shape(mean_g)))
    # print('beta_g = '+str(np.shape(beta_g)))
    global_signal = np.dot(np.asarray([mean_g]).T, [beta_g])
    progress_callback(0.7)
    frames = frames - global_signal
    progress_callback(0.8)
    frames = np.reshape(frames, (frames.shape[0], width, height))
    progress_callback(0.9)
    return frames



class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    pass

  class Defaults(WidgetDefault.Defaults):
    manip = "gsr"

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)

    if not project or not isinstance(plugin_position, int):
        return
    self.butt_gsr = QPushButton('Global Signal Regression')
    WidgetDefault.__init__(self, project, plugin_position)
  def setup_ui(self):
      super().setup_ui()
      hhbox = QHBoxLayout()
      hhbox.addWidget(self.butt_gsr)
      self.vbox.addLayout(hhbox)
      self.vbox.addStretch()

  def setup_signals(self):
      super().setup_signals()
      self.butt_gsr.clicked.connect(self.execute_primary_function)

  def execute_primary_function(self, input_paths=None):
    if not input_paths:
        if not self.selected_videos:
            return
        else:
            selected_videos = self.selected_videos
    else:
        selected_videos = input_paths

    global_progress = QProgressDialog('Total Progress for Computing GSR for Selection', 'Abort', 0, 100, self)
    global_progress.setAutoClose(True)
    global_progress.setMinimumDuration(0)
    def global_callback(x):
        global_progress.setValue(x * 100)
        QApplication.processEvents()
    output_paths = []
    total = len(selected_videos)
    for i, video_path in enumerate(selected_videos):
        global_callback(i / total)
        progress = QProgressDialog('Computing GSR for ' + video_path, 'Abort', 0, 100, self)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        def callback(x):
            progress.setValue(x * 100)
            QApplication.processEvents()
        callback(0.01)
        frames = file_io.load_file(video_path)
        callback(0.1)
        width = frames.shape[1]
        height = frames.shape[2]
        frames = gsr(frames, width, height, callback)
        path = pfs.save_project(video_path, self.project, frames, self.Defaults.manip, 'video')
        output_paths = output_paths + [path]
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])
        callback(1)
    global_callback(1)
    return output_paths

  def setup_whats_this(self):
      super().setup_whats_this()
      self.butt_gsr.setWhatsThis("Global Signal Regression(GSR) uses linear regression to remove shared variance "
                                 "between the global signal and the time course. The algebraic consequence is that GSR "
                                 "shifts the distribution of functional connectivity "
                                 "values from being predominantly positive to both positive and negative in any "
                                 "given subject.")

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Global Signal Regression'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def check_ready_for_automation(self, expected_input_number):
    return True

  def automation_error_message(self):
      return "YOU SHOULD NOT BE ABLE TO SEE THIS"

