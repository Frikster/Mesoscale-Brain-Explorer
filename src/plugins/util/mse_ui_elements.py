#!/usr/bin/env python3
import os
from . import fileloader

class Video_Selector:
    def selected_video_changed(self, selection):
        if not selection.indexes():
            return
        self.video_path = str(os.path.join(self.project.path,
                                           selection.indexes()[0].data(Qt.DisplayRole))
                              + '.npy')
        frame = fileloader.load_reference_frame(self.video_path)
        self.view.show(frame)