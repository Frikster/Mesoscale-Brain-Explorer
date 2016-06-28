#!/usr/bin/env python

import os
import sys
import imp

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import qtutil

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

class PipelineModel(QStandardItemModel):
  active_plugin_changed = pyqtSignal(int)
  
  def __init__(self, parent=None):
    super(PipelineModel, self).__init__(parent)

  def add_plugin(self, plugin, id_):
    item = QStandardItem(plugin.name)
    item.setData(QIcon('pics/idle.png'), Qt.DecorationRole)
    item.setData(id_, Qt.UserRole)
    self.appendRow(item)

  def selection_changed(self, index, prev):
    item = self.itemFromIndex(index)
    item.setData(QIcon('pics/active.png'), Qt.DecorationRole)
    
    item = self.itemFromIndex(prev)
    if item: 
      item.setData(QIcon('pics/done.png'), Qt.DecorationRole)

    plugin_id, ok = index.data(Qt.UserRole).toInt()
    self.active_plugin_changed.emit(plugin_id)

class PipelineView(QListView):
  def __init__(self, parent=None):
    super(PipelineView, self).__init__(parent)

  def currentChanged(self, current, previous):
    super(PipelineView, self).currentChanged(current, previous)

    self.model().selection_changed(current, previous)

class ToolButton(QToolButton):
  def __init__(self, parent=None):
    super(ToolButton, self).__init__(parent)

class Sidebar(QWidget):
  def __init__(self, parent=None):
    super(Sidebar, self).__init__(parent)

    self.setup_ui()

  def setup_ui(self):
    self.setContentsMargins(4, 6, 5, 0)

    vbox = QVBoxLayout()

    hbox = QHBoxLayout()
    
    tb = QToolButton()
    tb.setIcon(QIcon('pics/add.png'))
    tb.setIconSize(QSize(20, 20))
    hbox.addWidget(tb)

    tb = QToolButton()
    tb.setIcon(QIcon('pics/delete.png'))
    tb.setIconSize(QSize(20, 20))
    hbox.addWidget(tb)

    tb = QToolButton()
    tb.setIcon(QIcon('pics/up.png'))
    tb.setIconSize(QSize(20, 20))
    hbox.addWidget(tb)

    tb = QToolButton()
    tb.setIcon(QIcon('pics/down.png'))
    tb.setIconSize(QSize(20, 20))
    hbox.addWidget(tb)

    hbox.addSpacerItem(QSpacerItem(1, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

    self.pl_list = PipelineView()
    self.pl_list.setStyleSheet('QListView::item { height: 26px; }')
    self.pl_list.setIconSize(QSize(18, 18))

    vbox.addWidget(QLabel('Processing pipeline:'))
    vbox.addWidget(self.pl_list)
   
    vbox.addLayout(hbox)
    vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    vbox.setStretch(0, 0)
    vbox.setStretch(1, 0)
    vbox.setStretch(2, 1)

    self.setLayout(vbox)

class MainWindow(QMainWindow):
  def __init__(self, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle('SPCanalyse')

    self.plugin_count = 0

    self.setup_ui()

    self.plugins = {}

    self.load_plugin('empty_plugin', 'plugins/empty_plugin.py')
    self.load_plugin('imageviewer', 'plugins/imageviewer.py')
    self.load_plugin('colorinverter', 'plugins/colorinverter.py')
    self.load_plugin('imagecropper', 'plugins/imagecropper.py')
    self.load_plugin('imagerotator', 'plugins/imagerotator.py')
    self.load_plugin('connectivity_diagram', 'plugins/connectivity_diagram.py')
    self.load_plugin('scatterplot', 'plugins/scatterplot.py')

    for plugin in self.plugins:
      self.pl_model.add_plugin(self.plugins[plugin], plugin)

    #self.set_plugin(self.load_plugin('empty_plugin', 'plugins/empty_plugin.py'))

  def setup_ui(self):
    self.sidebar = Sidebar()
    self.pl_frame = QFrame()

    self.pl_model = PipelineModel()
    self.pl_model.active_plugin_changed[int].connect(self.set_plugin)
    self.sidebar.pl_list.setModel(self.pl_model)

    splitter = QSplitter(self)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')

    splitter.addWidget(self.sidebar)
    splitter.addWidget(self.pl_frame)

    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)

    self.setCentralWidget(splitter)
 
    quit_action = QAction("&Quit", self)
    quit_action.setShortcut("Ctrl+Q")
    quit_action.setStatusTip('Leave The App')
    quit_action.setIcon(QIcon('pics/quit.png'))
    quit_action.triggered.connect(qApp.quit)

    about_action = QAction('&About', self)
    about_action.setStatusTip('About')
    about_action.triggered.connect(self.about)
    about_action.setIcon(QIcon('pics/about.png'))
 
    self.menu = self.menuBar()
    file_menu = self.menu.addMenu('&File')
    file_menu.addAction(quit_action)
    edit_menu = self.menu.addMenu('&Edit')
    project_menu = self.menu.addMenu('&Project')
    settings_menu = self.menu.addMenu('&Settings')
    help_menu = self.menu.addMenu('&Help')
    help_menu.addAction(about_action)
  
  def set_plugin(self, plugin_id):
    plugin = self.plugins[plugin_id]
    lt = QVBoxLayout()
    lt.addWidget(QLabel('<center>' + plugin.name + '</center>'))
    lt.addWidget(plugin.widget)
    lt.setStretch(0, 0)
    lt.setStretch(1, 1)
 
    if self.pl_frame.layout():
      clear_layout(self.pl_frame.layout())
      QWidget().setLayout(self.pl_frame.layout())
    self.pl_frame.setLayout(lt)

  def load_plugin(self, name, path):
    m = imp.load_source(name, path)
    p = m.MyPlugin()
    p.run()

    self.plugins[self.plugin_count] = p   
    self.plugin_count += 1


  def about(self):
    pass


if __name__ == '__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  app.setApplicationName('SPCanalyse')
  app.setOrganizationName('SPCanalyse Corporation')
  app.setOrganizationDomain('spcanalyse.com')

  w = MainWindow()
  w.resize(700,500)
  w.setWindowIcon(QIcon('pics/logo.png'))

  w.show()
  app.exec_()
  sys.exit()
