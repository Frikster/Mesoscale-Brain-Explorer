#!/usr/bin/env python

import numpy as np

class UnknownFileFormatError(Exception):
  pass

def load_raw(fileinfo):
  filename = fileinfo['path']
  dat_type = fileinfo['dtype']
  width = fileinfo['width']
  height = fileinfo['height']
  channel_no = fileinfo['channel']
  
  dat_type = np.dtype(dat_type)

  with open(filename, "rb") as file:
    frames = np.fromfile(file, dtype=dat_type)

  total_number_of_frames = int(np.size(frames) / (width * height * channel_no))
  print("n_frames: " + str(total_number_of_frames))
  frames = np.reshape(frames, (total_number_of_frames, width, height, channel_no))

  #frames = np.reshape(frames, (total_number_of_frames, width, height))
  print("frames.shape PRE:"+str(frames.shape))
  # retrieve only one channel:
  # todo: make user definable
  frames = frames[:, :, :, 1]
  print("frames.shape POST:"+str(frames.shape))

  frames = np.asarray(frames, dtype=dat_type)
  plt.imshow(frames[self.ref_frame_sb.value()])
  return frames

def load_npy(fileinfo):
  frames = np.load(fileinfo['path'])
  frames[np.isnan(frames)] = 0
  return frames

def load_file(fileinfo):
  if fileinfo['path'].endswith('.npy'):
    frames = load_npy(fileinfo)
  elif fileinfo['path'].endswith('.raw'):
    frames = load_raw(fileinfo)
  else:
    raise UnknownFileFormatError()
  return frames

def load_reference_frame_npy(fileinfo, offset):
  frames_mmap = np.load(fileinfo['path'], mmap_mode='c')
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

def load_reference_frame(fileinfo, offset=400):
  if fileinfo['path'].endswith('.npy'):
    frame = load_reference_frame_npy(fileinfo, offset)
  else:
    raise UnknownFileFormatError()
  return frame
