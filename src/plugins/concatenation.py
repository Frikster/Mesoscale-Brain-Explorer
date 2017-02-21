#!/usr/bin/env python3

import psutil
import qtutil

from .temporal_filter import *
from .util import mse_ui_elements as mue
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault


class Widget(QWidget, WidgetDefault):
    class Labels(WidgetDefault.Labels):
        pass

    class Defaults(WidgetDefault.Defaults):
        pass

    def __init__(self, project, plugin_position, parent=None):
        super(Widget, self).__init__(parent)

        if not project or not isinstance(plugin_position, int):
            return
        self.concat_butt = QPushButton('Concatenate')
        WidgetDefault.__init__(self, project, plugin_position)

            # self.plugin_position = plugin_position
        # self.project = project
        #
        # # define ui components and global data
        # self.view = MyGraphicsView(self.project)
        # self.video_list = QListView()
        # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.left = QFrame()
        # self.right = QFrame()
        # self.open_dialogs = []
        #
        # self.setup_ui()
        # self.selected_videos = []
        #
        # self.video_list.setModel(QStandardItemModel())
        # self.video_list.selectionModel().selectionChanged[QItemSelection,
        #                                                   QItemSelection].connect(self.selected_video_changed)
        # self.video_list.doubleClicked.connect(self.video_triggered)
        # for f in project.files:
        #     if f['type'] != 'video':
        #         continue
        #     item = QStandardItem(f['name'])
        #     item.setDropEnabled(False)
        #     self.video_list.model().appendRow(item)
        # self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    # def video_triggered(self, index):
    #     filename = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
    #     dialog = PlayerDialog(self.project, filename, self)
    #     dialog.show()
    #     self.open_dialogs.append(dialog)

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
        # vbox.addWidget(QLabel('Selection order determines concatenation order'))
        # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.video_list.setAcceptDrops(True)
        self.video_list.setDragEnabled(True)
        self.video_list.setDropIndicatorShown(True)
        self.video_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.video_list.setDefaultDropAction(Qt.MoveAction)
        self.video_list.setDragDropOverwriteMode(False)
        # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        # vbox.addWidget(self.video_list)
        self.vbox.addWidget(mue.InfoWidget('Note that there is no explicit progress bar. '
                                           'Note that videos can be dragged and dropped in the list but that the order'
                                           'in which they are selected determines concatenation order.'))
        hhbox = QHBoxLayout()
        hhbox.addWidget(self.concat_butt)
        self.vbox.addLayout(hhbox)
        self.vbox.addStretch()
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

    # def refresh_video_list_via_combo_box(self, trigger_item=None):
    #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
    #
    # def selected_video_changed(self, selected, deselected):
    #     pfs.selected_video_changed_multi(self, selected, deselected)

    def setup_signals(self):
        super().setup_signals()
        self.concat_butt.clicked.connect(self.execute_primary_function)


    def execute_primary_function(self, input_paths=None):
        if not input_paths:
            if not self.selected_videos:
                return
            else:
                selected_videos = self.selected_videos
        else:
            selected_videos = input_paths

        summed_filesize = 0
        for path in self.selected_videos:
            summed_filesize = summed_filesize + os.path.getsize(path)
        available = list(psutil.virtual_memory())[1]
        if summed_filesize > available:
            qtutil.critical("Not enough memory. Concatenated file is of size ~"+str(summed_filesize) +\
               " and available memory is: " + str(available))
            raise MemoryError("Not enough memory. Concatenated file is of size ~"+str(summed_filesize) +\
               " and available memory is: " + str(available))

        paths = selected_videos
        if len(paths) < 2:
            qtutil.warning('Select multiple files to concatenate.')
            return
        frames = [fileloader.load_file(f) for f in paths]
        frames = np.concatenate(frames)
        # concat_name = '_'.join(filenames) + '.npy'
        # concat_path = os.path.join(self.project.path, concat_name)
        # First one has to take the name otherwise pfs.save_projects doesn't work
        filenames = [os.path.basename(path) for path in paths]
        manip = 'concat_'+str(len(filenames))
        # long_ass_name = 'concat_'+'_concat_'.join(filenames[1:])
        # long_ass_name = long_ass_name.replace('.npy', '')
        output_path = pfs.save_project(paths[0], self.project, frames, manip, 'video')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])
        return [output_path]
        # path = os.path.join(self.project.path, str(uuid.uuid4()) + 'Concat.npy')
        # np.save(path, frames)
        # self.project.files.append({
        #     'path': path,
        #     'type': 'video',
        #     'manipulations': 'concat',
        #     'source': filenames
        # })
        # self.project.save()


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Concatenation'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self):
        self.summed_filesize = 0
        for path in self.widget.selected_videos:
            self.summed_filesize = self.summed_filesize + os.path.getsize(path)
        self.available = list(psutil.virtual_memory())[1]
        if self.summed_filesize > self.available:
            return False
        return True

    def automation_error_message(self):
        return "Not enough memory. Concatenated file is of size ~"+str(self.summed_filesize) +\
               " and available memory is: " + str(self.available)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget(None))
    w.show()
    app.exec_()
    sys.exit()