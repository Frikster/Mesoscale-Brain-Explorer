from pyqtgraph.Qt import QtCore, QtGui, USE_PYSIDE
import pyqtgraph.graphicsItems.ROI as pgROI
import pyqtgraph.functions as fn
from pyqtgraph.Point import Point
from .custom_items import QMenuCustom
import numpy as np
import matplotlib.pylab as plt
import uuid

__all__ = ['ROI', 'Handle','PolylineSegment','RectROIcustom','PolyLineROIcustom']

class Handle(pgROI.Handle):
    """ Sub-class of pyqtgraph ROI handle. Main purpose is to deactivate the hoverEvent,
        mouseClickEvent and mouseDragEvent when the associated ROI is not active. This is
        required to allow ROIs to be drawn over the top of each other """

    def __init__(self, radius, typ=None, pen=(200, 200, 220), parent=None, deletable=False):
        pgROI.Handle.__init__(self,radius, typ, pen, parent, deletable)
        self.setSelectable(True)
        
    def setSelectable(self,isActive):
        self.isActive = isActive

    def raiseContextMenu(self, ev):
        menu = self.getMenu()

        ## Make sure it is still ok to remove this handle
        removeAllowed = all([r.checkRemoveHandle(self) for r in self.rois])
        self.removeAction.setEnabled(removeAllowed)
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y())) 
        
    def hoverEvent(self, ev):
        # Ignore events if handle is not active
        if not self.isActive: return 
        hover = False
        if not ev.isExit():
            if ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True
        if hover:
            self.currentPen = fn.mkPen(255, 255,0)
        else:
            self.currentPen = self.pen
        self.update()  
        
    def mouseClickEvent(self, ev):
        # Ignore events if handle is not active
        if not self.isActive: 
            ev.ignore()
            return
               
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.isMoving = False
            self.movePoint(self.startPos, finish=True)
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            if ev.button() == QtCore.Qt.RightButton and self.deletable:
                self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore() 

    def mouseDragEvent(self, ev):
        # Ignore events if handle is not active
        if not self.isActive: return
        
        if ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
            
        if ev.isFinish():
            if self.isMoving:
                for r in self.rois:
                    r.stateChangeFinished()
            self.isMoving = False
        elif ev.isStart():
            for r in self.rois:
                r.handleMoveStarted()
            self.isMoving = True
            self.startPos = self.scenePos()
            self.cursorOffset = self.scenePos() - ev.buttonDownScenePos()
            
        if self.isMoving:
            pos = ev.scenePos() + self.cursorOffset
            self.movePoint(pos, ev.modifiers(), finish=False)   
            
class ROI(pgROI.ROI):
    """ Sub-class of pyqtgraph ROI class. Main purpose is to customise the ROI handles """
    
    def __init__(self,pos,size=Point(1, 1),angle=0.0,invertible=False,maxBounds=None,snapSize=1.0,scaleSnap=False,
                 translateSnap=False,rotateSnap=False,parent=None,pen=None,movable=True,removable=False):
        pgROI.ROI.__init__(self,pos,size,angle,invertible,maxBounds,snapSize,scaleSnap,translateSnap,rotateSnap,parent,pen,movable,removable)
      
    def addHandle(self, info, index=None):
        
        ## If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = Handle(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
            
        ## Connect the handle to this ROI
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        
        h.setZValue(self.zValue()+1)
        self.stateChanged()
        return h   
        
    def paint(self, p, opt, widget):
        p.save()
        r = self.boundingRect()
        #p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.translate(r.left(), r.top())
        p.scale(r.width(), r.height())
        p.drawRect(0, 0, 1, 1)
        p.restore()        
        
