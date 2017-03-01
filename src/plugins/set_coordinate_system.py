#!/usr/bin/env python3

import ast

import qtutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
  x_origin_changed = pyqtSignal(float)
  y_origin_changed = pyqtSignal(float)

  class Labels(WidgetDefault.Labels):
      origin_label_label = 'Origin'

  class Defaults(WidgetDefault.Defaults):
      list_display_type = ['ref_frame', 'video']
      origin_label_default = 'Origin:'

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)

    if not project or not isinstance(plugin_position, int):
        return

    self.project = project
    self.combo_box = QComboBox()
    self.avg_origin_button = QPushButton('&Compute averaged origin')
    self.origin_label = QLabel(self.Defaults.origin_label_default)
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    self.vbox.addWidget(self.origin_label)
    self.vbox.addWidget(self.avg_origin_button)

  def setup_signals(self):
      super().setup_signals()
      self.view.vb.clicked.connect(self.vbc_clicked)
      self.avg_origin_button.clicked.connect(self.avg_origin)

  def selected_video_changed(self, selected, deselected):
      super().selected_video_changed(selected, deselected)
      project_file = pfs.get_project_file_from_key_item(self.project,
                                                        'path',
                                                        self.shown_video_path)
      # Check if origin exists
      if project_file is not None:
          try:
            (x, y) = ast.literal_eval(project_file['origin'])
          except KeyError:
            self.origin_label.setText('Origin:')
          else:
            (x, y) = ast.literal_eval(project_file['origin'])
            self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))
      frame = fileloader.load_reference_frame(self.shown_video_path)
      self.view.show(frame)

  def avg_origin(self):
    """Set origin to averaged over all selected files' origins"""
    if not self.selected_videos:
        return

    relevant_files = []
    for selected_path in self.selected_videos:
        relevant_files = relevant_files + \
                         [pfs.get_project_file_from_key_item(self.project, 'path', selected_path)]

    # check to see if all selected files have an origin
    try:
        [file['origin'] for file in relevant_files]
    except KeyError:
        qtutil.warning('One or more of your selected files have no origin. These will be ignored.')

    #collect dict items that have origins
    orgs = [file.get("origin") for file in relevant_files]
    orgs = [x for x in orgs if x is not None]
    orgs = [ast.literal_eval(org) for org in orgs]

    # collect and avg origins
    (x_tot, y_tot) = (0, 0)
    for (x, y) in orgs:
      (x_tot, y_tot) = (x_tot+x, y_tot+y)
    no_orgs = len(relevant_files)
    (x_avg, y_avg) = (x_tot / no_orgs, y_tot / no_orgs)
    self.project['origin'] = (x_avg, y_avg)
    self.view.update()
    self.save()
    self.x_origin_changed.emit(x_avg)
    self.y_origin_changed.emit(y_avg)

  def set_origin_label(self, x, y):
    self.origin_label.setText('Origin: ({} | {})'.format(round(x, 2), round(y, 2)))

  def update(self):
    videos = [f for f in self.project.files if f['type'] == 'video']
    if not videos:
      self.setEnabled(False)
      return
    frame = fileloader.load_reference_frame(videos[0]['path'])
    self.view.show(frame)
    self.setEnabled(True)

  def save(self):
    self.project.save()

  def vbc_clicked(self, x, y):
    pfs.change_origin(self.project, self.shown_video_path, (x, y))
    self.set_origin_label(x, y)
    self.view.update()

  def setup_whats_this(self):
      super().setup_whats_this()
      self.origin_label.setWhatsThis("Click the image to select an origin for each image stack by clicking your image "
                                     "and it will be saved and displayed here. Select multiple image stacks in the "
                                     "video list and then compute averaged origin to apply the averaged origin of all "
                                     "selected image stacks as the origin for the project")
      self.avg_origin_button.setWhatsThis("After clicking on the scene an origin is saved for that image stack "
                                          "and displayed above. Select multiple image stacks in the "
                                          "video list that have origins and then click this to compute the average of "
                                          "all those origins. This will then be set as the origin of the "
                                          "project")

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Set coordinate system'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def run(self):
    self.widget.update()

