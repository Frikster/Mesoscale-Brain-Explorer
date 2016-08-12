#!/usr/bin/env python

import numpy as np

def load_npy(filename):
  frames = np.load(filename)
  frames[np.isnan(frames)] = 0
  return frames

def load_file(filename):
  if filename.endswith('.npy'):
    frames = load_npy(filename)
  else:
    frames = None
  return frames

def load_reference_frame(filename, offset=400):
  frames = load_file(filename)
  if frames is None:
    return None
  frame = frames[min(offset, len(frames)-1)]
  frame = frame.swapaxes(0,1)
  if frame.ndim==2:
    frame = frame[:,::-1]
  elif frame.ndim==3:
    frame = frame[:,::-1,:]
  return frame

