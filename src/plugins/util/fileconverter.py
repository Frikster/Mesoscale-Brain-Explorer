#!/usr/bin/env python

import os
import numpy as np

import tifffile as tiff

def tif2npy(filename_from, filename_to, progress_callback):
  assert(not os.path.isfile(filename_to))
  with tiff.TiffFile(filename_from) as tif:
    w, h = tif[0].shape
    shape = len(tif), w, h
    np.save(filename_to, np.empty(shape, tif[0].dtype))
    fp = np.load(filename_to, mmap_mode='r+')
    for i, page in enumerate(tif):
      progress_callback(int(100.0 * i / float(shape[0]-1)))
      fp[i] = page.asarray()
