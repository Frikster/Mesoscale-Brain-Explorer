import os
import shutil
import sys
import traceback

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import constants
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView

sys.path.append('..')
import qtutil

from .util.qt import FileTable, MyProgressDialog
from .util import fileloader
import functools
import tifffile as tiff
import cv2
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault

class Exporter(QWidget):
  def __init__(self, parent=None):
    super(Exporter, self).__init__(parent)

  def export_mp4(self, fileinfo, filename):
    pass
  
  def export_avi(self, filepath, filename, export_dtype, export_framerate):
    progress = MyProgressDialog('File Exporter', 'Writing to avi...', self)
    try:
      frames = fileloader.load_file(filepath)
      frames = frames.astype(export_dtype)
      # todo: 30 = export framerate needs to be user-decided
      video = cv2.VideoWriter(
        filename, cv2.VideoWriter_fourcc(*'DIVX'), export_framerate,
        (frames.shape[1], frames.shape[2]), False
      )
      for i, frame in enumerate(frames):
        progress.setValue(100 * i / float(len(frames)-1))
        video.write(frame)
      cv2.destroyAllWindows()
      video.release()
    except:
      progress.close()
      qtutil.critical('Video file could not be written.', self)
  
  def export_tif(self, filepath, filename, export_dtype):
    frames = fileloader.load_file(filepath)
    frames = frames.astype(export_dtype)
    tiff.imsave(filename, frames)
  
  def export_raw(self, filepath, filename, export_dtype):
    frames = fileloader.load_file(filepath)
    frames = frames.astype(export_dtype)
    frames.tofile(filename)
  
  def export_roi(self, fileinfo, filename):
    try:
      shutil.copyfile(fileinfo['path'], filename)
    except:
      qtutil.critical('File could not be copied.\n' + traceback.format_exc(), self)

