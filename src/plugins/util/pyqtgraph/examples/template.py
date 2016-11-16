# -*- coding: utf-8 -*-
"""

Description of example


"""

from pyqtgraph.Qt import QtCore, QtGui

# win.setWindowTitle('pyqtgraph example: ____')

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
