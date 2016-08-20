#!/usr/bin/env python

import sys
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.UIGraphicsItem import *

import matplotlib.pyplot as plt

class GradientLegend(UIGraphicsItem):
  def __init__(self, min_label, max_label):
    super(GradientLegend, self).__init__(self)
    self.labels = {max_label: 1, min_label: 0}

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
    pen = QtGui.QPen(QtGui.QColor(0,0,0))
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
    p.setBrush(QtGui.QBrush(QtGui.QColor(255,255,255,100)))
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


if __name__ == '__main__':
    app = pg.mkQApp()
    win = pg.GraphicsWindow()
    view = win.addViewBox()
    view.setAspectLocked(True)
    l = GradientLegend('min', 'max')
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