class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    export_dtype_label = 'export_dtype_label'
    export_framerate_label = 'Export Framerate'

  class Defaults(WidgetDefault.Defaults):
    export_dtype_default = 0
    export_framerate_default = 30

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    self.project = project

    # define ui components and global data
    # self.view = MyGraphicsView(self.project)
    # self.video_list = MyListView()
    # self.left = QFrame()
    # self.right = QFrame()
    # self.left_cut_off = QSpinBox()
    # self.right_cut_off = QSpinBox()
    #
    # self.project = project
    # self.setup_ui()
    # self.open_dialogs = []
    # self.selected_videos = []
    # self.shown_video_path = None
    self.exporter = Exporter(self)
    self.export_pb = QPushButton('Export')
    self.framerate_sb = QSpinBox()
    self.cb_dtype = QComboBox()

    # self.video_list.setModel(QStandardItemModel())
    # self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
    # self.video_list.doubleClicked.connect(self.video_triggered)
    # for f in project.files:
    #     if f['type'] != 'video':
    #         continue
    #     self.video_list.model().appendRow(QStandardItem(f['name']))
    # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
    WidgetDefault.__init__(self, project, plugin_position)

  # def video_triggered(self, index):
  #     pfs.video_triggered(self, index)

  def setup_ui(self):
      super().setup_ui()
      # vbox_view = QVBoxLayout()
      # vbox_view.addWidget(self.view)
      # self.left.setLayout(vbox_view)
      #
      # vbox = QVBoxLayout()
      # list_of_manips = pfs.get_list_of_project_manips(self.project)
      # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
      # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
      # vbox.addWidget(self.toolbutton)
      # vbox.addWidget(QLabel('Choose video:'))
      # # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
      # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
      # # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
      # vbox.addWidget(self.video_list)
      self.vbox.addWidget(QLabel("Export Framerate (Hz)"))
      self.vbox.addWidget(self.framerate_sb)
      self.framerate_sb.setMinimum(1)
      self.framerate_sb.setMaximum(99999)
      for t in constants.DTYPES:
          self.cb_dtype.addItem(t)
      self.vbox.addWidget(self.cb_dtype)
      self.vbox.addWidget(self.export_pb)
      # self.right.setLayout(self.vbox)
      #
      # splitter = QSplitter(Qt.Horizontal)
      # splitter.setHandleWidth(3)
      # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
      # splitter.addWidget(self.left)
      # splitter.addWidget(self.right)
      # hbox_global = QHBoxLayout()
      # hbox_global.addWidget(splitter)
      # self.setLayout(hbox_global)
    # vbox = QVBoxLayout()
    #
    # self.table = FileTable(self.project.files)
    # self.table.setSelectionMode(QAbstractItemView.SingleSelection)
    # self.table.doubleClicked.connect(self.row_doubleclicked)
    # vbox.addWidget(self.table)
    #
    # pb = QPushButton('&Export')
    # pb.clicked.connect(self.export_clicked)
    # vbox.addWidget(pb)
    #
    # self.setLayout(vbox)

  def setup_signals(self):
      super().setup_signals()
      self.export_pb.clicked.connect(self.export_clicked)

  def setup_params(self, reset=False):
      super().setup_params(reset)
      if len(self.params) == 1 or reset:
          self.update_plugin_params(self.Labels.export_framerate_label, self.Defaults.export_framerate_default)
          self.update_plugin_params(self.Labels.export_dtype_label, self.Defaults.export_dtype_default)
      self.framerate_sb.setValue(self.params[self.Labels.export_framerate_label])
      self.cb_dtype.setCurrentIndex(self.params[self.Labels.export_dtype_label])

  def setup_param_signals(self):
      super().setup_param_signals()
      self.framerate_sb.valueChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                    self.Labels.export_framerate_label))
      self.cb_dtype.currentIndexChanged[int].connect(functools.partial(self.update_plugin_params,
                                                                       self.Labels.export_dtype_label))
      # def refresh_video_list_via_combo_box(self, trigger_item=None):
  #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
  #
  # def selected_video_changed(self, selected, deselected):
  #     pfs.selected_video_changed_multi(self, selected, deselected)

  def filedialog(self, name, filters):
    path = QSettings().value('export_path')
    dialog = QFileDialog(self)
    dialog.setWindowTitle('Export to')
    dialog.setDirectory(str(path))
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setOption(QFileDialog.DontUseNativeDialog)
    dialog.selectFile(name)
    dialog.setFilter(';;'.join(filters.values()))
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    if not dialog.exec_():
      return None
    filename = str(dialog.selectedFiles()[0])
    QSettings().setValue('export_path', os.path.dirname(filename))
    filter_ = str(dialog.selectedNameFilter())
    ext = [f for f in filters if filters[f] == filter_][0] 
    if not filename.endswith(ext):
      filename = filename + ext
    return filename

  def export_roi(self, fileinfo):
    """Ask for filename and call exporter function"""
    filters = {
      '.roi': 'ROI file (*.roi)'
    }
    default = 'name' in fileinfo and fileinfo['name'] or 'untitled'
    filename = self.filedialog(default, filters)
    if filename:
      assert(filename.endswith('.roi'))
      self.exporter.export_roi(fileinfo, filename)

  def export_video(self, filepath):
    """Ask for filename and dispatch based on requested file format"""
    filters = {
      #'.mp4': 'MP4 file (*.mp4)',
      '.avi': 'AVI file (*.avi)',
      '.tif': 'TIF file (*.tif)',
      '.raw': 'RAW file (*.raw)'
    }
    default = os.path.basename(filepath) or 'untitled'
    # default = 'name' in fileinfo and fileinfo['name'] or 'untitled'
    filename = self.filedialog(default, filters)
    if not filename:
      return
    export_dtype = self.cb_dtype.currentText()
    export_framerate = self.framerate_sb.value()

    if filename.endswith('.avi'):
      self.exporter.export_avi(filepath, filename, export_dtype, export_framerate)
    elif filename.endswith('.mp4'):
      self.exporter.export_mp4(filepath, filename)
    elif filename.endswith('.tif'):
      self.exporter.export_tif(filepath, filename, export_dtype)
    elif filename.endswith('.raw'):
      self.exporter.export_raw(filepath, filename, export_dtype)
    else:
      assert(False)

  def export(self, filepath):
      self.export_video(filepath)
    # """Dispatch according to field 'type'"""
    # if fileinfo['type'] == 'roi':
    #   self.export_roi(fileinfo)
    # elif fileinfo['type'] == 'video':
    #   self.export_video(filepath)
    # else:
    #   qtutil.critical('Unsupported file type.')

  def export_clicked(self):
    """Retrieve fileinfo and call export"""
    # rows = self.table.selectionModel().selectedRows()
    # if not rows:
    #   return
    # assert(len(rows) == 1)
    # f = self.table.model().get_entry(rows[0])

    #    f = self.shown_video_path
    progress = MyProgressDialog('Export Progress', 'Exporting files...', self)
    progress.show()
    for i, selected_video in enumerate(self.selected_videos):
        progress.setValue((i/len(self.selected_videos)) * 100)
        self.export(selected_video)
    progress.close()
  # def row_doubleclicked(self, index):
  #   """Retrieve fileinfo and call export"""
  #   f = self.table.model().get_entry(index)
  #   self.export(f)

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Export files'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def run(self):
    pass
