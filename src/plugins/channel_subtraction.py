#!/usr/bin/env python3

from .temporal_filter import *
from .util import custom_qt_items as cqt
import qtutil
import psutil
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
        WidgetDefault.__init__(self, project, plugin_position)

    def setup_ui(self):
        super().setup_ui()
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setAcceptDrops(True)
        self.video_list.setDragEnabled(True)
        self.video_list.setDropIndicatorShown(True)
        self.video_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.video_list.setDefaultDropAction(Qt.MoveAction)
        self.video_list.setDragDropOverwriteMode(False)
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        self.vbox.addWidget(cqt.InfoWidget('Press Ctrl or shift and then select your minuend first followed by '
                                           'subtrahend. Files can be dragged in the video list for convenience '
                                           'but the order does not determine which is the minuend and which the '
                                           'subtrahend.'))
        hhbox = QHBoxLayout()
        div_butt = QPushButton('Subtract second from first')
        hhbox.addWidget(div_butt)
        self.vbox.addLayout(hhbox)
        self.vbox.addStretch()
        div_butt.clicked.connect(self.sub_clicked)

    def sub_clicked(self):
        summed_filesize = 0
        for path in self.selected_videos:
            summed_filesize = summed_filesize + os.path.getsize(path)
        available = list(psutil.virtual_memory())[1]
        if summed_filesize > available:
            qtutil.critical("Not enough memory. Total is of size "+str(summed_filesize) +\
               " and available memory is: " + str(available))
            raise MemoryError("Not enough memory. Total is of size "+str(summed_filesize) +\
               " and available memory is: " + str(available))


        paths = self.selected_videos
        if len(paths) != 2:
            qtutil.warning('Select two files to subtract.')
            return
        frames = [file_io.load_file(f) for f in paths]
        min_len = min([len(f) for f in frames])
        frames = np.subtract(np.array(frames[0][0:min_len], dtype=np.float32),
                           np.array(frames[1][0:min_len], dtype=np.float32))
        frames = np.array(frames, dtype=np.float32)

        # First one has to take the name otherwise pfs.save_projects doesn't work
        manip = 'channel_sub'
        pfs.save_project(paths[0], self.project, frames, manip, 'video')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])

class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Channel Subtraction'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

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