#!/usr/bin/env python3

import psutil
import qtutil

from .temporal_filter import *
from .util import mse_ui_elements as mue
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util.qt import MyProgressDialog


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

    def setup_ui(self):
        super().setup_ui()
        self.video_list.setAcceptDrops(True)
        self.video_list.setDragEnabled(True)
        self.video_list.setDropIndicatorShown(True)
        self.video_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.video_list.setDefaultDropAction(Qt.MoveAction)
        self.video_list.setDragDropOverwriteMode(False)
        self.vbox.addWidget(mue.InfoWidget('Note that there is no explicit progress bar. '
                                           'Note that videos can be dragged and dropped in the list but that the order '
                                           'in which they are *selected* determines concatenation order. The '
                                           'dragging and dropping is for convenience so you can organize your desired '
                                           'order and then shift select them from top to bottom to concatenate '
                                           'that selection in that order'))
        hhbox = QHBoxLayout()
        hhbox.addWidget(self.concat_butt)
        self.vbox.addLayout(hhbox)
        self.vbox.addStretch()

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
        frames = [file_io.load_file(f) for f in paths]
        progress = MyProgressDialog('Concatenation', 'Concatenating files...', self)
        progress.show()
        progress.setValue(1)
        frames = np.concatenate(frames)
        progress.setValue(99)
        # First one has to take the name otherwise pfs.save_projects doesn't work
        filenames = [os.path.basename(path) for path in paths]
        manip = 'concat-'+str(len(filenames))
        output_path = pfs.save_project(paths[0], self.project, frames, manip, 'video')
        pfs.refresh_list(self.project, self.video_list,
                         self.params[self.Labels.video_list_indices_label],
                         self.Defaults.list_display_type,
                         self.params[self.Labels.last_manips_to_display_label])
        progress.close()
        return [output_path]


class MyPlugin(PluginDefault):
    def __init__(self, project, plugin_position):
        self.name = 'Concatenation'
        self.widget = Widget(project, plugin_position)
        super().__init__(self.widget, self.widget.Labels, self.name)

    def check_ready_for_automation(self, expected_input_number):
        self.summed_filesize = 0
        for path in self.widget.selected_videos:
            self.summed_filesize = self.summed_filesize + os.path.getsize(path)
        self.available = list(psutil.virtual_memory())[1]
        if self.summed_filesize > self.available:
            return False
        return True

    def output_number_expected(self, expected_input_number=None):
        return 1

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