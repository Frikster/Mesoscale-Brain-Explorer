#!/usr/bin/env python

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util.mygraphicsview import MyGraphicsView

class Widget(QWidget):
  def __init__(self, parent=None):
    super(Widget, self).__init__(parent)
    self.view = MyGraphicsView()
    self.view.vb.clicked.connect(self.vbc_clicked)
    self.view.vb.hovering.connect(self.vbc_hovering)

  def vbc_clicked(self, x, y):
    if self.origin_mode:
       self.set_origin(x, y)
       return
    y = int(self.sidePanel.vidHeightValue.text())-y
    self.compute_spc_map(x, y)
    if self.spc_map == None:
      return
    y = int(self.sidePanel.vidHeightValue.text())-y

  def vbc_hovering(self, x, y):
    x = x/self.mmpixel
    y = y / self.mmpixel
    #todo: FIX HARDCODED DIMENSIONS!
    if (self.showing_spc == False and self.showing_std == False) or x > 255 or y > 255 or x < 0 or y < 0:
      return
    if (self.showing_spc == True and self.showing_std == True):
      raise ArithmeticError("It should not be possible (yet) to display both maps at once.")

    if self.showing_spc:
      spc_map = self.spc_map.swapaxes(0, 1)
      spc_map = spc_map[:, ::-1]
      if(not math.isnan(spc_map[int(x), int(y)])):
        self.statusBar().showMessage(
          "Correlation/Standard deviation value at crosshair: " +\
          str(spc_map[int(x), int(y)]))
    else:
      std_map = self.st_map.swapaxes(0, 1)
      std_map = std_map[:, ::-1]
      if (not math.isnan(std_map[int(x), int(y)])):
        self.statusBar().showMessage(
          "Correlation/Standard deviation value at crosshair: " +\
          str(std_map[int(x), int(y)])) 

  def init_origin_mode(self):
    self.origin_mode = True
    self.view.vb.setCursor(QtCore.Qt.CrossCursor)
  
  def leave_origin_mode(self):
    self.view.vb.setCursor(QtCore.Qt.ArrowCursor)
    self.origin_mode = False

  def set_origin(self, x, y):
    self.origin = (x, y)
    self.update_rect()
    self.leave_origin_mode()

  def update_rect(self):
    w, h = self.img_shape
    ox, oy = self.origin

    x = -ox * self.mmpixel
    y = -oy * self.mmpixel
    w = w * self.mmpixel
    h = h * self.mmpixel
 
    self.view.vb.update_rect(x, y, w, h)

class MyPlugin:
  def __init__(self):
    self.name = 'Set origin'
    self.widget = Widget()

  def run(self):
    pass
