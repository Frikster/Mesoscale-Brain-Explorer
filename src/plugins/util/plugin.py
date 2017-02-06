from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .mygraphicsview import MyGraphicsView
from .qt import MyListView

from . import project_functions as pfs

class Plugin_default:
    def __init__(self, widget, widget_labels, name):
        self.name = name
        self.widget = widget
        self.widget_labels = widget_labels

    def run(self, input_paths=None):
        self.widget.params = self.widget.project.pipeline[self.widget.plugin_position]
        return self.widget.cut_off(input_paths)

    def get_input_paths(self):
        fs = self.widget.project.files
        indices = self.widget.params[self.widget_labels.video_list_indices_label]
        return [fs[i]['path'] for i in range(len(fs)) if i in indices]

    def check_ready_for_automation(self):
        return False

    def automation_error_message(self):
        return "Plugin " + self.name + " is not suitable for automation."

class Widget_default(QWidget):
    class Labels:
        video_list_indices_label = 'video_list_indices'
        last_manips_to_display_label = 'last_manips_to_display'

    class Defaults:
        video_list_indices_default = [0]
        last_manips_to_display_default = ['All']
        list_display_type = ['video']

    def __init__(self, project, plugin_position):
        super(Widget_default, self).__init__()
        if not project:
            return
        self.plugin_position = plugin_position
        self.project = project
        self.labels = self.get_labe

        # define ui components and global data
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.video_list.setModel(QStandardItemModel())
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.left = QFrame()
        self.right = QFrame()
        self.video_list_indices = []
        self.toolbutton_values = []
        self.open_dialogs = []
        self.selected_videos = []
        self.shown_video_path = None

        self.setup_ui()
        self.setup_signals()
        self.setup_signals()
        if isinstance(plugin_position, int):
            self.params = project.pipeline[self.plugin_position]
            self.setup_param_signals()
            try:
                self.setup_params()
            except:
                self.setup_params(reset=True)
            pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                             self.Defaults.list_display_type, self.toolbutton_values)

    def video_triggered(self, index):
        pfs.video_triggered(self, index)

    def setup_ui(self):
        vbox_view = QVBoxLayout()
        vbox_view.addWidget(self.view)
        self.left.setLayout(vbox_view)

        vbox = QVBoxLayout()
        vbox.addWidget(self.toolbutton)
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)

        self.right.setLayout(vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

    def setup_signals(self):
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)

    def setup_params(self, reset=False):
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.video_list_indices_label, self.Defaults.video_list_indices_default)
            self.update_plugin_params(self.Labels.last_manips_to_display_label, self.Defaults.last_manips_to_display_default)
        self.video_list_indices = self.params[self.Labels.video_list_indices_label]
        self.toolbutton_values = self.params[self.Labels.last_manips_to_display_label]
        manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
                                  if self.toolbutton.itemText(i) in self.params[self.Labels.last_manips_to_display_label]]
        for item in manip_items:
            item.setCheckState(Qt.Checked)
        not_checked = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
                       if self.toolbutton.itemText(i) not in self.params[self.Labels.last_manips_to_display_label]]
        for item in not_checked:
            item.setCheckState(Qt.Unchecked)

    def setup_param_signals(self):
        self.video_list.selectionModel().selectionChanged.connect(self.prepare_video_list_for_update)
        self.toolbutton.activated.connect(self.prepare_toolbutton_for_update)

    def prepare_video_list_for_update(self, selected, deselected):
        val = [v.row() for v in self.video_list.selectedIndexes()]
        self.update_plugin_params(self.Labels.video_list_indices_label, val)

    def prepare_toolbutton_for_update(self, trigger_item):
        val = self.params[self.Labels.last_manips_to_display_label]
        selected = self.toolbutton.itemText(trigger_item)
        if selected not in val:
            val = val + [selected]
            if trigger_item != 0:
                val = [manip for manip in val if manip not in self.Defaults.last_manips_to_display_default]
        else:
            val = [manip for manip in val if manip != selected]

        self.update_plugin_params(self.Labels.last_manips_to_display_label, val)

    def update_plugin_params(self, key, val):
        pfs.update_plugin_params(self, key, val)

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, self.Defaults.list_display_type, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def execute_primary_function(self, input_paths = None):
        pass