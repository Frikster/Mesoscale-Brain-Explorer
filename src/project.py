#!/usr/bin/env python3

import os
import json
import traceback
import shutil

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import qtutil

class NewProjectDialog(QDialog):
  def __init__(self, parent=None):
    super(NewProjectDialog, self).__init__(parent)
  
    self.path = None
    self.name = None

    self.setWindowTitle('Create new project')
    self.setup_ui()

  def setup_ui(self):
    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Project name:'))
    self.project_name_edit = QLineEdit()
    self.project_name_edit.textChanged[str].connect(self.project_name_changed)
    vbox.addWidget(self.project_name_edit)
    vbox.addWidget(QLabel('Location:'))
    hbox = QHBoxLayout()
    self.project_path_edit = QLineEdit()
    self.project_path_edit.setReadOnly(True)
    hbox.addWidget(self.project_path_edit)
    tb = QToolButton()
    tb.setIcon(QIcon('pics/folder-293.png'))
    tb.setIconSize(QSize(18, 18))
    tb.clicked.connect(self.get_path)
    hbox.addWidget(tb)
    vbox.addLayout(hbox)
    vbox.addWidget(QLabel('Final location:'))
    self.final_path_edit = QLineEdit()
    self.final_path_edit.setReadOnly(True)
    vbox.addWidget(self.final_path_edit)

    vbox.addStretch()
    vbox.addSpacing(10)

    hbox = QHBoxLayout()
    hbox.addSpacerItem(QSpacerItem(1, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
    pb = QPushButton('&Cancel')
    pb.clicked.connect(self.close)
    hbox.addWidget(pb)
    pb = QPushButton('&Go')
    pb.clicked.connect(self.go)
    hbox.addWidget(pb)

    vbox.addLayout(hbox)
    self.setLayout(vbox)
    self.resize(400, 0)

  def project_name_changed(self, project_name):
    if project_name and self.project_path_edit.text():
      final_path = os.path.join(str(self.project_path_edit.text()), str(project_name))
      self.final_path_edit.setText(final_path)
    else:
      self.final_path_edit.clear()

  def get_path(self):
    dialog = QFileDialog(self, 'Select project location', str(QSettings().value('projects_path')))
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.DontUseNativeDialog)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    path = ''
    if dialog.exec_():
      path = dialog.selectedFiles()[0]
    if not path:
      return
    QSettings().setValue('projects_path', path)
    self.project_path_edit.setText(path)
    if self.project_name_edit.text():
      self.final_path_edit.setText(os.path.join(str(path), str(self.project_name_edit.text())))

  def go(self):
    path = str(self.final_path_edit.text())
    if not path:
      qtutil.critical('Choose project location.')
    elif os.path.isdir(path):
      qtutil.critical('Directory already exists.')
    else:
      try:
        os.makedirs(path)  
      except Exception:
        qtutil.critical(traceback.format_exc())
      else:
        self.path = path
        self.name = str(self.project_name_edit.text())
        self.close()
        return
    self.path = None
    self.name = None

class ProjectManager:
  def __init__(self, mainwindow):
    self.mainwindow = mainwindow
    self.new_project_dialog = NewProjectDialog(mainwindow)

  def new_project(self):
    self.new_project_dialog.exec_()
    path = self.new_project_dialog.path
    if path:
      shutil.copy('../templates/spcproject.json', path)
      project = Project(path)
      project.name = self.new_project_dialog.name
      project.save()
      return project
    return None

  def open_project(self, path=''):
    if not path:
      dialog = QFileDialog(self.mainwindow, 'Select project location', str(QSettings().value('projects_path')))
      dialog.setFileMode(QFileDialog.Directory)
      dialog.setOption(QFileDialog.DontUseNativeDialog)
      dialog.setOption(QFileDialog.ShowDirsOnly, True)
      if dialog.exec_():
        path = str(dialog.selectedFiles()[0])
        if path:
          if not os.path.isfile(os.path.join(path, 'spcproject.json')):
            qtutil.critical('Directory is not a project.')
            return None
          parent = os.path.abspath(os.path.join(path, os.pardir))
          QSettings().setValue('projects_path', parent)
      
    if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'spcproject.json')):
      return Project(path)
    else:
      return None

class Project:
  def __init__(self, path):
    self.path = path
    self.attrs = json.load(open(os.path.join(path, 'spcproject.json')))
    self.name = self.attrs['name']
    self.files = self.attrs['files']
    self.pipeline = self.attrs['pipeline']

  def __contains__(self, key):
    return key in self.attrs

  def __getitem__(self, key):
    return self.attrs[key]

  def __setitem__(self, key, value):
    self.attrs[key] = value
    
  def save(self):
    self.attrs['name'] = self.name
    self.attrs['pipeline'] = self.pipeline
    self.attrs['files'] = self.files
    json.dump(self.attrs, open(os.path.join(self.path, 'spcproject.json'), 'w'),
      indent=2)

  def set_pipeline(self, data):
    self.pipeline = data
