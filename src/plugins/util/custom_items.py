import pyqtgraph as pg
from pyqtgraph.Qt import QtCore,QtGui
from pyqtgraph.exporters.ImageExporter import ImageExporter 
import numpy as np

class QMenuCustom(QtGui.QMenu):
    """ Custum QMenu that closes on leaveEvent """
    def __init__(self,parent=None):
        QtGui.QMenu.__init__(self,parent)

    def leaveEvent(self,ev):
        self.hide()    
        
class QActionCustom(QtGui.QAction):
    """ QAction class modified to emit a single argument (an event)"""
    clickEvent = QtCore.Signal(object)
    def __init__(self,name="",parent=None):
        QtGui.QAction.__init__(self,name,parent)
        self.triggered.connect(self.clicked)
        #self.event = None

    def updateEvent(self,event):
        self.event = event

    def clicked(self):
        self.clickEvent.emit(self.event)       
        
class ImageExporterCustom(ImageExporter):
    """
    Subclass to change preferred image output to bmp. Currently there are some issues 
    with png, as it creates some lines around the image 
    """
    def __init__(self, item):
        ImageExporter.__init__(self,item)
    
    def export(self, fileName=None, toBytes=False, copy=False):
        if fileName is None and not toBytes and not copy:
            filter = ["*."+str(f) for f in QtGui.QImageWriter.supportedImageFormats()]
            preferred = ['*.bmp','*.png', '*.tif', '*.jpg']
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
