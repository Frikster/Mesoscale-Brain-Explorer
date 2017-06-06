#!/usr/bin/env python3

import numpy as np
import qtutil
import tifffile as tiff

class RawToNpyConvertError(Exception):
  def error_msg(self):
      qtutil.critical("Convert Error: 'number_of_frames % (length * width * number_of_channels) != 0'\n"
            "The number of total pixels does not divide into an integer number of frames of the expected shape.\n"
            "This could be due to dropped frames")

def tif2npy(filename_from, filename_to, progress_callback):
  progress_callback(0.01)
  with tiff.TiffFile(filename_from) as tif:
    if len(tif[0].shape) == 2 or len(tif[0].shape) == 3:
        if len(tif[0].shape) == 2:
            w, h = tif[0].shape
            shape = len(tif), w, h
            image_j_tiff = False
        else:
            shape = tif[0].shape
            image_j_tiff = True
    else:
        raise ConvertError()
    progress_callback(0.01)
    np.save(filename_to, np.empty(shape, tif[0].dtype))
    fp = np.load(filename_to, mmap_mode='r+')

    if image_j_tiff:
        pages = tif[0].asarray()
        for i, page in enumerate(pages):
            progress_callback(i / float(shape[0] - 1))
            fp[i] = page
    else:
        for i, page in enumerate(tif):
          progress_callback(i / float(shape[0]-1))
          fp[i] = page.asarray()

def raw2npy(filename_from, filename_to, dtype, width, height, num_channels, channel, progress_callback,
            ignore_shape_error=False):
    progress_callback(0.01)
    fp = np.memmap(filename_from, dtype, 'r')
    frame_size = width * height * num_channels
    if not ignore_shape_error:
        if len(fp) % frame_size:
          raise RawToNpyConvertError().error_msg()
    num_frames = int(len(fp) / frame_size)
    fp = np.memmap(filename_from, dtype, 'r',
      shape=(num_frames, width, height, num_channels))
    np.save(filename_to, np.empty((num_frames, int(width), int(height)), dtype))
    fp_to = np.load(filename_to, mmap_mode='r+')
    for i, frame in enumerate(fp):
      progress_callback(i / float(len(fp)-1))
      fp_to[i] = frame[:, :, channel-1]

