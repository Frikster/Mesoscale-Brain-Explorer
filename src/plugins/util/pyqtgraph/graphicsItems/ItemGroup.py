from .GraphicsObject import GraphicsObject
from ..Qt import QtCore

__all__ = ['ItemGroup']
class ItemGroup(GraphicsObject):
    """
    Replacement for QGraphicsItemGroup
    """
    
    def __init__(self, *args):
        GraphicsObject.__init__(self, *args)
        if hasattr(self, "ItemHasNoContents"):
            self.setFlag(self.ItemHasNoContents)
    
    def boundingRect(self):
        return QtCore.QRectF()
        
    def paint(self, *args):
        pass
    
    def addItem(self, item):
        item.setParentItem(self)

