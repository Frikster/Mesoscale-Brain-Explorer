#!/usr/bin/env python

import os
import sys
import traceback
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *


class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project
    self.setup_ui()

    self.listview.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'video':
        self.listview.model().appendRow(QStandardItem(f['path']))

    #self.reference_frames_dict = {}

  def setup_ui(self):
    vbox = QVBoxLayout()

    pb = QPushButton('New Video')
    pb.clicked.connect(self.new_video)
    vbox.addWidget(pb)

    self.listview = QListView()
    self.listview.setStyleSheet('QListView::item { height: 26px; }')
    self.listview.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.listview)

    #right = QFrame()
    #right.setFrameShadow(QFrame.Raised)
    #right.setFrameShape(QFrame.Panel)
    #right.setContentsMargins(10, 0, 1, 0)
    #right.setMinimumWidth(200)

    #lt_right = QVBoxLayout()
    #lt_right.setContentsMargins(8, 8, 8, 8)

    #lt_right.addWidget(QLabel('Data type to be loaded'))
    #self.data_type_cb = QComboBox()
    #self.data_type_cb.addItem("uint8")
    #self.data_type_cb.addItem("float32")
    #self.data_type_cb.addItem("float64")
    #lt_right.addWidget(self.data_type_cb)

    #lt_right.addWidget(QLabel('Width'))
    #self.width_sb = QSpinBox()
    #self.width_sb.setMinimum(1)
    #self.width_sb.setMaximum(1024)
    #self.width_sb.setValue(256)
    #lt_right.addWidget(self.width_sb)
    #lt_right.addWidget(QLabel('Height'))
    #self.height_sb = QSpinBox()
    #self.height_sb.setMinimum(1)
    #self.height_sb.setMaximum(1024)
    #self.height_sb.setValue(256)
    #lt_right.addWidget(self.height_sb)

    #self.channel_no_sb = QSpinBox()
    #self.channel_no_sb.setMinimum(1)
    #self.channel_no_sb.setValue(3)
    #lt_right.addWidget(self.channel_no_sb)

    #lt_right.addWidget(QLabel('Frame to display'))
    #self.ref_frame_sb = QSpinBox()
    ##todo: Make the max the last frame in the file
    #self.ref_frame_sb.setMaximum(1000)
    #self.ref_frame_sb.setMinimum(0)
    #self.ref_frame_sb.setValue(400)
    #lt_right.addWidget(self.ref_frame_sb)

    #butt_file_load = QPushButton('&Load File')
    #butt_file_load.clicked.connect(self.import_file)
    #lt_right.addWidget(butt_file_load)

    #lt_right.addSpacerItem(QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
    #pb_done = QPushButton('&Done')
    #lt_right.addWidget(pb_done)

    #right.setLayout(lt_right)

    ## self.pixmap = QPixmap('../data/flower2.jpg')
    ## self.pic = QLabel()
    ## self.pic.setStyleSheet('background-color: black')
    ## self.pic.setPixmap(self.pixmap)
    ## left.addWidget(self.pic)

    #hbox.addLayout(left)
    #hbox.addWidget(right)

    #hbox.setStretch(0, 1)
    #hbox.setStretch(1, 0)

    self.setLayout(vbox)

  def import_file(self):
    """ Load an file to be analysed """
    print("working")
    print('Argument List:', str(sys.argv))

    width = self.width_sb.value()
    height = self.height_sb.value()
    data_type_str = str(self.data_type_cb.currentText())
    ref_frame = self.ref_frame_sb.value()
    channel_no = self.channel_no_sb.value()

    file_names = sys.argv[1:]

    if len(file_names) > 0:
      for fileName in file_names:
        if fileName != '':
          frames = self.load_raw(str(fileName), width, height, data_type_str, channel_no)
          self.reference_frames_dict[str(fileName)] = frames[ref_frame]

    print("LOOP FINISHED")
    print(str(self.reference_frames_dict))

    # Show image in Main window
    #self.vb.enableAutoRange()
    #if self.sidePanel.imageFileList.currentRow() == -1: self.sidePanel.imageFileList.setCurrentRow(0)
    #self.showImage(str(self.sidePanel.imageFileList.currentItem().text()))
    #self.vb.disableAutoRange()

  def load_raw(self, filename, width, height, dat_type, channel_no):
    dat_type = np.dtype(dat_type)

    with open(filename, "rb") as file:
      frames = np.fromfile(file, dtype=dat_type)

    total_number_of_frames = int(np.size(frames) / (width * height * channel_no))
    print("n_frames: " + str(total_number_of_frames))
    frames = np.reshape(frames, (total_number_of_frames, width, height, channel_no))

    #frames = np.reshape(frames, (total_number_of_frames, width, height))
    print("frames.shape PRE:"+str(frames.shape))
    # retrieve only one channel:
    # todo: make user definable
    frames = frames[:, :, :, 1]
    print("frames.shape POST:"+str(frames.shape))

    frames = np.asarray(frames, dtype=dat_type)
    plt.imshow(frames[self.ref_frame_sb.value()])
    return frames

  def new_video(self):
    filenames = QFileDialog.getOpenFileNames(
      self, 'Load images', QSettings().value('last_load_data_path').toString(),
      'Numpy files (*.npy)')
    filenames = map(str, filenames)
    if not filenames:
      return
    QSettings().setValue('last_load_data_path', os.path.dirname(filenames[0]))

    for filename in filenames:
      if filename in [f['path'] for f in self.project.files]:
        continue
      self.project.files.append({
        'path': filename,
        'type': 'video'
      })
      self.project.save()
      self.listview.model().appendRow(QStandardItem(filename))

    # try:
    #   total_number_of_frames = int(np.size(frames) / (width * height * channel_no))
    #   print("n_frames: " + str(total_number_of_frames))
    #   frames = np.reshape(frames, (total_number_of_frames, width, height, channel_no))
    #   frames = frames[:, :, :, 1]
    # except:
    #   print("Reshape failed. Attempting single channel")
    #   total_number_of_frames = int(np.size(frames) / (width * height))
    #   print("n_frames: " + str(total_number_of_frames))
    #   frames = np.reshape(frames, (total_number_of_frames, width, height))
    # frames = np.asarray(frames, dtype=dat_type)
    # return frames


class MyPlugin:
  def __init__(self, project):
    self.name = 'Import video files'
    self.widget = Widget(project)

  def run(self):
    pass


if __name__ == '__main__':
  app = QApplication(sys.argv)
  app.aboutToQuit.connect(app.deleteLater)
  w = QMainWindow()
  w.setCentralWidget(Widget())
  w.show()
  app.exec_()
  sys.exit()
