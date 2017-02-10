#!/usr/bin/env python3

import functools
import sys

import qtutil
from PyQt4.QtGui import *

from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    example_sb_label = "Example Spinbox"
    # todo: Define labels used as a key to save paramaters to file here

  class Defaults(WidgetDefault.Defaults):
    example_sb_default = 10
    # todo: Define default values for this plugin and its UI components here

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    # todo: Define global attributes and UI components here
    # example: here a button and spin box are defined
    self.main_button = QPushButton('Custom Analysis')
    self.example_sb = QSpinBox()
    WidgetDefault.__init__(self, project, plugin_position)

  def setup_ui(self):
    super().setup_ui()
    # todo: setup UI component layout and properties here
    # example: here the button is placed before the spinbox and the spinbox
    # is given a input max value of 1000
    # initially, before the spinbox a label is inserted which gets its text from Label class
    self.vbox.addWidget(self.main_button)
    self.example_sb.setMaximum(1000)
    self.vbox.addWidget(QLabel(self.Labels.example_sb_label))
    self.vbox.addWidget(self.example_sb)
    self.vbox.addStretch()

  def setup_signals(self):
    super().setup_signals()
    # todo: Setup signals (i.e. what ui components do) here
    # example: main button that activates execute_primary_function when clicked
    self.main_button.clicked.connect(self.execute_primary_function)

  def setup_params(self, reset=False):
      super().setup_params()
      if len(self.params) == 1 or reset:
        # todo: setup plugin paramaters (e.g. UI component starting values) initial values here
        # in this example the default value for the spinbox is associated with the label and saved to file
        self.update_plugin_params(self.Labels.example_sb_label, self.Defaults.example_sb_default)
      # todo: setup where plugin paramaters get their values from
      # in this example the example spinbox gets its value from the param dictionary
      # which is used to access plugin paramaters saved to file
      self.example_sb.setValue(self.params[self.Labels.example_sb_label])

  def setup_param_signals(self):
      super().setup_param_signals()
      # todo: setup how paramaters (e.g. UI component values) are stored
      # e.g. saving the value after a user changes the spinbox value, keeping it from resetting
      self.example_sb.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                    self.Labels.example_sb_label))

  def execute_primary_function(self, input_paths=None):
      '''Primary function of plugin'''
      qtutil.info('This is only a template. Use it to code from. \n'
                  'Value of spinbox is: ' + str(self.example_sb.value()))

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Empty Plugin' # Define plugin name here
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
