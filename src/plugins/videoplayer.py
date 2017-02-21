# #!/usr/bin/env python3
#
# import numpy as np
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
#
# from .util.mygraphicsview import MyGraphicsView
# from .util.qt import FileTable, FileTableModel
#
#
# class PlayerDialog(QDialog):
#   def __init__(self, project, filename, parent=None):
#     super(PlayerDialog, self).__init__(parent)
#     self.project = project
#     self.setup_ui()
#
#     self.fp = np.load(filename, mmap_mode='r')
#     self.slider.setMaximum(len(self.fp)-1)
#     self.show_frame(0)
#
#   def show_frame(self, frame_num):
#     frame = self.fp[frame_num]
#     self.label_frame.setText(str(frame_num) + ' / ' + str(len(self.fp)-1))
#     self.view.show(frame)
#
#   def setup_ui(self):
#     vbox = QVBoxLayout()
#     self.view = MyGraphicsView(self.project)
#     vbox.addWidget(self.view)
#     hbox = QHBoxLayout()
#     self.slider = QSlider(Qt.Horizontal)
#     self.slider.valueChanged.connect(self.slider_moved)
#     hbox.addWidget(self.slider)
#     self.label_frame = QLabel('- / -')
#     hbox.addWidget(self.label_frame)
#     vbox.addLayout(hbox)
#     self.setLayout(vbox)
#
#   def slider_moved(self, value):
#     self.show_frame(value)
#
# class Widget(QWidget):
#   def __init__(self, project, parent=None):
#     super(Widget, self).__init__(parent)
#     if not project:
#       return
#     self.project = project
#     self.setup_ui()
#
#     videos = [f for f in self.project.files if f['type'] == 'video']
#     self.table.setModel(FileTableModel(videos))
#     self.table.doubleClicked.connect(self.video_triggered)
#     self.table.setSelectionMode(QAbstractItemView.SingleSelection)
#
#     self.open_dialogs = []
#
#   def setup_ui(self):
#     vbox = QVBoxLayout()
#     self.table = FileTable()
#     vbox.addWidget(self.table)
#     self.setLayout(vbox)
#
#   def video_triggered(self, index):
#     filename = self.table.model().get_path(index)
#     dialog = PlayerDialog(self.project, filename, self)
#     dialog.show()
#     self.open_dialogs.append(dialog)
#
# class MyPlugin:
#   def __init__(self, project, plugin_position):
#     self.name = 'Play video'
#     self.widget = Widget(project)
#
#   def run(self):
#     pass
#
