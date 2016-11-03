#!/usr/bin/env python3

import numpy as np
import psutil
import os
import qtutil

class UnknownFileFormatError(Exception):
  pass

def load_npy(filename):
  frames = np.load(filename)
  # frames[np.isnan(frames)] = 0
  return frames

def save_file(path, data):
  if os.path.isfile(path):
    os.remove(path)
  np.save(path, data)

def load_file(filename):
  file_size = os.path.getsize(filename)
  [total, available, percent, used, free] = list(psutil.virtual_memory())

  if file_size > available:
    qtutil.critical('Not enough memory. File is of size '+str(file_size) +
                    ' and available memory is: ' + str(available))
    raise MemoryError('Not enough memory. File is of size '+str(file_size) +
                    ' and available memory is: ' + str(available))

  if percent > 95:
      qtutil.warning('Your memory appears to be getting low.')

  if filename.endswith('.npy'):
    frames = load_npy(filename)
  else:
    raise UnknownFileFormatError()
  return frames

def load_reference_frame_npy(filename, offset):
  frames_mmap = np.load(filename, mmap_mode='c')
  if frames_mmap is None:
    return None
  frame = np.array(frames_mmap[offset])
  frame[np.isnan(frame)] = 0
  frame = frame.swapaxes(0, 1)
  if frame.ndim == 2:
    frame = frame[:, ::-1]
  elif frame.ndim == 3:
    frame = frame[:, ::-1, :]
  return frame

def load_reference_frame(filename, offset=0):
  if filename.endswith('.npy'):
    frame = load_reference_frame_npy(filename, offset)
  else:
    raise UnknownFileFormatError()
  return frame
