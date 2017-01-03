#!/usr/bin/env python3

from .temporal_filter import *
from .util import mse_ui_elements as mue
import qtutil
from .videoplayer import PlayerDialog

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)

        if not project:
            return
        self.project = project

        # define ui components and global data
        self.view = MyGraphicsView(self.project)
        self.video_list = QListView()
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.left = QFrame()
        self.right = QFrame()
        self.open_dialogs = []

        self.setup_ui()
        self.selected_videos = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                          QItemSelection].connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        for f in project.files:
            if f['type'] != 'video':
                continue
            item = QStandardItem(f['name'])
            item.setDropEnabled(False)
            self.video_list.model().appendRow(item)
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    def video_triggered(self, index):
        filename = str(os.path.join(self.project.path, index.data(Qt.DisplayRole)) + '.npy')
        dialog = PlayerDialog(self.project, filename, self)
        dialog.show()
        self.open_dialogs.append(dialog)

    def setup_ui(self):
        vbox_view = QVBoxLayout()
        vbox_view.addWidget(self.view)
        self.view.vb.setCursor(Qt.CrossCursor)
        self.left.setLayout(vbox_view)

        vbox = QVBoxLayout()
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        vbox.addWidget(self.toolbutton)
        vbox.addWidget(QLabel('Selection order determines concatenation order'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setAcceptDrops(True)
        self.video_list.setDragEnabled(True)
        self.video_list.setDropIndicatorShown(True)
        self.video_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.video_list.setDefaultDropAction(Qt.MoveAction)
        self.video_list.setDragDropOverwriteMode(False)
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        vbox.addWidget(self.video_list)
        vbox.addWidget(mue.InfoWidget('This operation requires as much memory as the combined size of all selected '
                                      'stacks in the project directory. Note also there is no explicit progress bar'))
        hhbox = QHBoxLayout()
        div_butt = QPushButton('Divide first by second')
        hhbox.addWidget(div_butt)
        vbox.addLayout(hhbox)
        vbox.addStretch()
        div_butt.clicked.connect(self.div_clicked)
        self.right.setLayout(vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def div_clicked(self):
        paths = self.selected_videos
        if len(paths) != 2:
            qtutil.warning('Select 2 files to divide.')
            return
        frames = [fileloader.load_file(f) for f in paths]
        frames = np.divide(frames[0], frames[1])

        # concat_name = '_'.join(filenames) + '.npy'
        # concat_path = os.path.join(self.project.path, concat_name)
        # First one has to take the name otherwise pfs.save_projects doesn't work
        filenames = [os.path.basename(path) for path in paths]
        manip = 'channel_math_'+str(len(filenames))
        # long_ass_name = 'concat_'+'_concat_'.join(filenames[1:])
        # long_ass_name = long_ass_name.replace('.npy', '')
        pfs.save_project(paths[0], self.project, frames, manip, 'video')
        pfs.refresh_all_list(self.project, self.video_list)

        # path = os.path.join(self.project.path, str(uuid.uuid4()) + 'Concat.npy')
        # np.save(path, frames)
        # self.project.files.append({
        #     'path': path,
        #     'type': 'video',
        #     'manipulations': 'concat',
        #     'source': filenames
        # })
        # self.project.save()


class MyPlugin:
    def __init__(self, project):
        self.name = 'Channel Math'
        self.widget = Widget(project)

    def run(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget(None))
    w.show()
    app.exec_()
    sys.exit()