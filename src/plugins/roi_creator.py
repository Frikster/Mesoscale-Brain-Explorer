# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Widget(QWidget):
  pass

class MyPlugin:
  def __init__(self):
    self.name = 'Create ROIs'
    self.widget = QWidget()
  
  def run(self):
    pass