class PolylineSegment(pgROI.LineSegmentROI):
    """ Sub-class of pyqtgraph LineSegmentROI class. Main purpose is to deactivate functions if not active """
    
    def __init__(self, positions=(None, None), pos=None, handles=(None,None), **args):
        pgROI.LineSegmentROI.__init__(self, positions, pos, handles, **args)
 
        self.penHover     = fn.mkPen(255, 255, 0)        
        self.translatable = False            
        self.setSelectable(True)
        self.setAcceptsHandles(True)

    def setSelectable(self,isActive):
        self.isActive = isActive
        if isActive:
            self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        else:
            self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

    def setAcceptsHandles(self, acceptsHandles):
        self.acceptsHandles = acceptsHandles
        if acceptsHandles:
            self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        else:         
            self.setAcceptedMouseButtons(QtCore.Qt.NoButton)  

    def hoverEvent(self, ev):
        if not self.isActive: return
        if (self.translatable or self.acceptsHandles) and (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
        else:
            self.setMouseHover(False)
            
    def setMouseHover(self, hover):
        ## Inform the ROI that the mouse is(not) hovering over it
        #if self.mouseHovering == hover:
        #    return
        #self.mouseHovering = hover
        if hover:
            self.currentPen = self.penHover
        else:
            self.currentPen = self.pen
        self.update()            
            
    def paint(self, p, *args):
        #p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(self.currentPen)
        h1 = self.handles[0]['item'].pos()
        h2 = self.handles[1]['item'].pos()
        p.drawLine(h1, h2)            
            
class selectableROI(object):
    """ A ROI class that can be used with a multiRoiViewbox """

    sigRemoveRequested = QtCore.Signal(object)
    sigCopyRequested   = QtCore.Signal(object)
    sigSaveRequested   = QtCore.Signal(object)  

    def __init__(self):
        self.penActive   = fn.mkPen( 0, 255, 0)
        self.penInactive = fn.mkPen(255,   0, 0) 
        self.penHover    = fn.mkPen(255, 255, 0)   
        self.penActive.setWidth(1)
        self.penInactive.setWidth(1) 
        self.penHover.setWidth(1)   
        self.setName(str(uuid.uuid4()))
        self.isSelected = False
        self.menu = None
        self.setActive(True)

    def set_color(self, r, g, b):
      self.penActive.setColor(QtGui.QColor(r, g, b))

    def setActive(self,isActive):
        self.isActive = isActive
        if isActive:
            self.setAcceptedMouseButtons(QtCore.Qt.LeftButton or QtCore.Qt.RightButton)
        else:       
            self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

    def __lt__(self,other):
        selfid  = int(self.name.split('-')[-1])
        otherid = int(other.name.split('-')[-1])
        return selfid < otherid
        
    def setName(self, name):
        if name is not None:
            self.name = name
        else:
            raise ValueError('No ROI name')

    def removeClicked(self):
        self.sigRemoveRequested.emit(self) 
        
    def copyClicked(self):
        self.sigCopyRequested.emit(self) 
        
    def saveClicked(self):
        self.sigSaveRequested.emit(self)  
        
    def hoverEvent(self, ev):
        hover = False
        if not ev.isExit():
            if self.translatable and ev.acceptDrags(QtCore.Qt.LeftButton):
                hover=True
            for btn in [QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MidButton]:
                if int(self.acceptedMouseButtons() & btn) > 0 and ev.acceptClicks(btn):
                    hover=True                
            if self.contextMenuEnabled():
                ev.acceptClicks(QtCore.Qt.RightButton)
        
        if hover:
            self.setMouseHover(True)
            self.sigHoverEvent.emit(self)
            ev.acceptClicks(QtCore.Qt.RightButton)
        else:
            self.setMouseHover(False)         
        
    def mouseDragEvent(self, ev):
        if ev.isStart():  
            # Drag using left button only if selected  
            if ev.button() == QtCore.Qt.LeftButton:
                if self.translatable:
                    self.isMoving = True
                    self.preMoveState = self.getState()
                    self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    self.sigRegionChangeStarted.emit(self)
                    ev.accept()
                else:
                    ev.ignore()
        elif ev.isFinish():
            if self.translatable:
                if self.isMoving:
                    self.stateChangeFinished()
                self.isMoving = False
            return
        if self.translatable and self.isMoving and ev.buttons() == QtCore.Qt.LeftButton:
            snap = True if (ev.modifiers() & QtCore.Qt.ControlModifier) else None
            newPos = self.mapToParent(ev.pos()) + self.cursorOffset
            self.translate(newPos - self.pos(), snap=snap, finish=False)
      
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()
        elif ev.button() == QtCore.Qt.RightButton and self.contextMenuEnabled():
            self.raiseContextMenu(ev)
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()
    
    def contextMenuEnabled(self):
        return (self.removable and self.isActive)
    
    def raiseContextMenu(self, ev):
        if not self.contextMenuEnabled():
            return
        menu = self.getMenu()
        pos  = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def getMenu(self):
        # Setup menu
        if self.menu is None:
            self.menu         = QMenuCustom()
            self.menuTitle    = QtGui.QAction(self.name,self.menu)
            self.copyAct      = QtGui.QAction("Copy", self.menu)
            self.saveAct      = QtGui.QAction("Save", self.menu)
            self.remAct       = QtGui.QAction("Remove", self.menu)            
            self.menu.actions = [self.menuTitle,self.copyAct,self.saveAct,self.remAct]
            # Connect signals to actions
            self.copyAct.triggered.connect(self.copyClicked)
            self.remAct.triggered.connect(self.removeClicked)
            self.saveAct.triggered.connect(self.saveClicked)
            # Add actions to menu
            self.menu.addAction(self.menuTitle)
            self.menu.addSeparator()
            for action in self.menu.actions[1:]:
                self.menu.addAction(action)
            # Set default properties
            self.menuTitle.setDisabled(True)
            self.menu.setStyleSheet("QMenu::item {color: black; font-weight:normal;}")
            font = QtGui.QFont()
            font.setBold(True)
            self.menuTitle.setFont(font)
        # Enable menus only for selected roi
        if self.isSelected:
            self.copyAct.setVisible(True) 
            self.saveAct.setVisible(True)
            self.remAct.setVisible(True)
        else:               
            self.copyAct.setVisible(False)
            self.saveAct.setVisible(False)
            self.remAct.setVisible(False)  
        return self.menu


class PolyLineROIcustom(selectableROI,ROI):
#class PolyLineROIcustom(selectableROI):
    
    sigRemoveRequested = QtCore.Signal(object)
    sigCopyRequested   = QtCore.Signal(object)
    sigSaveRequested   = QtCore.Signal(object)    
    
    def __init__(self, pos=[0,0], handlePositions=None, **args):        
        ROI.__init__(self, pos, size=[1,1], **args)
        selectableROI.__init__(self)
                
        self.segments = []
        self.translatable = False
        self.closed = True
        self.pen = self.penActive
        self.handlePen = self.penActive        
        self.createROI(handlePositions)
        self.setActive(False)     
 
    def createROI(self,handlePositions):
        # Create ROI from handle positions. Used mainly for copy and save
        if handlePositions is None: return
        for hp in handlePositions:
            self.addFreeHandle(hp)
        for i in range(-1, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item'])        

    def addSegment(self, h1, h2, index=None):
        seg = PolylineSegment(handles=(h1, h2), pen=self.pen, parent=self, movable=False)
        if index is None:
            self.segments.append(seg)
        else:
            self.segments.insert(index, seg)
        seg.sigClicked.connect(self.segmentClicked)
        seg.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        seg.setZValue(self.zValue()+1)
        for h in seg.handles:
            h['item'].setDeletable(True)
            h['item'].setAcceptedMouseButtons(h['item'].acceptedMouseButtons() | QtCore.Qt.LeftButton) ## have these handles take left clicks too, so that handles cannot be added on top of other handles   
    
    def setMouseHover(self, hover):
        #self.counter += 1
        #print 'setMouseHover ', self.counter, " ", hover
        ROI.setMouseHover(self, hover)
        for s in self.segments:
            s.setMouseHover(hover)
        #    print s
        self.update()
                          
    def addHandle(self, info, index=None):
        h = ROI.addHandle(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)
        return h
        
    def segmentClicked(self, segment, ev=None, pos=None): ## pos should be in this item's coordinate system
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        h2 = segment.handles[1]['item']
        
        i = self.segments.index(segment)
        h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
        self.addSegment(h3, h2, index=i+1)
        segment.replaceHandle(h2, h3)
        
    def removeHandle(self, handle, updateSegments=True):
        ROI.removeHandle(self, handle)
        handle.sigRemoveRequested.disconnect(self.removeHandle)
        
        if not updateSegments:
            return
        segments = handle.rois[:]
        
        if len(segments) == 1:
            self.removeSegment(segments[0])
        else:
            handles = [h['item'] for h in segments[1].handles]
            handles.remove(handle)
            segments[0].replaceHandle(handle, handles[0])
            self.removeSegment(segments[1])
        
    def removeSegment(self, seg):
        for handle in seg.handles[:]:
            seg.removeHandle(handle['item'])
        self.segments.remove(seg)
        seg.sigClicked.disconnect(self.segmentClicked)
        self.scene().removeItem(seg)
        
    def checkRemoveHandle(self, h):
        if self.closed:
            return len(self.handles) > 3
        else:
            return len(self.handles) > 2
        
    def paint(self, p, *args):
        pass
    
    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        p = QtGui.QPainterPath()
        p.moveTo(self.handles[0]['item'].pos())
        for i in range(len(self.handles)):
            p.lineTo(self.handles[i]['item'].pos())
        p.lineTo(self.handles[0]['item'].pos())
        return p  
               
    def setSelected(self, s):
        QtGui.QGraphicsItem.setSelected(self, s)
        if s:
            self.isSelected   = True
            self.translatable = True         
            for seg in self.segments:
                seg.setPen(self.penActive)
                seg.setSelectable(True)
                seg.setAcceptsHandles(True)
                seg.update()
            for h in self.handles:
                h['item'].currentPen = self.penActive 
                h['item'].pen = h['item'].currentPen             
                h['item'].show()
                h['item'].update()
        else:
            self.isSelected   = False
            self.translatable = False         
            for seg in self.segments:
                seg.setPen(self.penInactive)
                seg.setSelectable(False)
                seg.setAcceptsHandles(False)
                seg.update()            
            for h in self.handles:             
                h['item'].currentPen = self.penInactive 
                h['item'].pen = h['item'].currentPen               
                h['item'].hide()
                h['item'].update()
            
    def getArrayRegion(self, data, img, axes=(0,1), returnMappedCoords=False, **kwds):
        sl = self.getArraySlice(data, img, axes=(0, 1))
        if sl is None:
            return None
        sliced = data[sl[0]]
        im = QtGui.QImage(sliced.shape[axes[0]], sliced.shape[axes[1]], QtGui.QImage.Format_ARGB32)
        im.fill(0x0)
        p = QtGui.QPainter(im)
        p.setPen(fn.mkPen(None))
        p.setBrush(fn.mkBrush('w'))
        p.setTransform(self.itemTransform(img)[0])
        bounds = self.mapRectToItem(img, self.boundingRect())
        p.translate(-bounds.left(), -bounds.top()) 
        p.drawPath(self.shape())
        p.end()
        mask = imageToArray(im)[:,:,0].astype(float) / 255.
        # Old code that doesn't seem to do what it should
        #shape = [1] * data.ndim
        #shape[axes[0]] = sliced.shape[axes[0]]
        #shape[axes[1]] = sliced.shape[axes[1]]
        #return sliced * mask.reshape(shape)

        # Return image with mask applied
        reshaped_mask = mask.T[:, :, np.newaxis]
        return sliced * reshaped_mask

    def getROIMask(self, data, img, axes=(0,1), returnMappedCoords=False, **kwds):
        #sl = self.getArraySlice(data, img, axes=(0, 1))
        #if sl is None:
        #    return None
        #sliced = data[sl[0]]
        sliced = data
        im = QtGui.QImage(sliced.shape[axes[0]], sliced.shape[axes[1]], QtGui.QImage.Format_ARGB32)
        im.fill(0x0)
        p = QtGui.QPainter(im)
        p.setPen(fn.mkPen(None))
        p.setBrush(fn.mkBrush('w'))
        p.setTransform(self.itemTransform(img)[0])
        # No moving
        # bounds = self.mapRectToItem(img, self.boundingRect())
        # p.translate(-bounds.left(), -bounds.top())
        p.drawPath(self.shape())
        p.end()
        mask = imageToArray(im)[:,:,0].astype(float) / 255.
        # Old code that doesn't seem to do what it should
        #shape = [1] * data.ndim
        #shape[axes[0]] = sliced.shape[axes[0]]
        #shape[axes[1]] = sliced.shape[axes[1]]
        #return sliced * mask.reshape(shape)

        # Return image with mask applied
        #reshaped_mask = mask.T[:, :, np.newaxis]
        return np.flipud(mask)

    # def getROISlice(self, data, img, axes=(0,1), returnMappedCoords=False, **kwds):
    #     sl = self.getArraySlice(data, img, axes=(0, 1))
    #     if sl is None:
    #         return None
    #     sliced = data[sl[0]]
    #     im = QtGui.QImage(sliced.shape[axes[0]], sliced.shape[axes[1]], QtGui.QImage.Format_ARGB32)
    #     im.fill(0x0)
    #     p = QtGui.QPainter(im)
    #     p.setPen(fn.mkPen(None))
    #     p.setBrush(fn.mkBrush('w'))
    #     p.setTransform(self.itemTransform(img)[0])
    #     bounds = self.mapRectToItem(img, self.boundingRect())
    #     p.translate(-bounds.left(), -bounds.top())
    #     p.drawPath(self.shape())
    #     p.end()
    #     mask = imageToArray(im)[:,:,0].astype(float) / 255.
    #     # Old code that doesn't seem to do what it should
    #     #shape = [1] * data.ndim
    #     #shape[axes[0]] = sliced.shape[axes[0]]
    #     #shape[axes[1]] = sliced.shape[axes[1]]
    #     #return sliced * mask.reshape(shape)
    #
    #     return sliced

def imageToArray(img):
    """
    Replaces imageToArray in pyqtgraph functions.py. Due to errors in Python 2.6
    Error appears to be due to numpy and converting ptr to arr. Early versions create
    an array of empty strings and later versions create an array of the wrong size.
    The following method works, although arr in read-only i.e. changing the values in 
    the arr will not change the pixel values in the original QImage. 
    """
    fmt = img.format()
    ptr = img.bits()
    if USE_PYSIDE:
        arr = np.frombuffer(ptr, dtype=np.ubyte)
    else:   
        ptr.setsize(img.byteCount())
        buf = buffer(ptr, 0, img.byteCount())
        arr = np.frombuffer(buf, dtype=np.ubyte)  
    if fmt == img.Format_RGB32:
        arr = arr.reshape(img.height(), img.width(), 3)
    elif fmt == img.Format_ARGB32 or fmt == img.Format_ARGB32_Premultiplied:
        arr = arr.reshape(img.height(), img.width(), 4)
    return arr      
     
class RectROIcustom(selectableROI,ROI): 
    
    sigRemoveRequested = QtCore.Signal(object)
    sigCopyRequested   = QtCore.Signal(object)
    sigSaveRequested   = QtCore.Signal(object)    
    
    def __init__(self, pos, size, angle, **args):
        ROI.__init__(self, pos, size, angle, **args)
        selectableROI.__init__(self)     
        self.addScaleHandle([0.0, 0.5], [1.0, 0.5])
        self.addScaleHandle([1.0, 0.5], [0.0, 0.5])  
        self.addScaleHandle([0.5, 0.0], [0.5, 1.0])
        self.addScaleHandle([0.5, 1.0], [0.5, 0.0]) 
        self.addRotateHandle([0.0,0.0], [1.0, 1.0])
        self.addRotateHandle([0.0,1.0], [1.0, 0.0]) 
        self.addRotateHandle([1.0,0.0], [0.0, 1.0])
        self.addRotateHandle([1.0,1.0], [0.0, 0.0]) 
 
    def setSelected(self, s):
        QtGui.QGraphicsItem.setSelected(self, s)
        if s:
            self.isSelected   = True
            self.translatable = True
            self.setPen(self.penActive)
            for h in self.handles:
                h['item'].currentPen = self.penActive 
                h['item'].pen = h['item'].currentPen             
                h['item'].show()
                h['item'].update()
        else:
            self.isSelected   = False
            self.translatable = False
            self.setPen(self.penInactive)      
            for h in self.handles:
                h['item'].currentPen = self.penInactive 
                h['item'].pen = h['item'].currentPen               
                h['item'].hide()
                h['item'].update()             
                
           
