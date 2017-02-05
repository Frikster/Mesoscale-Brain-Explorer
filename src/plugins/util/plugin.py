from PyQt4.QtGui import *

class Plugin:
    def __init__(self, widget, widget_labels, name):
        self.name = name
        self.widget = widget
        self.widget_labels = widget_labels

    def run(self, input_paths=None):
        self.widget.params = self.widget.project.pipeline[self.widget.plugin_position]
        return self.widget.cut_off(input_paths)

    def get_input_paths(self):
        fs = self.widget.project.files
        indices = self.widget.params[self.widget_labels.video_list_indices_label]
        return [fs[i]['path'] for i in range(len(fs)) if i in indices]

    def check_ready_for_automation(self):
        return False

    def automation_error_message(self):
        return "Plugin " + self.name + " is not suitable for automation."

class Widget_default(QWidget):
    def __init__(self, project, plugin_position):
        super(Widget_default, self).__init__()

