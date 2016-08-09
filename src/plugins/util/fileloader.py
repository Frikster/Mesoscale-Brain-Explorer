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
