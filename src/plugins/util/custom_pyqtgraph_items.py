#!/usr/bin/env python3

import sys

import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.exporters.ImageExporter import ImageExporter
from pyqtgraph.graphicsItems.UIGraphicsItem import *


class QMenuCustom(QtGui.QMenu):
    """ Custum QMenu that closes on leaveEvent """
    def __init__(self,parent=None):
        QtGui.QMenu.__init__(self, parent)

    def leaveEvent(self,ev):
        self.hide()    
        
class QActionCustom(QtGui.QAction):
    """ QAction class modified to emit a single argument (an event)"""
    clickEvent = QtCore.Signal(object)
    def __init__(self, name="", parent=None):
        QtGui.QAction.__init__(self, name, parent)
        self.triggered.connect(self.clicked)
        # self.event = None

    def updateEvent(self,event):
        self.event = event

    def clicked(self):
        self.clickEvent.emit(self.event)       


class GradientLegend(UIGraphicsItem):
  def __init__(self, min_label, max_label, cm_type):
    super(GradientLegend, self).__init__(self)
    self.labels = {max_label: 1, min_label: 0}
    self.cm_type = cm_type
    self.labelsize = QtCore.QSize(0, 0)

  def maximumLabelSize(self, p):
    width, height = 0, 0
    for label in self.labels:
      b = p.boundingRect(QtCore.QRectF(0, 0, 0, 0), QtCore.Qt.AlignLeft
                         | QtCore.Qt.AlignVCenter, str(label))
      width = max(b.width(), width)
      height = max(b.height(), height)
    self.labelsize = QtCore.QSize(width, height)
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
      color = plt.get_cmap(self.cm_type)(i)
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
    self.labelsize = self.maximumLabelSize(p)
    lh = self.labelsize.height()
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



class ImageExporterCustom(ImageExporter):
    """
    Subclass to change preferred image output to bmp. Currently there are some issues
    with png, as it creates some lines around the image
    """
    def __init__(self, item):
        ImageExporter.__init__(self, item)

    def export(self, fileName=None, toBytes=False, copy=False):
        if fileName is None and not toBytes and not copy:
            filter = ["*."+str(f) for f in QtGui.QImageWriter.supportedImageFormats()]
            preferred = ['*.bmp', '*.png', '*.tif', '*.jpg']
            for p in preferred[::-1]:
                if p in filter:
                    filter.remove(p)
                    filter.insert(0, p)
            self.fileSaveDialog(filter=filter)
            return

        targetRect = QtCore.QRect(0, 0, self.params['width'], self.params['height'])
        sourceRect = self.getSourceRect()

        bg = np.empty((self.params['width'], self.params['height'], 4), dtype=np.ubyte)
        color = self.params['background']
        bg[:,:,0] = color.blue()
        bg[:,:,1] = color.green()
        bg[:,:,2] = color.red()
        bg[:,:,3] = color.alpha()
        self.png = pg.makeQImage(bg, alpha=True)

        origTargetRect = self.getTargetRect()
        resolutionScale = targetRect.width() / origTargetRect.width()

        painter = QtGui.QPainter(self.png)
        try:
            self.setExportMode(True, {'antialias': self.params['antialias'], 'background': self.params['background'], 'painter': painter, 'resolutionScale': resolutionScale})
            painter.setRenderHint(QtGui.QPainter.Antialiasing, self.params['antialias'])
            self.getScene().render(painter, QtCore.QRectF(targetRect), QtCore.QRectF(sourceRect))
        finally:
            self.setExportMode(False)
        painter.end()

        if copy:
            QtGui.QApplication.clipboard().setImage(self.png)
        elif toBytes:
            return self.png
        else:
            self.png.save(fileName)
