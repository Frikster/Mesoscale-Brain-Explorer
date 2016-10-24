#!/usr/bin/env python3

from PyQt4.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
from pdb import set_trace
import sys
import pdb

class SetTrace:
  def __init__(self):
    pyqtRemoveInputHook()
    set_trace()

  def __del__(self):
    pyqtRestoreInputHook()

def set_trace():
    pyqtRemoveInputHook()
    # set up the debugger
    debugger = pdb.Pdb()
    debugger.reset()
    # custom next to get outside of function scope
    debugger.do_next(None) # run the next command
    users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    debugger.interaction(users_frame, None)
