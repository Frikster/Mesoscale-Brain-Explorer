#!/usr/bin/env python3

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class PluginModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(PluginModel, self).__init__(parent)

class PipelineModel(QStandardItemModel):
  def __init__(self, parent=None):
    super(PipelineModel, self).__init__(parent)

  def supportedDropActions(self):
    return Qt.MoveAction | Qt.CopyAction

  def dropMimeData(self, data, action, row, column, parent):
    return super(PipelineModel, self).dropMimeData(data, action, row, column, parent)

  def flags(self, index):
    if not index.isValid() or index.row() >= self.rowCount() or index.model() != self:
       return Qt.ItemIsDropEnabled #we allow drops outside the items
    return super(PipelineModel, self).flags(index) & (~Qt.ItemIsDropEnabled)

  def removeRows(self, row, count, parent):
    #print('remove', row, count)
    return super(PipelineModel, self).removeRows(row, count, parent)

  def insertRows(self, row, count, parent):
    #print('insert', row, count)
    return super(PipelineModel, self).insertRows(row, count, parent)

  def get_plugin_names(self):
    ret = []
    for i in range(self.rowCount()):
      index = self.index(i, 0)
      value = str(self.data(index, Qt.UserRole))
      ret.append(value)
    return ret      

  def set_plugins(self, plugins):
    for name, title in plugins:
      item = QStandardItem(title)
      item.setData(name, Qt.UserRole)
      self.appendRow(item)

class PluginList(QListView):
  def __init__(self, plugins, parent=None):
    super(PluginList, self).__init__(parent)
    self.setModel(PluginModel())
    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')
    self.setDragEnabled(True)
    self.setDragDropMode(QAbstractItemView.DragOnly)

    for plugin in sorted(plugins, key=lambda x: plugins[x].name):
      item = QStandardItem(plugins[plugin].name)
      item.setData(plugin, Qt.UserRole)
      self.model().appendRow(item)

class PipelineList(QListView):
  def __init__(self, parent=None):
    super(PipelineList, self).__init__(parent)
    self.setStyleSheet('QListView::item { border: 0px; padding-left: 4px;'
      'height: 26px; }'
      'QListView::item::selected { background-color: #ccf; }')
    self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.setAcceptDrops(True)
    self.setDragEnabled(True)
    self.setDropIndicatorShown(True)
    self.setDragDropMode(QAbstractItemView.DragDrop)
    self.setDragDropOverwriteMode(False)

  def rowDropped(self, row):
    print(row)

  def startDrag(self, supportedActions): 
    self.setDefaultDropAction(Qt.MoveAction)
    super(PipelineList, self).startDrag(supportedActions)

  def dropEvent(self, event):
    super(PipelineList, self).dropEvent(event)

  def rowsInserted(self, parent, first, last):
    return super(PipelineList, self).rowsInserted(parent, first, last)

class PipeconfDialog(QDialog):
  def __init__(self, plugins, parent=None):
    super(PipeconfDialog, self).__init__(parent)

    self.setWindowTitle('Pipeline Configuration')

    self.plugin_list = PluginList(plugins)
    self.plugin_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.pipeline_list = PipelineList()
  
    hbox = QHBoxLayout()

    grid = QGridLayout()
    hbox.addLayout(grid)
    grid.addWidget(QLabel('Available plugins:'), 0, 0)
    grid.addWidget(QLabel('Pipeline:'), 0, 1)
    grid.addWidget(self.plugin_list, 1, 0)
    grid.addWidget(self.pipeline_list, 1, 1)

    vbox = QVBoxLayout()
    pb = QPushButton('Add')
    pb.clicked.connect(self.add_plugin)
    vbox.addWidget(pb)
    pb = QPushButton('Remove')
    pb.clicked.connect(self.remove_plugins)
    vbox.addWidget(pb)
    pb = QPushButton('Move up')
    pb.clicked.connect(self.move_up)
    vbox.addWidget(pb)
    pb = QPushButton('Move down')
    pb.clicked.connect(self.move_down)
    vbox.addWidget(pb)
    vbox.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
    pb = QPushButton('Close')
    pb.clicked.connect(self.hide)
    vbox.addWidget(pb)

    grid.addLayout(vbox, 1, 2)
    self.setLayout(hbox)

    self.resize(760, 440)

  def add_plugin(self):
    indices = self.plugin_list.selectionModel().selectedIndexes()
    if indices:
      for indice in indices:
          item = self.plugin_list.model().itemFromIndex(indice)
          self.pipeline_list.model().appendRow(QStandardItem(item))
    
  def remove_plugins(self):
    self.pipeline_list.setUpdatesEnabled(False)
    indices = self.pipeline_list.selectionModel().selectedIndexes()
    indices.sort()
    for index in reversed(indices):
      self.pipeline_list.model().removeRow(index.row())
    self.pipeline_list.setUpdatesEnabled(True)

  def move_up(self):
    self.pipeline_list.setUpdatesEnabled(False)
    indices = self.pipeline_list.selectionModel().selectedIndexes()
    first_row = indices and sorted(indices)[0].row() or None
    for index in sorted(indices):
      if first_row > 0:
        item = self.pipeline_list.model().takeRow(index.row())
        self.pipeline_list.model().insertRow(index.row()-1, item)
        new_index = self.pipeline_list.model().index(index.row()-1, 0)
        selection = QItemSelection(new_index, new_index)
        self.pipeline_list.selectionModel().select(selection, QItemSelectionModel.Select)
    self.pipeline_list.setUpdatesEnabled(True)

  def move_down(self):
    self.pipeline_list.setUpdatesEnabled(False)
    indices = self.pipeline_list.selectionModel().selectedIndexes()
    last_row = indices and sorted(indices, reverse=True)[0].row() or None
    for index in sorted(indices, reverse=True):
      if last_row < self.pipeline_list.model().rowCount()-1:
        item = self.pipeline_list.model().takeRow(index.row())
        self.pipeline_list.model().insertRow(index.row()+1, item)
        new_index = self.pipeline_list.model().index(index.row()+1, 0)
        selection = QItemSelection(new_index, new_index)
        self.pipeline_list.selectionModel().select(selection, QItemSelectionModel.Select)
    self.pipeline_list.setUpdatesEnabled(True)
    
