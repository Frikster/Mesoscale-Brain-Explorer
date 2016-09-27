#!/usr/bin/env python3

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.UIGraphicsItem import *

from .util import filter_jeff
from .util.mygraphicsview import MyGraphicsView
from .util.qt import MyListView, MyProgressDialog, InfoWidget
from .util.gradient import GradientLegend

from .util import fileloader

import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math
import multiprocessing

def calc_spc(video_path, x, y, progress):
    frame = fileloader.load_reference_frame(video_path)
    width, height = frame.shape

    x = int(x)
    y = int(height - y)

    frames = fileloader.load_file(video_path)

    spc_map = filter_jeff.correlation_map(y, x, frames, progress)

    # Make the location of the seed - self.image[y,x] - blatantly obvious
    spc_map[y+1, x+1] = 1
    spc_map[y+1, x] = 1
    spc_map[y, x+1] = 1
    spc_map[y-1, x-1] = 1
    spc_map[y-1, x] = 1
    spc_map[y, x-1] = 1
    spc_map[y+1, x-1] = 1
    spc_map[y-1, x+1] = 1

    return spc_map



class InfoWidget(QFrame):
    def __init__(self, text, parent=None):
        super(InfoWidget, self).__init__(parent)
        self.setup_ui(text)
  
    def setup_ui(self, text):
        hbox = QHBoxLayout()
        icon = QLabel()
        image = QImage('pics/info.png')
        icon.setPixmap(QPixmap.fromImage(image.scaled(40, 40)))
        hbox.addWidget(icon)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        hbox.addWidget(self.label)
        hbox.addStretch()
        self.setLayout(hbox)

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet('QFrame{background-color: #999; border-radius: 10px;}')

class SPCMapDialog(QDialog):
    def __init__(self, project, video_path, spcmap, cm_type, parent=None):
        super(SPCMapDialog, self).__init__(parent)
        self.project = project
        self.video_path = video_path
        self.spc = spcmap
        self.cm_type = cm_type
        self.setup_ui()
        self.setWindowTitle('SPC')

        self.view.show(self.colorize_spc(spcmap))
        self.view.vb.clicked.connect(self.vbc_clicked)
        self.view.vb.hovering.connect(self.vbc_hovering)

        l = GradientLegend(-1.0, 1.0, cm_type)
        l.setParentItem(self.view.vb)

    def setup_ui(self):
        vbox = QVBoxLayout()
        self.the_label = QLabel()
        vbox.addWidget(self.the_label)
        self.view = MyGraphicsView(self.project)
        vbox.addWidget(self.view)
        self.setLayout(vbox)

    def vbc_clicked(self, x, y):
        progress = MyProgressDialog('SPC Map', 'Recalculating...', self)
        self.spc = calc_spc(self.video_path, x, y, progress)
        self.view.show(self.colorize_spc(self.spc))

    def colorize_spc(self, spc_map):
        spc_map[np.isnan(spc_map)] = 0.0
        #todo: http://stackoverflow.com/questions/22548813/python-color-map-but-with-all-zero-values-mapped-to-black
        # a = np.ma.masked_where(spc_map == 0, spc_map)
        # cmap = plt.cm.OrRd
        gradient_range = matplotlib.colors.Normalize(-1.0, 1.0)
        #cmap.set_bad(color='black')
        spc_map_color = matplotlib.cm.ScalarMappable(
          gradient_range, self.cm_type).to_rgba(spc_map, bytes=True)

        spc_map_color = spc_map_color.swapaxes(0, 1)
        if spc_map_color.ndim == 2:
          spc_map_color = spc_map_color[:, ::-1]
        elif spc_map_color.ndim == 3:
          spc_map_color = spc_map_color[:, ::-1, :]
        return spc_map_color

    def vbc_hovering(self, x, y):
        x_origin, y_origin = self.project['origin']
        mmpixel = self.project['mmpixel']
        x = x / mmpixel
        y = y / mmpixel
        spc = self.spc.swapaxes(0, 1)
        spc = spc[:, ::-1]
        try:
          value = str(spc[int(x)+int(x_origin), int(y)+int(y_origin)])
        except:
          value = '-'
        self.the_label.setText('Correlation value at crosshair: {}'.format(value))

class Widget(QWidget):
    def __init__(self, project, parent=None):
        super(Widget, self).__init__(parent)
        if not project:
          return
        self.project = project
        self.setup_ui()
        self.cm_type = self.cm_comboBox.itemText(0)

        self.video_path = None
        self.open_dialogs = []

        self.video_list.setModel(QStandardItemModel())
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        for f in project.files:
          if f['type'] != 'video':
            continue
          self.video_list.model().appendRow(QStandardItem(f['name']))
        self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
        self.cm_comboBox.activated[str].connect(self.cm_choice)
        self.view.vb.clicked.connect(self.vbc_clicked)

    def setup_ui(self):
        hbox = QHBoxLayout()
        self.view = MyGraphicsView(self.project)
        hbox.addWidget(self.view)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Choose video:'))
        self.video_list = MyListView()
        vbox.addWidget(self.video_list)

        vbox.addWidget(QLabel('Choose colormap:'))
        self.cm_comboBox = QtGui.QComboBox(self)
        self.cm_comboBox.addItem("jet")
        self.cm_comboBox.addItem("viridis")
        self.cm_comboBox.addItem("inferno")
        self.cm_comboBox.addItem("plasma")
        self.cm_comboBox.addItem("magma")
        self.cm_comboBox.addItem("seismic")
        self.cm_comboBox.addItem("rainbow")
        vbox.addWidget(self.cm_comboBox)

        vbox.addStretch()
        vbox.addWidget(InfoWidget('Click on the image to generate SPC map.'))

        hbox.addLayout(vbox)
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 0)
        self.setLayout(hbox)

    def cm_choice(self, cm_choice):
        self.cm_type = cm_choice

    def selected_video_changed(self, selection):
        if not selection.indexes():
          return
        self.video_path = str(os.path.join(self.project.path,
                                       selection.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)

    def vbc_clicked(self, x, y):
        if not self.video_path:
          return

        progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
        spc = calc_spc(self.video_path, x, y, progress)
        dialog = SPCMapDialog(self.project, self.video_path, spc, self.cm_type, self)
        dialog.show()
        self.open_dialogs.append(dialog)

class MyPlugin:
    def __init__(self, project):
        self.name = 'SPC map'
        self.widget = Widget(project)

    def run(self):
        pass
