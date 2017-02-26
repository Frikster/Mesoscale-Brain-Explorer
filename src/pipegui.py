#!/usr/bin/env python3

import collections
import functools
import importlib
import multiprocessing
import os
import sys
import json

import qtutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtGui import QApplication
from datadialog import DataDialog
from pipeconf import PipeconfDialog, PipelineModel
from project import ProjectManager

from plugins.util import mse_ui_elements as mue
from plugins import set_coordinate_system as scs
import traceback

APPNAME = 'Mesoscale Brain Explorer'
VERSION = open('../VERSION').read()

def clear_layout(layout):
  while True:
    item = layout.takeAt(0)
    if not item:
      break
    item.widget().setParent(None)
    child = item.layout()
    if child:
      clear_layout(child)
    del item

class PipelineView(QListView):
  active_plugin_changed = pyqtSignal(str, int)

  def __init__(self, parent=None):
    super(PipelineView, self).__init__(parent)

    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')

  def currentChanged(self, current, previous):
    super(PipelineView, self).currentChanged(current, previous)
    plugin_name = str(current.data(Qt.UserRole))
    plugin_position = current.row()
    self.active_plugin_changed.emit(plugin_name, plugin_position)

class ToolButton(QToolButton):
  def __init__(self, parent=None):
    super(ToolButton, self).__init__(parent)

class Sidebar(QWidget):
  open_pipeconf_requested = pyqtSignal()
  open_datadialog_requested = pyqtSignal()
  automate_pipeline_requested = pyqtSignal()
  x_origin_changed = pyqtSignal(float)
  y_origin_changed = pyqtSignal(float)
  units_per_pixel_changed = pyqtSignal(float)

  def __init__(self, parent=None):
    super(Sidebar, self).__init__(parent)
    self.x_origin = QDoubleSpinBox()
    self.y_origin = QDoubleSpinBox()
    self.units_per_pixel = QDoubleSpinBox()
    self.auto_pb = QPushButton('&Automation')
    self.setup_ui()
    self.setup_signals()
    self.setup_whats_this()

  def setup_ui(self):
    self.setContentsMargins(4, 6, 5, 0)

    vbox = QVBoxLayout()

    vbox.addWidget(QLabel('Origin:'))
    hbox = QHBoxLayout()
    hbox.addWidget(QLabel("X:"))
    hbox.addWidget(self.x_origin)
    hbox.addWidget(QLabel("Y:"))
    hbox.addWidget(self.y_origin)
    vbox.addLayout(hbox)
    vbox.addWidget(QLabel('Units per pixel:'))
    vbox.addWidget(self.units_per_pixel)
    self.units_per_pixel.setDecimals(5)
    self.units_per_pixel.setMaximum(100000)
    self.x_origin.setMaximum(100000)
    self.y_origin.setMaximum(100000)
    # self.x_origin.setValue(self.project['origin'][0])
    # self.y_origin.setValue(self.project['origin'][1])
    # self.units_per_pixel.setValue(self.project['unit_per_pixel'])

    self.pl_list = PipelineView()
    self.pl_list.setIconSize(QSize(18, 18))
    self.pl_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.pl_list.setEditTriggers(QAbstractItemView.NoEditTriggers)

    vbox.addWidget(QLabel('Pipeline:'))
    vbox.addWidget(self.pl_list)

    self.auto_pb.clicked.connect(self.automate_pipeline_requested)
    vbox.addWidget(self.auto_pb)

    vbox.addWidget(mue.InfoWidget('Automation allows you to use the output from a preceding plugin in the pipeline as '
                                  'input to the next. You can configure your pipeline to set up a custom order, '
                                  'add additional plugins or remove plugins. '
                                  'To use: \n'
                                  '1) If your first plugin is not the importer, select files in the video list to use '
                                  'as input. These files will go through each step in your pipeline. \n'
                                  '2) Set paramaters on each individual plugin in your pipeline. For example, in the '
                                  'alignment plugin select the reference frame all files will be aligned to and in the '
                                  'ROI plugin select the ROIs cropped to for all files. \n'
                                  'Use the "What\'s This" help feature on UI elements in each plugin to learn '
                                  'how to set paramaters for each one.\n'
                                  '3) When you\'re ready highlight each plugin you intend to run and make sure they '
                                  'are in the correct order. Some plugins cannot be automated so do not highlight '
                                  'those.\n'
                                  '\n Click Automate!'))

    vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    pb = QPushButton('&Configure Pipeline')
    pb.clicked.connect(self.open_pipeconf_requested)
    vbox.addWidget(pb)
    pb = QPushButton('&Manage Data')
    pb.clicked.connect(self.open_datadialog_requested)
    vbox.addWidget(pb)

    vbox.setStretch(0, 0)
    vbox.setStretch(1, 0)
    vbox.setStretch(2, 0)

    self.setLayout(vbox)

  def setup_sidebar_values(self, project):
      if project:
        self.x_origin.setValue(project['origin'][0])
        self.y_origin.setValue(project['origin'][1])
        self.units_per_pixel.setValue(project['unit_per_pixel'])

  def setup_signals(self):
      self.x_origin.valueChanged.connect(self.x_origin_changed)
      self.y_origin.valueChanged.connect(self.y_origin_changed)

      self.units_per_pixel.valueChanged.connect(self.units_per_pixel_changed)

  def setup_whats_this(self):
      self.x_origin.setWhatsThis("Set the x coordinate used across all plugins in this project. "
                                 "Units are in pixels so coordinates must be within the size of "
                                 "all imported files"
                                 "Coordinates can also be set via plugins, after which the change "
                                 "should be reflected in the value here"
                                 )
      self.y_origin.setWhatsThis("Set the y coordinate used across all plugins in this project. "
                                 "Units are in pixels so coordinates must be within the size of "
                                 "all imported files"
                                 "Coordinates can also be set via plugins, after which the change "
                                 "should be reflected in the value here"
                                 )
      self.units_per_pixel.setWhatsThis("Set the amount of units there are in a single pixel. "
                                        "This is applied across all plugins in this project. "
                                        "Units can be anything as long as the same units are used "
                                        "across all plugins. e.g. if you use microns for units per pixel "
                                        "then microns must be used for the coordinates in the ROI Placer plugin.")
      self.auto_pb.setWhatsThis("If you are still unsure how to automate, watch a video tutorial. "
                                "A link to where to find tutorials can be find by clicking Help -> About")

