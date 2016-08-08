#!/usr/bin/env python

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pyqtgraph as pg

from viewboxcustom import MultiRoiViewBox

class MyGraphicsView(pg.GraphicsView):
  def __init__(self, parent=None):
    super(MyGraphicsView, self).__init__(parent)

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
       "<i>Width</i>",units="mm")
    l.addItem(self.xScale, 1, 1)

    self.yScale = pg.AxisItem(orientation='left', linkView=self.vb)
    self.yScale.setLabel(text="<span style='color: #ff0000; font-weight: bold'>Y</span>"
      "<i>Height</i>", units='mm')
    l.addItem(self.yScale, 0, 0)
 
