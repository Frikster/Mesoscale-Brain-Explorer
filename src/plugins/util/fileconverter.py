#!/usr/bin/env python3

import numpy as np

import tifffile as tiff

class ConvertError(Exception):
  pass

def tif2npy(filename_from, filename_to, progress_callback):
  progress_callback(0.01)
  with tiff.TiffFile(filename_from) as tif:
    w, h = tif[0].shape
    shape = len(tif), w, h
    progress_callback(0.01)
    np.save(filename_to, np.empty(shape, tif[0].dtype))
    fp = np.load(filename_to, mmap_mode='r+')
    for i, page in enumerate(tif):
      progress_callback(i / float(shape[0]-1))
      fp[i] = page.asarray()

def raw2npy(filename_from, filename_to, dtype, width, height,
  num_channels, channel, progress_callback):
    progress_callback(0.01)
    fp = np.memmap(filename_from, dtype, 'r')
    frame_size = width * height * num_channels
    if len(fp) % frame_size:
      raise ConvertError()
    num_frames = len(fp) / frame_size
    fp = np.memmap(filename_from, dtype, 'r',
      shape=(num_frames, width, height, num_channels))
    np.save(filename_to, np.empty((num_frames, width, height), dtype))
    fp_to = np.load(filename_to, mmap_mode='r+')
    for i, frame in enumerate(fp):
      progress_callback(i / float(len(fp)-1))
      fp_to[i] = frame[:, :, channel-1]

