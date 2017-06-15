#!/usr/bin/env python3

import os

import numpy as np
import psutil
import qtutil

from PyQt4.QtGui import QMessageBox


class UnknownFileFormatError(Exception):
  pass

def load_npy(filename, progress_callback=None, segment=None):
  if segment:
      frames_mmap = np.load(filename, mmap_mode='r')
      frames_mmap = frames_mmap[segment[0]:segment[1]]
      frames = np.empty((frames_mmap.shape[0], frames_mmap.shape[1], frames_mmap.shape[2]),
                        dtype=frames_mmap.dtype)
      for frame_no, frame_mmap in enumerate(frames_mmap):
          frames[frame_no] = frame_mmap
          if progress_callback:
              progress_callback(frame_no / (len(frames_mmap)))
  else:
      if not progress_callback:
          frames = np.load(filename)
          return frames
      else:
          frames_mmap = np.load(filename, mmap_mode='r')
          frames = np.zeros(frames_mmap.shape, dtype=frames_mmap.dtype)
          for i, mmap_frame in enumerate(frames_mmap):
              frames[i] = mmap_frame
              progress_callback(i/(len(frames_mmap)))
          # frames[np.isnan(frames)] = 0
  return frames

def get_name_after_no_overwrite(name_before, manip, project):
    """check if a file with same name already exists and *don't* overwrite if it does"""
    name_after = str(name_before + '_' + manip + '.')
    name_after_copy = str(name_before + '_' + manip + '(')
    file_after = [files for files in project.files if name_after in files['path'] or name_after_copy in files['name']]

    if len(file_after) > 0:
        name_after = str(name_before + '_' + manip) + '(' + str(len(file_after)) + ')'
    else:
        name_after = str(name_before + '_' + manip)

    return name_after

def save_file(path, data):
    file_size = data.nbytes
    available = list(psutil.virtual_memory())[1]
    percent = list(psutil.virtual_memory())[2]
    # [total, available, percent, used, free, active, inactive, buffers, cached, shared] = list(psutil.virtual_memory())

    if file_size > available:
        qtutil.critical('Memory warning. File is of size ' + str(file_size) +
                        ' and available memory is: ' + str(available))
        # del_msg = path + " might not be saved due to insufficient memory. " \
        #                  "If you attempt to save it, it may cause system instability. If you do abort then this file" \
        #                  "will be lost. Note that only this one file will be lost. Proceed?"
        # reply = QMessageBox.question(widget, 'File Save Error',
        #                              del_msg, QMessageBox.Yes, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     raise MemoryError('Not enough memory. File is of size ' + str(file_size) +
        #                       ' and available memory is: ' + str(available))

    if percent > 95:
        qtutil.warning('Your memory appears to be getting low.')
    # total, used, free = psutil.disk_usage(os.path.dirname(path))
    # if data.nbytes > free:
    #     qtutil.critical('Not enough space on drive. File is of size ' + str(data.nbytes) +
    #                     ' and available space is: ' + str(free))
    #     raise IOError('Not enough space on drive. File is of size ' + str(data.nbytes) +
    #                     ' and available space is: ' + str(free))
    if os.path.isfile(path):
        os.remove(path)
    try:
        # if data.dtype == 'float64':
        #     qtutil.critical("FLOAT64")
        #     raise MemoryError("FLOAT64")
        np.save(path, data)
    except:
        qtutil.critical('Could not save ' + path +
                            '. This is likely due to running out of space on the drive')

def load_file(filename, progress_callback=None, segment=None):
  file_size = os.path.getsize(filename)
  available = list(psutil.virtual_memory())[1]
  percent = list(psutil.virtual_memory())[2]
  # [total, available, percent, used, free, active, inactive, buffers, cached, shared] = list(psutil.virtual_memory())

  if file_size > available:
    qtutil.critical('Not enough memory. File is of size '+str(file_size) +
                    ' and available memory is: ' + str(available))
    raise MemoryError('Not enough memory. File is of size '+str(file_size) +
                    ' and available memory is: ' + str(available))

  if percent > 95:
      qtutil.warning('Your memory appears to be getting low.')

  if filename.endswith('.npy'):
    frames = load_npy(filename, progress_callback, segment)
    # if frames.dtype == 'float64':
    #     qtutil.critical("FLOAT64")
    #     raise MemoryError("FLOAT64")
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
