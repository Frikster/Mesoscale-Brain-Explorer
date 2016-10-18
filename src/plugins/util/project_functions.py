#!/usr/bin/env python3

import os
import numpy as np
from PyQt4.QtGui import *
from PyQt4.QtCore import *

def save_project(video_path, project, frames, manip, file_type):
    name_before, ext = os.path.splitext(os.path.basename(video_path))
    file_before = [files for files in project.files if files['name'] == name_before]
    assert(len(file_before) == 1)
    file_before = file_before[0]

    name_after = str(name_before + '_' + manip)
    path = str(os.path.join(project.path, name_after) + '.npy')
    np.save(path, frames)
    project.files.append({
        'path': path,
        'type': file_type,
        'source_video': video_path,
        'manipulations': str(file_before['manipulations'] + [manip]),
        'name': name_after
    })
    project.save()

# Always ensure all reference_frames come first in the list
def refresh_all_list(project, video_list):
    video_list.model().clear()
    for f in project.files:
        if f['type'] != 'ref_frame':
            continue
        video_list.model().appendRow(QStandardItem(f['name']))
    for f in project.files:
        if f['type'] != 'video':
            continue
        video_list.model().appendRow(QStandardItem(f['name']))
    video_list.setCurrentIndex(video_list.model().index(0, 0))

def refresh_video_list(project, video_list):
    video_list.model().clear()
    for f in project.files:
        if f['type'] != 'video':
            continue
        video_list.model().appendRow(QStandardItem(f['name']))
    video_list.setCurrentIndex(video_list.model().index(0, 0))