#!/usr/bin/env python3

import os
import numpy as np

def save_project_video(video_path, project, frames, manip):
    name_before, ext = os.path.splitext(os.path.basename(video_path))
    file_before = [files for files in project.files if files['name'] == name_before]
    assert(len(file_before) == 1)
    file_before = file_before[0]

    name_after = str(name_before + '_' + manip)
    path = str(os.path.join(project.path, name_after) + '.npy')
    np.save(path, frames)
    project.files.append({
        'path': path,
        'type': 'video',
        'source_video': video_path,
        'manipulations': str(file_before['manipulations'] + [manip]),
        'name': name_after
    })
    project.save()