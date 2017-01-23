#!/usr/bin/env python3
# -*- coding: cp1252 -*-

import pyqtgraph as pg
from PyQt4.QtGui import *

from .viewboxcustom import MultiRoiViewBox

class MyGraphicsView(pg.GraphicsView):
  def __init__(self, project, parent=None):
    super(MyGraphicsView, self).__init__(parent)
    self.unit_per_pixel = 'mm'

    self.project = project
    self.shape = 0, 0

    self.setup_ui()

    self.update()

  def setup_ui(self):
    self.setMinimumSize(200, 200)
    l = QGraphicsGridLayout()

    self.centralWidget.setLayout(l)
    l.setHorizontalSpacing(0)
    l.setVerticalSpacing(0)

    self.vb = MultiRoiViewBox(lockAspect=True, enableMenu=True)
    self.vb.enableAutoRange()

    l.addItem(self.vb, 0, 1)
    self.xScale = pg.AxisItem(orientation='bottom', linkView=self.vb)
    self.xScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>X</span>"
       "<i>Width</i>", units=self.unit_per_pixel)
    l.addItem(self.xScale, 1, 1)

    self.yScale = pg.AxisItem(orientation='left', linkView=self.vb)
    self.yScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>Y</span>"
      "<i>Height</i>", units=self.unit_per_pixel)
    l.addItem(self.yScale, 0, 0)

    self.centralWidget.setLayout(l)
 
  def show(self, frame, min=None, max=None):
    self.shape = frame.shape
    self.vb.showImage(frame, min, max)
    self.update()

  def _update_rect(self):
    self.xScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>X</span>"
       "<i>Width</i>", units=self.unit_per_pixel)
    self.yScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>Y</span>"
      "<i>Height</i>", units=self.unit_per_pixel)
    w, h = self.shape[0], self.shape[1]
    if not (not self.project):
      ox, oy = self.project['origin']
      unit_per_pixel = self.project['unit_per_pixel']

      x = -ox *unit_per_pixel
      y = -oy * unit_per_pixel
      w = w * unit_per_pixel
      h = h * unit_per_pixel

      self.vb.update_rect(x, y, w, h)

  def update(self):
    self._update_rect()
