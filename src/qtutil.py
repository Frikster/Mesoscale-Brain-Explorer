from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

def critical(msg, parent=None):
  msgbox = QMessageBox(parent)
  msgbox.setText(msg)
  msgbox.setIcon(QMessageBox.Critical)
  msgbox.exec_()

def warning(msg, parent=None):
  msgbox = QMessageBox(parent)
  msgbox.setText(msg)
  msgbox.setIcon(QMessageBox.Warning)
  msgbox.exec_()

def info(msg, parent=None):
  msgbox = QMessageBox(parent)
  msgbox.setText(msg)
  msgbox.setIcon(QMessageBox.Information)
  msgbox.exec_()

def separator():
  toto = QFrame()
  toto.setFrameShape(QFrame.HLine)
  toto.setFrameShadow(QFrame.Sunken)
  return toto

class MyToolBar(QToolBar):
  def __init__(self, parent=None):
    super(MyToolBar, self).__init__(parent)
    self.setMovable(False)

  def add_action(self, data, pic, label, parent, func=None, shortcut=None, checkable=False, checked=False):
    a = QAction(QIcon('pics/'+pic), label, parent)

    a.setData(data)

    if shortcut:
      a.setShortcut(shortcut)

    if checkable:
      a.setCheckable(True)
      a.setChecked(checked)

    if func:
      a.triggered.connect(func)

    self.addAction(a)

  def add_group(self, parent, func=None):
    ag = QActionGroup(parent)

    if func:
      ag.triggered[QAction].connect(func)

    return ag

  def add_stretch(self):
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.addWidget(w)
