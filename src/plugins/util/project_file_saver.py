#!/usr/bin/env python3

import os
import numpy as np

def save_project_video(video_path, project, frames, manip):
    name, ext = os.path.splitext(os.path.basename(video_path))
    name = str(name + '_' + manip)
    path = str(os.path.join(project.path, name) + '.npy')
    np.save(path, frames)
    project.files.append({
        'path': path,
        'type': 'video',
        'source_video': video_path,
        'manipulations': [manip],
        'name': name
    })
    project.save()