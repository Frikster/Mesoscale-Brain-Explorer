#!/usr/bin/env python3

from .filter_jeff import filter2_test
from math import pow, sqrt
import os
import numpy as np
from . import fileloader

import matplotlib.pyplot as plt
#import parmap
#import image_registration


class Position:
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.dd = sqrt(pow(dx, 2) + pow(dy, 2))

def find_min_ref(lor):
    curr_min = 100
    for positions in lor:
        sum = 0
        for position in positions:
            sum += position.dd
        if curr_min > sum:
            curr_min = sum
            curr_min_positions = positions
    return curr_min_positions

def chi2shift(frame1, frame2):
  dx, dy, _, _ = image_registration.chi2_shift(frame1, frame2)
  return Position(dx, dy)

def align_videos(filenames, progress_callback):
  """Return filenames of generated videos"""
  progress_callback(0)
  frames = []
  for filename in filenames:
    frame = fileloader.load_reference_frame(filename)
    frame = filter2_test_j(frame)
    frames.append(frame)

  refs = []
  for frame in frames:
    positions = parmap.map(chi2shift, frames, frame)
    refs.append(positions)

  positions = find_min_ref(refs)
  assert(len(filenames) == len(positions))
  ret_filenames = []
  for i, pos in enumerate(positions):
    frames = fileloader.load_file(filenames[i])
    frames = shift_frames(frames, pos, progress_callback)
    path = os.path.join(os.path.dirname(filenames[i]), 'aligned_' +\
      os.path.basename(filenames[i]))
    np.save(path, frames)
    ret_filenames.append(path)
  progress_callback(1)
  return ret_filenames

def shift_frames(frames, positions, progress_callback):
    #print(positions.dx, positions.dy)
    #print(frames.shape)
    for i in range(len(frames)):
        progress_callback(i / float(len(frames)))
        frames[i] = image_registration.fft_tools.shift2d(frames[i], positions.dx, positions.dy)

    return frames