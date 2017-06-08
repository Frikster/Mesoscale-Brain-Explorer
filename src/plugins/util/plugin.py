import functools
import os

import qtutil
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import project_functions as pfs
from .mygraphicsview import MyGraphicsView
from .qt import MyListView


class PrimaryFunctionMissing(Exception):
    def __init__(self, message):
        self.message = message


class WidgetDefault(object):
    class Labels(object):
        video_list_indices_label = 'video_list_indices'
        last_manips_to_display_label = 'last_manips_to_display'
        video_player_scaled_label = 'video_player_scaled'
        video_player_unscaled_label = 'video_player_unscaled'
        delete_signal_label = 'delete_signal'
        detatch_signal_label = 'detatch_signal'

    class Defaults(object):
        video_list_indices_default = [0]
        last_manips_to_display_default = ['All']
        list_display_type = ['video']

    def __init__(self, project, plugin_position):
        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project

        # define ui components and global data
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.video_list.setModel(QStandardItemModel())
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.execute_primary_function_button = QPushButton('&Execute')
        self.left = QFrame()
        self.right = QFrame()
        self.vbox_view = QVBoxLayout()
        self.vbox = QVBoxLayout()
        self.video_list_indices = []
        self.toolbutton_values = []
        self.open_dialogs = []
        self.selected_videos = []
        self.shown_video_path = None

        self.setup_ui()
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
        self.setup_whats_this()

    def video_triggered(self, index, scaling=False):
        pfs.video_triggered(self, index, scaling)

    def setup_ui(self):
        self.vbox_view.addWidget(self.view)
        self.left.setLayout(self.vbox_view)

        self.vbox.addWidget(self.toolbutton)
        self.vbox.addWidget(QLabel('Choose video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        self.vbox.addWidget(self.video_list)

        self.right.setLayout(self.vbox)

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
        self.video_list.video_player_scaled_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.video_player_scaled_label))
        self.video_list.video_player_unscaled_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.video_player_unscaled_label))
        self.video_list.delete_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.delete_signal_label))
        self.video_list.detatch_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.detatch_signal_label))

    def prepare_context_menu_signal_for_action(self, key):
        if key == self.Labels.video_player_scaled_label:
            self.video_triggered(self.video_list.currentIndex(), True)
        if key == self.Labels.video_player_unscaled_label:
            self.video_triggered(self.video_list.currentIndex(), False)
        if key == self.Labels.delete_signal_label:
            self.remove_clicked()
        if key == self.Labels.detatch_signal_label:
            self.detatch_clicked()

    def remove_clicked(self):
        for path in self.selected_videos:
            norm_path = os.path.normpath(path)
            self.project.files[:] = [f for f in self.project.files if os.path.normpath(f['path']) != norm_path]
        self.project.save()
        for path in self.selected_videos:
            try:
                os.remove(path)
            except:
                qtutil.critical('Could not delete file ' + path)
                return
        pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                         self.Defaults.list_display_type, self.toolbutton_values)

    def detatch_clicked(self):
       for path in self.selected_videos:
            norm_path = os.path.normpath(path)
            self.project.files[:] = [f for f in self.project.files if os.path.normpath(f['path']) != norm_path]
       self.project.save()
       pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                        self.Defaults.list_display_type, self.toolbutton_values)

    def setup_params(self, reset=False):
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.video_list_indices_label, self.Defaults.video_list_indices_default)
            self.update_plugin_params(self.Labels.last_manips_to_display_label,
                                      self.Defaults.last_manips_to_display_default)
        self.video_list_indices = self.params[self.Labels.video_list_indices_label]
        self.toolbutton_values = self.params[self.Labels.last_manips_to_display_label]
        manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
                                  if self.toolbutton.itemText(i) in self.params[
                           self.Labels.last_manips_to_display_label]]
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

    def save_dock_windows(self):
        pfs.save_dock_windows(self, 'misc_window')

    def load_dock_windows(self):
        pfs.load_dock_windows(self, 'misc_window')

    def execute_primary_function(self, input_paths=None):
        raise PrimaryFunctionMissing("Your custom plugin does not have a primary function."
                                     "Override this method")

    def setup_whats_this(self):
        self.video_list.setWhatsThis("List of files available for manipulation in this plugin. "
                                     "Double click a file to load the video player for it. Right click for additional "
                                     "options. "
                                     "Note that some plugins may have unique lists so if you don't "
                                     "see the file you are looking for you may be in the wrong plugin. "
                                     "In most cases Multiple files can be selected allowing for bulk processing. ")
        self.toolbutton.setWhatsThis("Filter allowing you to set which files to view. Files are filtered "
                                     "based on the last manipulation they went through. Note that sometimes "
                                     "'All' may be displayed despite not all files being in view. "
                                     "This is a limitation. Simply click the dropdown list and check which options "
                                     "are really selected.")


class PluginDefault:
    def __init__(self, widget, widget_labels_class, name):
        self.name = name
        self.widget = widget
        if hasattr(self.widget, 'project') and hasattr(self.widget, 'plugin_position'):
            self.widget.params = self.widget.project.pipeline[self.widget.plugin_position]
        self.widget_labels = widget_labels_class

    def run(self, input_paths=None):
        return self.widget.execute_primary_function(input_paths)

    def get_input_paths(self):
        return self.widget.selected_videos

    def output_number_expected(self, expected_input_number=None):
        if expected_input_number:
            return expected_input_number
        else:
            return len(self.get_input_paths())

    def check_ready_for_automation(self, expected_input_number):
        return False

    def automation_error_message(self):
        return "Plugin " + self.name + " is not suitable for automation."
