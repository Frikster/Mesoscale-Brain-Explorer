#!/usr/bin/env python

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.UIGraphicsItem import *

from util import filter_jeff
from util.mygraphicsview import MyGraphicsView
from util.qt import MyListView, MyProgressDialog

from util import fileloader

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math

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

def colorize_spc(spc_map):
  spc_map[np.isnan(spc_map)] = 0.0
  gradient_range = matplotlib.colors.Normalize(-1.0, 1.0)
  spc_map_color = matplotlib.cm.ScalarMappable(
    gradient_range, 'jet').to_rgba(spc_map, bytes=True)

  spc_map_color = spc_map_color.swapaxes(0, 1)
  if spc_map_color.ndim == 2:
    spc_map_color = spc_map_color[:, ::-1]
  elif spc_map_color.ndim == 3:
    spc_map_color = spc_map_color[:, ::-1, :]
  return spc_map_color

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

class GradientLegend(UIGraphicsItem):
  def __init__(self):
    super(GradientLegend, self).__init__(self)

    self.labels = {'max': 1, 'min': 0}

  def maximumLabelSize(self, p):
    width, height = 0, 0
    for label in self.labels:
      b = p.boundingRect(QtCore.QRectF(0, 0, 0, 0), QtCore.Qt.AlignLeft
                         | QtCore.Qt.AlignVCenter, str(label))
      width = max(b.width(), width)
      height = max(b.height(), height)
    return QtCore.QSize(width, height)

  def paint(self, p, opt, widget):
    super(GradientLegend, self).paint(p, opt, widget)
    pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
    rect = self.boundingRect()
    unit = self.pixelSize()

    offset = 10, 10
    size = 30, 200
    padding = 10

    x1 = rect.left() + unit[0] * offset[0]
    x2 = x1 + unit[0] * size[0]
    y1 = rect.bottom() - unit[1] * offset[1]
    y2 = y1 - unit[1] * size[1]

    # Draw background
    p.setPen(pen)
    p.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255, 100)))
    rect = QtCore.QRectF(
        QtCore.QPointF(x1 - padding * unit[0], y1 + padding * unit[1]),
        QtCore.QPointF(x2 + padding * unit[0], y2 - padding * unit[1])
    )
    p.drawRect(rect)

    p.scale(unit[0], unit[1])

    # Draw color bar
    gradient = QtGui.QLinearGradient()
    i = 0.0
    while i < 1:
      color = plt.cm.jet(i)
      color = [x * 255 for x in color]
      gradient.setColorAt(i, QtGui.QColor(*color))
      i += 0.1
    gradient.setStart(0, y1 / unit[1])
    gradient.setFinalStop(0, y2 / unit[1])
    p.setBrush(gradient)
    rect = QtCore.QRectF(
      QtCore.QPointF(x1 / unit[0], y1 / unit[1]),
      QtCore.QPointF(x2 / unit[0], y2 / unit[1])
    )
    p.drawRect(rect)

    # Draw labels
    labelsize = self.maximumLabelSize(p)
    lh = labelsize.height()
    p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
    for label in self.labels:
      y = y1 + self.labels[label] * (y2 - y1)
      p.drawText(QtCore.QRectF(x1, y-lh/2.0, 1000, lh),
                 QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, str(label))

class SPCMapDialog(QDialog):
  def __init__(self, project, video_path, spcmap, parent=None):
    super(SPCMapDialog, self).__init__(parent)
    self.project = project
    self.video_path = video_path
    self.spc = spcmap
    self.setup_ui()
    self.setWindowTitle('SPC')

    self.view.show(colorize_spc(spcmap))
    self.view.vb.clicked.connect(self.vbc_clicked)
    self.view.vb.hovering.connect(self.vbc_hovering)

    l = GradientLegend()
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
    self.view.show(colorize_spc(self.spc))

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
#    if not math.isnan(spc[int(x), int(y)]):
#      self.the_label.setText('Correlation value at crosshair: '
#                             + str(spc[int(x), int(y)]))

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)
    if not project:
      return
    self.project = project
    self.setup_ui()

    self.video_path = None
    self.open_dialogs = []

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
    for f in project.files:
      if f['type'] != 'video':
        continue
      self.video_list.model().appendRow(QStandardItem(f['path']))
    self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))

    self.view.vb.clicked.connect(self.vbc_clicked)

  def setup_ui(self):
    hbox = QHBoxLayout()
    self.view = MyGraphicsView(self.project) 
    hbox.addWidget(self.view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Choose video:'))
    self.video_list = MyListView()
    vbox.addWidget(self.video_list)
    vbox.addStretch()
    vbox.addWidget(InfoWidget('Click on the image to generate SPC map.'))
    
    hbox.addLayout(vbox)    
    hbox.setStretch(0, 1)
    hbox.setStretch(1, 0)
    self.setLayout(hbox)

  def selected_video_changed(self, selection):
    if not selection.indexes():
      return
    self.video_path = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
    frame = fileloader.load_reference_frame(self.video_path)
    self.view.show(frame)

  def vbc_clicked(self, x, y):
    if not self.video_path:
      return

    progress = MyProgressDialog('SPC Map', 'Generating correlation map...', self)
    spc = calc_spc(self.video_path, x, y, progress)
    dialog = SPCMapDialog(self.project, self.video_path, spc, self)
    dialog.show()
    self.open_dialogs.append(dialog)

class MyPlugin:
  def __init__(self, project):
    self.name = 'SPC map'
    self.widget = Widget(project)

  def run(self):
    pass