class MainWindow(QMainWindow):
  def __init__(self, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle(APPNAME)
    self.setWindowFlags(Qt.Window | Qt.WindowContextHelpButtonHint |
                        Qt.WindowMinimizeButtonHint |
                        Qt.WindowMaximizeButtonHint |
                        Qt.WindowCloseButtonHint)
    self.project = None
    self.current_plugin = None
    self.project_manager = ProjectManager(self)
    self.plugins = self.load_plugins()
    self.sidebar = Sidebar()
    self.setup_ui()
    self.setup_signals()

    self.enable(False)

    self.pipeline_model = PipelineModel()
    self.sidebar.pl_list.setModel(self.pipeline_model)
    self.pipeconf.pipeline_list.setModel(self.pipeline_model)

    last = str(QSettings().value('path_of_last_project'))
    if last:
        quit_msg = "Load last project " + last + " ?"
        reply = QMessageBox.question(self, 'Project Setup',
                         quit_msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if last:
                try:
                    self.open_project(last)
                except:
                    qtutil.critical('Previous project appears to have been corrupted.\n \n'
                                    + traceback.format_exc(), self)
                    #qtutil.critical("Previous project appears to have been corrupted. Please move or delete it.")
            self.sidebar.setup_sidebar_values(self.project)

  def load_plugins(self):
    """This just gets all the plugins (no reference to pipeline)"""
    plugins = collections.OrderedDict()
    filenames = [f for f in sorted(os.listdir('plugins')) if f.endswith('.py')]
    for filename in filenames:
      name, ext = os.path.splitext(filename)
      p = self.load_plugin('plugins.' + name, None)
      if p:
        plugins[name] = p
    return plugins

  def load_plugin(self, module, plugin_position):
    try:
        m = importlib.import_module(module)
        if not hasattr(m, 'MyPlugin'):
          return None
        p = m.MyPlugin(self.project, plugin_position)
        # p.run()
    except:
        print('Failed to import \'{}\'.'.format(module))
        raise
    else:
        return p

  # def reset_pipeline_plugins(self, plugin_names):
  #     for i, plugin_name in enumerate(plugin_names):
  #         p = self.load_plugin('plugins.' + plugin_name, i)
  #         if p:
  #             self.plugins[plugin_name] = p
  #     if self.current_plugin:
  #         self.set_plugin(self.current_plugin, None)

  def reload_pipeline_plugins(self):
    for i, plugin_name in enumerate(self.pipeline_model.get_plugin_names()):
      p = self.load_plugin('plugins.' + plugin_name, i)
      if p:
        self.plugins[plugin_name] = p
        # def set_x(val):
        #     self.sidebar.x_origin.setValue(val)
        # def set_y(val):
        #     self.sidebar.y_origin.setValue(val)
        # if plugin_name == 'set_coordinate_system':
        #     p.widget.x_origin_changed[float].connect(self.set_x)
        #     p.widget.y_origin_changed[float].connect(set_y)
    if self.current_plugin:
      self.set_plugin(self.current_plugin, None)

  def setup_ui(self):
    self.pipeconf = PipeconfDialog(self.plugins, self)
    self.datadialog = DataDialog(self)

    self.pl_frame = QFrame()

    splitter = QSplitter(self)
    self.enable = lambda yes: splitter.setEnabled(yes)

    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')

    splitter.addWidget(self.sidebar)
    splitter.addWidget(self.pl_frame)

    # splitter.setStretchFactor(0, 0)
    # splitter.setStretchFactor(1, 1)

    self.setCentralWidget(splitter)

    self.menu = self.menuBar()
    m = self.menu.addMenu('&File')

    a = QAction('&New project', self)
    a.setShortcut('Ctrl+N')
    a.setStatusTip('Create new project')
    a.triggered.connect(self.create_project)
    m.addAction(a)

    a = QAction('&Open project', self)
    a.setShortcut('Ctrl+O')
    a.setStatusTip('Open project')
    a.triggered.connect(self.open_project)
    m.addAction(a)

    a = QAction("&Quit", self)
    a.setShortcut("Ctrl+Q")
    a.setStatusTip('Leave The App')
    a.setIcon(QIcon('pics/quit.png'))
    a.triggered.connect(self.close)
    m.addAction(a)

    about_action = QAction('&About ' + APPNAME, self)
    about_action.setStatusTip('About ' + APPNAME)
    about_action.triggered.connect(self.about)
    about_action.setShortcut('F1')
    whats_this_action = QWhatsThis.createAction(QAction('&What\'s This?', self))
    whats_this_action.setShortcut('Shift+F1')

    m = self.menu.addMenu('&Project')
    m.setEnabled(False)
    a = QAction("&Close", self)
    a.setStatusTip('Close project')
    a.triggered.connect(self.close_project)
    m.addAction(a)
    a = QAction("&Reset All Plugin Parameters", self)
    a.setStatusTip('This is useful if you experience JSON-related issues allowing for a clean slate')
    a.triggered.connect(self.reset_all_params)
    m.addAction(a)
    self.project_menu = m

    help_menu = self.menu.addMenu('&Help')
    help_menu.addAction(about_action)
    help_menu.addAction(whats_this_action)

  def reset_all_params(self):
      for plugin_position, p in enumerate(self.project.pipeline):
          if p['name'] in self.plugins.keys():
            plugin = self.plugins[p['name']]
          if hasattr(plugin, 'widget'):
              if hasattr(plugin.widget, 'setup_params'):
                  if not hasattr(plugin.widget, 'params'):
                      plugin.widget.params = self.project.pipeline[plugin_position]
                      plugin.widget.project = self.project
                      plugin.widget.plugin_position = plugin_position
                  try:
                    plugin.widget.setup_params(reset=True)
                  except:
                    print("Failed to reset " + p['name'])

  def setup_signals(self):
      self.datadialog.reload_plugins.connect(self.reload_pipeline_plugins)

      self.sidebar.open_pipeconf_requested.connect(self.open_pipeconf)
      self.sidebar.open_datadialog_requested.connect(self.open_datadialog)
      self.sidebar.automate_pipeline_requested.connect(self.automate_pipeline)
      self.sidebar.x_origin_changed[float].connect(functools.partial(self.set_project_coordinate_system, 'x'))
      self.sidebar.y_origin_changed[float].connect(functools.partial(self.set_project_coordinate_system, 'y'))
      self.sidebar.units_per_pixel_changed[float].connect(functools.partial(self.set_project_coordinate_system,
                                                                            'units_per_pixel'))
      self.plugins['set_coordinate_system'].widget.x_origin_changed[float].connect(functools.partial(
          self.set_project_coordinate_system, 'x'))
      self.plugins['set_coordinate_system'].widget.y_origin_changed[float].connect(functools.partial(
          self.set_project_coordinate_system, 'y'))
      # todo: add signals from set_coordinate_system here

      self.sidebar.pl_list.active_plugin_changed[str, int].connect(self.set_plugin)
      self.sidebar.pl_list.setModel(self.pipeconf.pipeline_list.model())

  def set_project_coordinate_system(self, key, value):
    #todo: add update for view
    self.project['origin'] = list(self.project['origin'])
    if key == 'x':
        self.project['origin'][0] = value
        self.project.save()
    elif key == 'y':
        self.project['origin'][1] = value
        self.project.save()
    elif key == 'units_per_pixel':
        self.project['unit_per_pixel'] = value
        self.project.save()

    if self.current_plugin in self.plugins.keys():
        self.plugins[self.current_plugin].widget.view.update()

  def create_project(self):
    project = self.project_manager.new_project()
    if project:
      self.load_project(project)
  
  def load_project(self, project):
    self.clean()
    self.project = project
    self.setWindowTitle(APPNAME + ' - ' + project.name)
    self.enable(True)
    self.project_menu.setEnabled(True)
    QSettings().setValue('path_of_last_project', project.path)

    pipeline = []
    for plugin_dict in self.project.pipeline:
      # include fix to update old versions to new format
      try:
          plugin_name = plugin_dict['name']
      except:
          attrs = json.load(open('../templates/spcproject.json'))
          pipeline_template = attrs['pipeline']
          # pipeline_names = [p['name'] for p in pipeline_template]
          # plugins = self.load_plugins()
          # for plugin_name in pipeline_names:
          #     for plugin in plugins:
          #         if plugin == plugin_name:
          #             pipeline.append((plugin, plugins[plugin].name))
          #             break
          QMessageBox.about(self, 'Critical Error in pipeline. Manual Reset Recommended',
                            """
                            <p>Please quit and replace the pipeline in your project JSON file with</p>
                            <p></p>
                             <td>%s</td>
                             <p>which can be copied from
                             <a href="https://github.com/Frikster/Mesoscale-Brain-Explorer/blob/master/templates/spcproject.json">here</a></p>
                            <p>Only the pipeline section needs to be replaced</p>
                            """ % pipeline_template)

          # qtutil.critical("Pipeline appears to be corrupt. "
          #                 "Please replace your current pipeline in the JSON file with \n"
          #                 " " + str(pipeline_template) + "which can be copied from \n" +
          #                 < a href = "https://github.com/Frikster/Mesoscale-Brain-Explorer/issues" > here < / a > < / p >
          #                 "https://github.com/Frikster/Mesoscale-Brain-Explorer/blob/master/templates/spcproject.json")
          return
      for plugin in self.plugins:
        if plugin == plugin_name:
           pipeline.append((plugin, self.plugins[plugin].name))
           break
    self.pipeline_model.set_plugins(pipeline)
    self.reload_pipeline_plugins()
    # self.reset_pipeline_plugins([p[0] for p in pipeline])

  def open_project(self, path=''):
    project = self.project_manager.open_project(path)
    if project:
      self.load_project(project)

  def close_project(self):
    self.clean()
    self.project = None
    self.setWindowTitle(APPNAME)
    self.project_menu.setEnabled(False)
    self.enable(False)
  
  def set_plugin(self, plugin_name, plugin_position):
    p = self.load_plugin('plugins.' + str(plugin_name), plugin_position)
    if not p:
      return
    self.current_plugin = plugin_name
    self.plugins[plugin_name] = p

    def set_x(val):
        self.sidebar.x_origin.setValue(val)
    def set_y(val):
        self.sidebar.y_origin.setValue(val)
    if plugin_name == 'set_coordinate_system':
        p.widget.x_origin_changed[float].connect(set_x)
        p.widget.y_origin_changed[float].connect(set_y)

    lt = QVBoxLayout()
    lt.addWidget(p.widget)
 
    self.clean_plugin()
    self.pl_frame.setLayout(lt)

    # p.run()
  
  def clean_plugin(self):
    if self.pl_frame.layout():
      clear_layout(self.pl_frame.layout())
      QWidget().setLayout(self.pl_frame.layout())

  def clean(self):
    model = self.sidebar.pl_list.model()
    if model:
      model.clear()
    self.clean_plugin()

  def open_pipeconf(self):
    self.pipeconf.exec_()
    pipeline = self.pipeline_model.get_plugin_names()
    self.project.set_pipeline(pipeline)
    self.project.save()

  def open_datadialog(self):
    self.datadialog.update(self.project)
    self.datadialog.exec_()

  def automate_pipeline(self):
      # qtutil.info('Coming Soon')
      # return

      # order by index
      ordered_q_model_indexes = sorted(self.sidebar.pl_list.selectedIndexes(), key=lambda x: x.row(), reverse=False)
      if not ordered_q_model_indexes:
          qtutil.info("Select all the plugins you want to process through. Use shift or ctrl to select multiple")

      # ensure all selected plugins are ready for automation
      for q_model_index in ordered_q_model_indexes:
          p = self.plugins[q_model_index.data(Qt.UserRole)]
          if not p.check_ready_for_automation():
            qtutil.critical(p.automation_error_message())
            return

      p = self.plugins[ordered_q_model_indexes[0].data(Qt.UserRole)]
      input_paths = p.get_input_paths()
      if not input_paths:
          qtutil.critical("The first plugin in the pipeline does not have a set of input files selected")
          return

      for q_model_index in ordered_q_model_indexes:
          p = self.plugins[q_model_index.data(Qt.UserRole)]
          output_paths = p.run(input_paths)
          input_paths = output_paths


      # self.sidebar.pl_list.selectedIndexes()[0].data(Qt.UserRole)
      #
      # self.sidebar.pl_list.selectedIndexes()[0].row()
      # self.sidebar.pl_list.model().data(self.sidebar.pl_list.selectedIndexes()[0])

  def about(self):
    author = 'Cornelis Dirk Haupt'
    date = '2017'

    QMessageBox.about(self, 'About ' + APPNAME, 
        """
        <b>%s</b>
        <p>An online readme, including user manual and developer tutorial can be found
        <a href="https://github.com/Frikster/Mesoscale-Brain-Explorer">here</a></p>
        <p>Use the "what's this" feature to click on any UI component and learn how to use it</p>
        <p>Please submit any feature requests or issues
        <a href="https://github.com/Frikster/Mesoscale-Brain-Explorer/issues">here</a></p>
        <p></p>
        <p><table border="0" width="150">
        <tr>
        <td>Author:</td>
        <td>%s</td>
        </tr>
        <tr>
        <td>Version:</td>
        <td>%s</td>
        </tr>
        <tr>
        <td>Date:</td>
        <td>%s</td>
        </tr>            
        </table></p>
        """ % (APPNAME, author, VERSION, date))


if __name__ == '__main__':
  multiprocessing.freeze_support()

  app = QApplication(sys.argv)
  app.setApplicationName(APPNAME)
  app.setOrganizationName('University of British Columbia')
  app.setOrganizationDomain('https://github.com/Frikster/Mesoscale-Brain-Explorer')

  w = MainWindow()
  w.resize(1800, 800)
  w.setWindowIcon(QIcon('pics/cbhlogo.png'))
  w.show()

  app.exec_()
  app.deleteLater()
  del w
  sys.exit()
