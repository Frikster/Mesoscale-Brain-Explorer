#!/usr/bin/env python3

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import filter_jeff as fj
from .util import project_functions as pfs
from .util.mygraphicsview import MyGraphicsView
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

    # self.plugin_position = plugin_position
    # self.project = project
    #
    # # define ui components and global data
    # self.view = MyGraphicsView(self.project)
    # self.video_list = QListView()
    # self.left = QFrame()
    # self.right = QFrame()
    #
    # self.setup_ui()
    # self.selected_videos = []
    #
    # self.video_list.setModel(QStandardItemModel())
    # self.video_list.selectionModel().selectionChanged[QItemSelection,
    #                                                   QItemSelection].connect(self.selected_video_changed)
    # for f in project.files:
    #   if f['type'] != 'video':
    #     continue
    #   self.video_list.model().appendRow(QStandardItem(f['name']))
    # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
    # self.video_list.doubleClicked.connect(self.video_triggered)

  # def video_triggered(self, index):
  #     pfs.video_triggered(self, index)

  def setup_ui(self):
      super().setup_ui()
    # vbox_view = QVBoxLayout()
    # vbox_view.addWidget(self.view)
    # self.view.vb.setCursor(Qt.CrossCursor)
    # self.left.setLayout(vbox_view)
    #
    # vbox = QVBoxLayout()
    # list_of_manips = pfs.get_list_of_project_manips(self.project)
    # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    # vbox.addWidget(self.toolbutton)
    # vbox.addWidget(QLabel('Choose video:'))
    # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    # vbox.addWidget(self.video_list)
      hhbox = QHBoxLayout()
    # butt_gsr = QPushButton('Global Signal Regression')
      hhbox.addWidget(self.butt_gsr)
      self.vbox.addLayout(hhbox)
      self.vbox.addStretch()
    # self.right.setLayout(vbox)
    #
    # splitter = QSplitter(Qt.Horizontal)
    # splitter.setHandleWidth(3)
    # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    # splitter.addWidget(self.left)
    # splitter.addWidget(self.right)
    # hbox_global = QHBoxLayout()
    # hbox_global.addWidget(splitter)
    # self.setLayout(hbox_global)

  def setup_signals(self):
      super().setup_signals()
      self.butt_gsr.clicked.connect(self.execute_primary_function)

  # def refresh_video_list_via_combo_box(self, trigger_item=None):
  #   pfs.refresh_video_list_via_combo_box(self, trigger_item)
  #
  # def selected_video_changed(self, selected, deselected):
  #   pfs.selected_video_changed_multi(self, selected, deselected)

  # def selected_video_changed(self, selected, deselected):
  #   if not selected.indexes():
  #     return
  #
  #   for index in deselected.indexes():
  #     vidpath = str(os.path.join(self.project.path,
  #                                index.data(Qt.DisplayRole))
  #                   + '.npy')
  #     self.selected_videos = [x for x in self.selected_videos if x != vidpath]
  #   for index in selected.indexes():
  #     vidpath = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
  #     if vidpath not in self.selected_videos and vidpath != 'None':
  #       self.selected_videos = self.selected_videos + [vidpath]
  #
  #   self.shown_video_path = str(os.path.join(self.project.path,
  #                                            selected.indexes()[0].data(Qt.DisplayRole))
  #                               + '.npy')
  #   frame = fileloader.load_reference_frame(self.shown_video_path)
  #   self.view.show(frame)


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
        frames = fileloader.load_file(video_path)
        callback(0.1)
        width = frames.shape[1]
        height = frames.shape[2]
        frames = fj.gsr(frames, width, height, callback)
        pfs.save_project(video_path, self.project, frames, self.Defaults.manip, 'video')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])
        callback(1)
    global_callback(1)

class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Global Signal Regression'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  def check_ready_for_automation(self):
    return True

  def automation_error_message(self):
      return "YOU SHOULD NOT BE ABLE TO SEE THIS"

