#!/usr/bin/env python3

from PyQt4.QtGui import *

from .util import file_io
from .util import filter_jeff as fj
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

# on button click!

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
        frames = fj.gsr(frames, width, height, callback)
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

  def check_ready_for_automation(self):
    return True

  def automation_error_message(self):
      return "YOU SHOULD NOT BE ABLE TO SEE THIS"

