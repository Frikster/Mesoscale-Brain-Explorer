#!/usr/bin/env python3

import os
import sys
import inspect
import importlib
import collections
import traceback
import multiprocessing

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from pipeconf import PipeconfDialog, PipelineModel
from datadialog import DataDialog
from project import ProjectManager

import qtutil

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
  active_plugin_changed = pyqtSignal(str)

  def __init__(self, parent=None):
    super(PipelineView, self).__init__(parent)

    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')

  def currentChanged(self, current, previous):
    super(PipelineView, self).currentChanged(current, previous)
    plugin_name = str(current.data(Qt.UserRole))
    self.active_plugin_changed.emit(plugin_name)

class ToolButton(QToolButton):
  def __init__(self, parent=None):
    super(ToolButton, self).__init__(parent)

class Sidebar(QWidget):
  open_pipeconf_requested = pyqtSignal()
  open_datadialog_requested = pyqtSignal()

  def __init__(self, parent=None):
    super(Sidebar, self).__init__(parent)

    self.setup_ui()

  def setup_ui(self):
    self.setContentsMargins(4, 6, 5, 0)

    vbox = QVBoxLayout()

    self.pl_list = PipelineView()
    self.pl_list.setIconSize(QSize(18, 18))

    vbox.addWidget(QLabel('Pipeline:'))
    vbox.addWidget(self.pl_list)
   
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

class MainWindow(QMainWindow):
  def __init__(self, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle(APPNAME)

    self.project = None
    self.current_plugin = None
    self.project_manager = ProjectManager(self)
    self.plugins = self.load_plugins()
    self.setup_ui()

    self.enable(False)

    self.pipeline_model = PipelineModel()
    self.sidebar.pl_list.setModel(self.pipeline_model)
    self.pipeconf.pipeline_list.setModel(self.pipeline_model)

    last = str(QSettings().value('path_of_last_project'))
    if last:
      try:
        self.open_project(last)
      except:
        qtutil.critical("Previous project appears to have been corrupted. Please move or delete it.")

  def load_plugins(self):
    plugins = collections.OrderedDict()
    filenames = [f for f in sorted(os.listdir('plugins')) if f.endswith('.py')]
    for filename in filenames:
      name, ext = os.path.splitext(filename)
      p = self.load_plugin('plugins.' + name)
      if p:
        plugins[name] = p
    return plugins

  def load_plugin(self, module):
    try:
      m = importlib.import_module(module)
      if not hasattr(m, 'MyPlugin'):
        return None
      p = m.MyPlugin(self.project)
      # p.run()
    except:
      print('Failed to import \'{}\'.'.format(module))
      raise
    else:
      return p

  def reload_pipeline_plugins(self):
    for plugin_name in self.pipeline_model.get_plugin_names():
      p = self.load_plugin('plugins.' + plugin_name)
      if p:
        self.plugins[plugin_name] = p
    if self.current_plugin:
      self.set_plugin(self.current_plugin)

  def setup_ui(self):
    self.pipeconf = PipeconfDialog(self.plugins, self)
    self.datadialog = DataDialog(self)
    self.datadialog.reload_plugins.connect(self.reload_pipeline_plugins)

    self.sidebar = Sidebar()
    self.sidebar.open_pipeconf_requested.connect(self.open_pipeconf)
    self.sidebar.open_datadialog_requested.connect(self.open_datadialog)

    self.pl_frame = QFrame()

    self.sidebar.pl_list.active_plugin_changed[str].connect(self.set_plugin)
    self.sidebar.pl_list.setModel(self.pipeconf.pipeline_list.model())

    splitter = QSplitter(self)
    self.enable = lambda yes: splitter.setEnabled(yes)

    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')

    splitter.addWidget(self.sidebar)
    splitter.addWidget(self.pl_frame)

    #splitter.setStretchFactor(0, 0)
    #splitter.setStretchFactor(1, 1)

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
    a.triggered.connect(qApp.quit)
    m.addAction(a)

    about_action = QAction('&About ' + APPNAME, self)
    about_action.setStatusTip('About ' + APPNAME)
    about_action.triggered.connect(self.about)
    about_action.setShortcut('F1')

    m = self.menu.addMenu('&Project')
    m.setEnabled(False)
    a = QAction("&Close", self)
    a.setStatusTip('Close project')
    a.triggered.connect(self.close_project)
    m.addAction(a)
    self.project_menu = m

    settings_menu = self.menu.addMenu('&Settings')
    #a = QAction('&Pipeline Automation', self)
    #a.setEnabled(False)
    #a.setStatusTip('Create new project')
    #a.triggered.connect(self.create_project)
    settings_menu.addAction(a)

    help_menu = self.menu.addMenu('&Help')
    help_menu.addAction(about_action)

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
    for plugin_name in self.project.pipeline:
      for plugin in self.plugins:
        if plugin == plugin_name:
           pipeline.append((plugin, self.plugins[plugin].name))
           break
    self.pipeline_model.set_plugins(pipeline)
    self.reload_pipeline_plugins()

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
  
  def set_plugin(self, plugin_name):
    p = self.load_plugin('plugins.' + str(plugin_name))
    if not p:
      return
    self.current_plugin = plugin_name
    self.plugins[plugin_name] = p

    lt = QVBoxLayout()
    lt.addWidget(p.widget)
 
    self.clean_plugin()
    self.pl_frame.setLayout(lt)

    p.run()
  
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

  def about(self):
    author = 'Cornelis Dirk Haupt'
    date = '2016'

    QMessageBox.about(self, 'About ' + APPNAME, 
        """
        <b>%s</b>
        <p>A simple program that is a work in progress.</p>
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
  app.setOrganizationDomain('spc-corporation.com')

  w = MainWindow()
  w.resize(1060,660)
  w.setWindowIcon(QIcon('pics/cbhlogo.png'))
  w.show()

  app.exec_()
  app.deleteLater()
  sys.exit()
