#!/usr/bin/env python3

import os
import numpy as np
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import ast
from .mse_ui_elements import CheckableComboBox

def save_project(video_path, project, frames, manip, file_type):
    name_before, ext = os.path.splitext(os.path.basename(video_path))
    file_before = [files for files in project.files if files['name'] == name_before]
    assert(len(file_before) == 1)
    file_before = file_before[0]

    name_after = str(name_before + '_' + manip)
    path = str(os.path.join(project.path, name_after) + '.npy')
    if frames is not None:
        np.save(path, frames)
    if not file_before['manipulations'] == []:
        project.files.append({
            'path': path,
            'type': file_type,
            'source_video': video_path,
            'manipulations': str(ast.literal_eval(file_before['manipulations']) + [manip]),
            'name': name_after
        })
    else:
        project.files.append({
            'path': path,
            'type': file_type,
            'source_video': video_path,
            'manipulations': str([manip]),
            'name': name_after
        })
    project.save()

def change_origin(project, video_path, origin):
    file = [files for files in project.files if files['path'] == video_path]
    assert(len(file) == 1)
    file = file[0]
    index_of_file = project.files.index(file)
    project.files[index_of_file]['origin'] = str(origin)
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

def refresh_video_list(project, video_list, last_manips_to_display=['All']):
    video_list.model().clear()
    for f in project.files:
        if f['type'] != 'video':
            continue
        if 'All' in last_manips_to_display:
            video_list.model().appendRow(QStandardItem(f['name']))
        elif f['manipulations'] != []:
            if ast.literal_eval(f['manipulations'])[-1] in last_manips_to_display:
                video_list.model().appendRow(QStandardItem(f['name']))
    video_list.setCurrentIndex(video_list.model().index(0, 0))

def get_project_file_from_key_item(project, key, item):
    file = [files for files in project.files if files[key] == item]
    if not file:
        return
    assert (len(file) == 1)
    return file[0]

def add_combo_dropdown(widget, title, items):
    # widget.toolbutton = QToolButton(widget)
    # widget.toolbutton.setText(title)
    # widget.toolmenu = QMenu(widget)
    widget.ComboBox = CheckableComboBox()
    widget.ComboBox.addItem('All')
    item = widget.ComboBox.model().item(0, 0)
    item.setCheckState(Qt.Checked)
    for i, text in enumerate(items):
        widget.ComboBox.addItem(text)
        item = widget.ComboBox.model().item(i+1, 0)
        item.setCheckState(Qt.Unchecked)

    # widget.toolbutton.setMenu(widget.toolmenu)
    # widget.toolbutton.setPopupMode(QToolButton.InstantPopup)
    return widget.ComboBox

from collections import Iterable
def flatten(foo):
    for x in foo:
        if hasattr(x, '__iter__') and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x

def get_list_of_project_manips(project):
    vid_files = [f for f in project.files if f['type'] == 'video']
    list_of_manips = [x['manipulations'] for x in vid_files if x['manipulations'] != []]
    list_of_manips = [ast.literal_eval(l) for l in list_of_manips]
    list_of_manips = list(flatten(list_of_manips))
    return list(set(list_of_manips))