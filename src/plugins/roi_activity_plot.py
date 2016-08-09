#!/usr/bin/env python

import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

kelly_colors = dict(
  vivid_yellow = (255, 179, 0),
  strong_purple = (128, 62, 117),
  vivid_red = (193, 0, 32),
  # vivid_orange=(255, 104, 0),
  # very_light_blue=(166, 189, 215),
  # grayish_yellow=(206, 162, 98),
  # medium_gray=(129, 112, 102)
)

# these aren't good for people with defective color vision:
worse_kelly_colors = dict(
  vivid_green = (0, 125, 52),
  strong_purplish_pink = (246, 118, 142),
  strong_blue = (0, 83, 138),
  strong_yellowish_pink = (255, 122, 92),
  strong_violet = (83, 55, 122),
  vivid_orange_yellow = (255, 142, 0),
  strong_purplish_red = (179, 40, 81),
  vivid_greenish_yellow = (244, 200, 0),
  strong_reddish_brown = (127, 24, 13),
  vivid_yellowish_green = (147, 170, 0),
  deep_yellowish_brown = (89, 51, 21),
  vivid_reddish_orange = (241, 58, 19),
  dark_olive_green = (35, 44, 22)
)

class Widget(QWidget):
  def roi_activity_plots(self):
    fileName = str(self.sidePanel.imageFileList.currentItem().text())
    width = int(self.sidePanel.vidWidthValue.text())
    height = int(self.sidePanel.vidHeightValue.text())
    dtype_string = str(self.sidePanel.dtypeValue.text())
    frames = fj.get_frames(fileName, width, height, dtype_string)

    # return plots of average activity over time for ROI's
    if self.view.vb.img == None: return

    self.roi_activity_plots_win = pg.GraphicsWindow(title="Activity across frames")
    self.roi_activity_plots_win.resize(1000, 600)
    self.roi_activity_plots_win.setWindowTitle('Activity across frames')

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    # swap axis for aligned_frames
    frames_swap = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)

    # Collect ROI's
    numROIs = len(self.view.vb.rois)
    arrRegion_masks = {}
    for i in xrange(numROIs):
      roi = self.view.vb.rois[i]
      arrRegion_mask = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
      arrRegion_masks[self.view.vb.rois[i].name] = arrRegion_mask

    roi_plots = {}
    for mask_key in arrRegion_masks.keys():
      mask_size = np.count_nonzero(arrRegion_masks[mask_key])
      roi_frames = (frames * arrRegion_masks[mask_key][np.newaxis, :, :])
      roi_frames_flatten = np.ndarray.sum(np.ndarray.sum(roi_frames, axis = 1), axis = 1)
      roi_plots[mask_key] = roi_frames_flatten/mask_size

      #roi_plots.append(roi_frames_flatten/mask_size)

      # mask_ready = np.repeat(mask, len(roi_frames))
      # roi_frames_masked = np.ma.array(roi_frames, mask=mask_ready)
      # #mask_bool = mask.astype(bool)
      # #mask[mask == 0] = False
      # #mask[mask == 1] = True
      # a = np.ma.mean(roi_frames, mask = mask_bool)
      # a.mean()
      # roi_plots.append(np.average(np.average(roi_frames, axis=1), axis=1))

    self.view.vb.rois[i]
    plot = self.roi_activity_plots_win.addPlot(title="Activity across frames")
    plot.addLegend()

    usable_kelly_colors = self.kelly_colors.keys()
    usable_bad_kelly_colours = self.worse_kelly_colors.keys()
    for plot_pts_key in roi_plots.keys():
      if len(usable_kelly_colors) == 0 and len(usable_bad_kelly_colours) == 0:
        raise LookupError("Ran out of colours!")

      if len(usable_kelly_colors) > 0:
         col_name = random.choice(usable_kelly_colors)
         usable_kelly_colors.remove(col_name)
         col = self.kelly_colors[col_name]
      else:
        col_name = random.choice(usable_bad_kelly_colours)
        usable_bad_kelly_colours.remove(col_name)
        col = self.worse_kelly_colors[col_name]

      plot.plot(roi_plots[plot_pts_key], pen=col, name=plot_pts_key)

    # p2 = self.roi_activity_plots_win.addPlot(title="Multiple curves")
    # p2.plot(np.random.normal(size=100), pen=(255, 0, 0), name="Red curve")
    # p2.plot(np.random.normal(size=110) + 5, pen=(0, 255, 0), name="Blue curve")
    # p2.plot(np.random.normal(size=120) + 10, pen=(0, 0, 255), name="Green curve")

class MyPlugin:
  def __init__(self, project):
    self.name = 'ROI activity plot'
    self.widget = QWidget()
  
  def run(self):
    pass
