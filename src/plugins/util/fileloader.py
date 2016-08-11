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

def load_mmap(filename, mode):
  if filename.endswith('.npy'):
    frames_mmap = np.load(filename, mmap_mode=mode)
  else:
    frames_mmap = None
  return frames_mmap

def load_reference_frame(filename, offset=400):
  frames_mmap = load_mmap(filename, 'c')
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

