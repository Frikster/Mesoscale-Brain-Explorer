import sys

import numpy as np
import pyqtgraph as pg
import pyqtgraph.console
from PyQt4.QtCore import QSettings, pyqtSignal
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import *
import uuid
import os
import pickle
import qtutil
from itertools import cycle
#todo: DockWindow wishlist
"""1) Save dockwindow as is to file (including state)
2) load dockwindow from file without killing current dockwindow (includes loading saved state)
3) can save stuff in docks dragged and dropped from other plugins (incl. correlation matrix)
4) an "add notes" option"""

class DockWindow(QMainWindow):
    saving_state = pyqtSignal(str)

    def __init__(self, state=None, area=None, title=None, parent=None):
        super(DockWindow, self).__init__(parent)
        if not title:
            title = str(uuid.uuid4())
        self.setWindowTitle(title)
        if area:
            self.area = area
        else:
            self.area = self.setup_docks()
        self.setCentralWidget(self.area)
        if state:
            self.area.restoreState(state)
        self.setup_ui()

    def setup_ui(self):
        menu = self.menuBar()
        m = menu.addMenu('&File')

        a = QAction('&Open state', self)
        a.setShortcut('Ctrl+O')
        a.setStatusTip('Open visualization')
        a.triggered.connect(self.load_state)
        m.addAction(a)

        a = QAction('&Save state', self)
        a.setShortcut('Ctrl+S')
        a.setStatusTip('Save all visualizations')
        a.triggered.connect(self.save_state)
        m.addAction(a)

        menu = self.menuBar()
        m = menu.addMenu('&Tools')
        a = QAction('&Add notes', self)
        a.setShortcut('Ctrl+N')
        a.setStatusTip('Add notes to a dock')
        a.triggered.connect(self.add_notes)
        m.addAction(a)

        menu = self.menuBar()
        m = menu.addMenu('&Help')
        a = QWhatsThis.createAction(QAction('&What\'s This?', self))
        a.setShortcut('Shift+F1')
        a.setStatusTip('Help overlay')
        a.triggered.connect(self.add_notes)
        m.addAction(a)

    def setup_docks(self):
        area = DockArea()
        d1 = Dock("d1", size=(500, 200), closable=True)
        d2 = Dock("d2", size=(500, 200), closable=True)
        d3 = Dock("d3", size=(500, 200), closable=True)
        d4 = Dock("d4", size=(500, 200), closable=True)
        d5 = Dock("d5", size=(500, 200), closable=True)
        d6 = Dock("d6", size=(500, 200), closable=True)
        area.addDock(d1)
        area.addDock(d2, 'bottom', d1)
        area.addDock(d3, 'right', d2)
        area.addDock(d4, 'right', d3)
        area.moveDock(d5, 'right', d1)
        area.moveDock(d6, 'left', d5)
        return area

    def save_state(self):
        save_loc = QtGui.QFileDialog.getSaveFileName(self, 'Save ' + self.windowTitle() + ' Visualizations Window',
                                                     QSettings().value('last_vis_path'),
                                                     'visualization window pickle (*.pkl)')
        if not save_loc:
            return
        self.saving_state.emit(save_loc)
        QSettings().setValue('last_vis_path', os.path.dirname(save_loc))
        self.setWindowTitle(os.path.basename(save_loc))
        state = self.area.saveState()
        with open(save_loc, 'wb') as output:
            pickle.dump(state, output, pickle.HIGHEST_PROTOCOL)
        return save_loc

    def load_state(self):
        filenames = QFileDialog.getOpenFileNames(
          self, 'Load images', QSettings().value('last_vis_path'),
          'visualization window pickle (*.pkl)')
        if not filenames:
            return
        QSettings().setValue('last_vis_path', os.path.dirname(filenames[0]))
        for filename in filenames:
            try:
                with open(filename, 'rb') as input:
                    state = pickle.load(input)
                    new_dw = DockWindow(state, os.path.basename(filename))
                    new_dw.show()
            except:
                qtutil.critical(filename + " failed to open. Aborting.")
                return
        return filenames

    def add_notes(self):
        pass

    def closeEvent(self, event):
        quit_msg = "Do you want to save changes made to " + self.windowTitle() + " before exiting?"
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           quit_msg, QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No,
                                           QtGui.QMessageBox.Cancel)

        if reply == QtGui.QMessageBox.Cancel or reply == QtGui.QMessageBox.Close:
            event.ignore()
            return

        if reply == QtGui.QMessageBox.Yes:
            self.save_state()
            event.accept()
        else:
            event.accept()

    # ## first dock gets save/restore buttons
    # w1 = pg.LayoutWidget()
    # label = QtGui.QLabel(""" -- DockArea Example --
    # This window has 6 Dock widgets in it. Each dock can be dragged
    # by its title bar to occupy a different space within the window
    # but note that one dock has its title bar hidden). Additionally,
    # the borders between docks may be dragged to resize. Docks that are dragged on top
    # of one another are stacked in a tabbed layout. Double-click a dock title
    # bar to place it in its own window.
    # """)
    # saveBtn = QtGui.QPushButton('Save dock state')
    # restoreBtn = QtGui.QPushButton('Restore dock state')
    # restoreBtn.setEnabled(False)
    # w1.addWidget(label, row=0, col=0)
    # w1.addWidget(saveBtn, row=1, col=0)
    # w1.addWidget(restoreBtn, row=2, col=0)
    # d1.addWidget(w1)
    # state = None
    # saveBtn.clicked.connect(save)
    # restoreBtn.clicked.connect(load)
    #
    # w2 = pg.console.ConsoleWidget()
    # d2.addWidget(w2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = DockWindow()
    w.show()
    app.exec_()
    sys.exit()