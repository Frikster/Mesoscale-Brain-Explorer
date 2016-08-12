# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os, sys
import numpy as np

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from util import filter_jeff as fj
from util import fileloader

class Widget(QWidget):
    def crop_ROI(self):
        #todo: complete changing this into the cropping function
        """ Get change in BMD over time (e.g. for each image) for all ROIs. 
            
            Revised function that converts the list of images into a 3D array
            and then uses the relative position of the ROIs to the current
            image, self.view.vb.img, to get the average BMD value e.g. it doesn't use
            setImage to change the image in the view. This requires that all
            images are the same size and in the same position.
        """
        fileName = str(self.sidePanel.imageFileList.currentItem().text())
        width = int(self.sidePanel.vidWidthValue.text())
        height = int(self.sidePanel.vidHeightValue.text())
        dtype_string = str(self.sidePanel.dtypeValue.text())
        # Return if there is nod image or rois in view
        if self.view.vb.img == None or len(self.view.vb.rois) == 0:
            print("there is nod image or rois in view ")
            return

        # swap axis for aligned_frames
        frames = fj.get_frames(fileName, width, height, dtype_string)
        frames_swap = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)
        # Collect ROI's and combine
        numROIs = len(self.view.vb.rois)
        arrRegion_masks = []
        for i in xrange(numROIs):
            roi = self.view.vb.rois[i]
            arrRegion_mask   = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
            arrRegion_masks.append(arrRegion_mask)

        combined_mask = np.sum(arrRegion_masks, axis=0)
        # Make all rows with all zeros na
        combined_mask[(combined_mask == 0)] = None
        self.mask = combined_mask
        #TODO!!!
        # #combined_mask.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"mask.raw")
        #print("mask saved to " + os.path.expanduser('/Downloads/')+"mask.raw")

        # In imageJ - Gap Between Images The number of bytes from the end of one image to the beginning of the next.
        # Set this value to width × height × bytes-per-pixel × n to skip n images for each image read. So use 4194304
        # Dont forget to set Endian value and set to 64 bit
        #todo: clean up your dirty long code.videoFiles[str(self.sidePanel.imageFileList.currentItem().text())] turns up everywhere
        roi_frames = (frames * combined_mask[np.newaxis, :, :])

        np.save(os.path.expanduser('/Downloads/')+"ROI", roi_frames)
        #roi_frames.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"ROI.raw")
        #print("ROI saved to " + os.path.expanduser('/Downloads/')+"ROI")

class MyPlugin:
  def __init__(self, project):
    self.name = 'Crop ROIs'
    self.widget = QWidget()
  
  def run(self):
    pass
