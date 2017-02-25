# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import sys

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from .util import fileloader
from .util import project_functions as pfs

sys.path.append('..')
import qtutil
from .util.plugin import PluginDefault
from .util.plugin import WidgetDefault
from .util.mse_ui_elements import RoiItemModel
from .util.mse_ui_elements import RoiList

# class myQStringListModel(QStringListModel):
#     def __init__(self, parent=None):
#         super(myQStringListModel, self).__init__(parent)
#
#     def createIndex(self, *args, **kwargs):


# class RoiItemModel(QAbstractListModel):
#     textChanged = pyqtSignal(str, str)
#
#     def __init__(self, parent=None):
#         super(RoiItemModel, self).__init__(parent)
#         self.rois = []
#
#     def appendRoi(self, name):
#         self.rois.append(name)
#         row = len(self.rois) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def edit_roi_name(self, name, index):
#         self.rois.append(name)
#         row = len(self.rois) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def rowCount(self, parent):
#         return len(self.rois)
#
#     def data(self, index, role):
#         if role == Qt.DisplayRole:
#             return self.rois[index.row()]
#         return
#
#     def setData(self, index, value, role):
#       if role == Qt.EditRole:
#         value = str(value)
#         if value in self.rois[index.row()]:
#           pass
#         elif value in self.rois:
#           qtutil.critical('Roi name taken.')
#         else:
#           self.textChanged.emit(self.rois[index.row()], value)
#           self.rois[index.row()] = value
#         return True
#       return super(RoiItemModel, self).setData(index, value, role)
#
#     def flags(self, index):
#         return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
#
#     def removeRow(self, roi_to_remove):
#         for roi in self.rois:
#             if roi == roi_to_remove:
#                 del roi
#                 break

class Widget(QWidget, WidgetDefault):
  class Labels(WidgetDefault.Labels):
    roi_list_indices_label = "ROIs - double click to rename"

  class Defaults(WidgetDefault.Defaults):
    roi_list_indices_default = [0]
    list_display_type = ['ref_frame', 'video']
    roi_list_types_displayed = ['roi']
    manip = 'crop'

  def __init__(self, project, plugin_position, parent=None):
    super(Widget, self).__init__(parent)
    if not project or not isinstance(plugin_position, int):
        return
    # self.plugin_position = plugin_position
    self.project = project
    #
    # # define ui components and global data
    # self.selected_videos = []
    # #self.selected_rois = []
    # self.view = MyGraphicsView(self.project)
    # self.video_list = QListView()
    self.roi_list = RoiList(self, self.Defaults.roi_list_types_displayed)
    self.roi_list.model().textChanged.connect(self.roi_item_changed)

    # self.roi_list = QListView()
    self.create_roi_button = QPushButton('Create ROI')
    self.crop_button = QPushButton('Crop to ROI(s) for selected files')

    # self.left = QFrame()
    # self.right = QFrame()

    # self.video_list.setModel(QStandardItemModel())
    # self.video_list.selectionModel().selectionChanged[QItemSelection,
    #                                                   QItemSelection].connect(self.selected_video_changed)
    # self.video_list.doubleClicked.connect(self.video_triggered)

    # model = RoiItemModel()
    # model.textChanged.connect(self.roi_item_changed)
    # self.roi_list.setModel(model)
    # self.roi_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # A flag to see whether selected_roi_changed is being entered for the first time
    # self.selected_roi_changed_flag = 0
    # self.roi_list.selectionModel().selectionChanged[QItemSelection,
    #   QItemSelection].connect(self.selected_roi_changed)

    # for f in project.files:
    #   if f['type'] != 'video':
    #     continue
    #   self.video_list.model().appendRow(QStandardItem(f['name']))

    # roi_names = [f['name'] for f in project.files if f['type'] == 'roi']
    # for roi_name in roi_names:
    #   model.appendRoi(roi_name)
    # self.view.vb.roi_placed.connect(self.update_project_roi)
    WidgetDefault.__init__(self, project, plugin_position)
    # self.setup_ui()
    # if isinstance(plugin_position, int):
    #     self.params = project.pipeline[self.plugin_position]
    #     assert (self.params['name'] == 'roi_creator')
    #     self.setup_param_signals()
    #     try:
    #         self.setup_params()
    #     except:
    #         self.setup_params(reset=True)
    #     pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
    #                      Defaults.list_display_type, self.toolbutton_values)

  # def video_triggered(self, index):
  #     pfs.video_triggered(self, index)

  def roi_item_edited(self, item):
    new_name = item.text()
    prev_name = item.data(Qt.UserRole)
    # disconnect and reconnect signal
    self.roi_list.itemChanged.disconnect()
    item.setData(new_name, Qt.UserRole)
    self.roi_list.model().itemChanged[QStandardItem.setData].connect(self.roi_item_edited)

  def setup_ui(self):
      super().setup_ui()
    # vbox_view = QVBoxLayout()
    # vbox_view.addWidget(self.view)
    # self.view.vb.setCursor(Qt.CrossCursor)
    # self.left.setLayout(vbox_view)
    #
    # vbox = QVBoxLayout()
    # list_of_manips = pfs.get_list_of_project_manips(self.project)
    # self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
    # self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
    # vbox.addWidget(self.toolbutton)
    # vbox.addWidget(QLabel('Choose video:'))
    # self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    # self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    # vbox.addWidget(self.video_list)
    # pb = QPushButton('Create ROI')
    # pb.clicked.connect(self.create_roi)
      self.vbox.addWidget(self.create_roi_button)
    # pb = QPushButton('Crop to ROI(s) for selected files')
    # pb.clicked.connect(self.crop_clicked)
      self.vbox.addWidget(self.crop_button)
    # pb = QPushButton('Delete selected ROIs')
    # pb.clicked.connect(self.delete_roi)
    # vbox.addWidget(pb)
    # vbox.addWidget(qtutil.separator())
    # vbox2 = QVBoxLayout()
    # w = QWidget()
    # w.setLayout(vbox2)
    # vbox.addWidget(w)
    # vbox.addWidget(qtutil.separator())
      self.vbox.addWidget(QLabel(self.Labels.roi_list_indices_label))
      self.vbox.addWidget(self.roi_list)

    # self.right.setLayout(self.vbox)
    #
    # splitter = QSplitter(Qt.Horizontal)
    # splitter.setHandleWidth(3)
    # splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    # splitter.addWidget(self.left)
    # splitter.addWidget(self.right)
    # hbox_global = QHBoxLayout()
    # hbox_global.addWidget(splitter)
    # self.setLayout(hbox_global)

    # hbox.addLayout(vbox)
    # hbox.setStretch(0, 1)
    # hbox.setStretch(1, 0)
    # self.setLayout(hbox)

  # def refresh_video_list_via_combo_box(self, trigger_item=None):
  #     pfs.refresh_video_list_via_combo_box(self, trigger_item)
  #
  # def selected_video_changed(self, selected, deselected):
  #     pfs.selected_video_changed_multi(self, selected, deselected)

  def setup_signals(self):
      super().setup_signals()
      self.create_roi_button.clicked.connect(self.create_roi)
      self.crop_button.clicked.connect(self.execute_primary_function)
      # self.roi_list.selectionModel().selectionChanged[QItemSelection,
      #                                                 QItemSelection].connect(self.selected_roi_changed)
      self.view.vb.roi_placed.connect(self.update_project_roi)


  def setup_params(self, reset=False):
      super().setup_params(reset)
      self.roi_list.setup_params()

      # if len(self.params) == 1 or reset:
      #     self.update_plugin_params(self.Labels.roi_list_indices_label, self.Defaults.roi_list_indices_default)
      #     # self.update_plugin_params(Labels.video_list_indices_label, Defaults.video_list_indices_default)
      #     # self.update_plugin_params(Labels.last_manips_to_display_label, Defaults.last_manips_to_display_default)
      #
      # roi_indices = self.params[self.Labels.roi_list_indices_label]
      # theQIndexObjects = [self.roi_list.model().createIndex(rowIndex, 0) for rowIndex in
      #                     roi_indices]
      # for Qindex in theQIndexObjects:
      #     self.roi_list.selectionModel().select(Qindex, QItemSelectionModel.Select)
      # # self.video_list_indices = self.params[Labels.video_list_indices_label]
      # self.toolbutton_values = self.params[Labels.last_manips_to_display_label]
      # manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
      #                if self.toolbutton.itemText(i) in self.params[Labels.last_manips_to_display_label]]
      # for item in manip_items:
      #     item.setCheckState(Qt.Checked)
      # not_checked = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
      #                if self.toolbutton.itemText(i) not in self.params[Labels.last_manips_to_display_label]]
      # for item in not_checked:
      #     item.setCheckState(Qt.Unchecked)

  def setup_param_signals(self):
      super().setup_param_signals()
      self.roi_list.setup_param_signals()
      # self.video_list.selectionModel().selectionChanged.connect(self.prepare_video_list_for_update)
      # self.toolbutton.activated.connect(self.prepare_toolbutton_for_update)
      # self.roi_list.selectionModel().selectionChanged.connect(self.prepare_roi_list_for_update)

  # def prepare_video_list_for_update(self, selected, deselected):
  #     val = [v.row() for v in self.video_list.selectedIndexes()]
  #     if not val:
  #         val = Defaults.video_list_indices_default
  #     self.update_plugin_params(Labels.video_list_indices_label, val)

  # def prepare_toolbutton_for_update(self, trigger_item):
  #     val = self.params[Labels.last_manips_to_display_label]
  #     selected = self.toolbutton.itemText(trigger_item)
  #     if selected not in val:
  #         val = val + [selected]
  #         if trigger_item != 0:
  #             val = [manip for manip in val if manip not in Defaults.last_manips_to_display_default]
  #     else:
  #         val = [manip for manip in val if manip != selected]
  #
  #     self.update_plugin_params(Labels.last_manips_to_display_label, val)

  # def prepare_roi_list_for_update(self, selected, deselected):
  #     val = [v.row() for v in self.roi_list.selectedIndexes()]
  #     self.update_plugin_params(self.Labels.roi_list_indices_label, val)

  # def update_plugin_params(self, key, val):
  #     pfs.update_plugin_params(self, key, val)

  def remove_all_rois(self):
    rois = self.view.vb.rois[:]
    for roi in rois:
      if not roi.isSelected:
        self.view.vb.selectROI(roi)
      self.view.vb.removeROI()

  # def selected_roi_changed(self, selection):
  #   # if self.selected_roi_changed_flag == 0:
  #   #   self.selected_roi_changed_flag = self.selected_roi_changed_flag + 1
  #   #   return
  #   if not selection.indexes() or self.view.vb.drawROImode:
  #     return
  #   self.remove_all_rois()
  #
  #   # todo: re-explain how you can figure out to go from commented line to uncommented line
  #   # rois_selected = str(selection.indexes()[0].data(Qt.DisplayRole).toString())
  #   rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
  #                    for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
  #   if len(rois_selected) == 1 and rois_selected[0] == 'None':
  #       return
  #   rois_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
  #   rois_to_add = [x for x in rois_selected if x not in rois_in_view]
  #   for roi_to_add in rois_to_add:
  #     self.view.vb.loadROI([self.project.path + '/' + roi_to_add + '.roi'])

  def roi_item_changed(self, prev_name, new_name):
    # todo: Why not pass the paramaters as strings? Is it important to have them in this format?
    if prev_name == '':
      raise ValueError("The ROI already has no name... you monster")
    prev_name_str = str(prev_name)
    new_name_str = str(new_name)
    self.remove_all_rois()
    old_path = self.project.path + '/' + str(prev_name_str) + '.roi'
    self.view.vb.loadROI([old_path])
    assert(len(self.view.vb.rois) == 1)
    roi = self.view.vb.rois[0]
    roi.setName(str(new_name_str))
    for i in range(len(self.project.files)):
      if self.project.files[i]['path'].endswith(str(prev_name_str) + '.roi'):
        new_path = self.project.files[i]['path'].replace(prev_name_str, new_name_str)
        os.rename(self.project.files[i]['path'], new_path)
        self.view.vb.saveROI(new_path)
        self.project.files[i]['path'] = self.project.files[i]['path'].replace(prev_name_str, new_name_str)
        self.project.files[i]['name'] = new_name_str
    self.project.save()

  def update_project_roi(self, roi):
    name = roi.name
    if not name:
      raise ValueError('ROI has no name')
    if self.view.vb.drawROImode:
      return

    roi.setName(name)
    path = os.path.join(self.project.path, name + '.roi')
    self.view.vb.saveROI(path)
    # TODO check if saved, notifiy user of save and save location (really needed if they can simply export?)
    if path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
      self.project.files.append({
        'path': path,
        'type': 'roi',
        'source_video': self.shown_video_path,
        'name': name
      })
    else:
      for i, file in enumerate(self.project.files):
        if file['path'] == path:
          self.project.files[i]['source_video'] = self.shown_video_path
    self.project.save()

    roi_names = [f['name'] for f in self.project.files if f['type'] == 'roi']
    for roi_name in roi_names:
      if roi_name not in self.roi_list.model().rois:
        self.roi_list.model().appendRoi(roi_name)

  def create_roi(self):
    self.view.vb.addPolyRoiRequest()

  def delete_roi(self):
    rois_selected = [str(self.roi_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
                     for x in range(len(self.roi_list.selectionModel().selectedIndexes()))]
    if rois_selected == None:
      return
    rois_dict = [self.project.files[x] for x in range(len(self.project.files))
                 if (self.project.files[x]['type'] == 'roi' and self.project.files[x]['name'] in rois_selected)]
    self.project.files = [self.project.files[x] for x in range(len(self.project.files))
                          if self.project.files[x] not in rois_dict]
    self.project.save()
    self.view.vb.setCurrentROIindex(None)

    for roi_to_remove in [rois_dict[x]['name'] for x in range(len(rois_dict))]:
      self.roi_list.model().removeRow(roi_to_remove)

  def crop_clicked(self):
      # progress = QProgressDialog('Cropping for selection', 'Abort', 0, 100, self)
      # progress.setAutoClose(True)
      # progress.setMinimumDuration(0)
      #
      # def callback(x):
      #     progress.setValue(x * 100)
      #     QApplication.processEvents()
      self.crop_ROI()

  def execute_primary_function(self, input_paths=None):
    if not input_paths:
      if not self.selected_videos:
          return
      else:
          selected_videos = self.selected_videos
    else:
      selected_videos = input_paths

    global_progress = QProgressDialog('Total Progress Cropping to ROIs for Selection', 'Abort', 0, 100, self)
    global_progress.setAutoClose(True)
    global_progress.setMinimumDuration(0)
    def global_callback(x):
        global_progress.setValue(x * 100)
        QApplication.processEvents()
    output_paths = []
    total = len(selected_videos)
    for i, video_path in enumerate(selected_videos):
      global_callback(i / total)
      progress = QProgressDialog('Cropping to ROIs for ' + video_path, 'Abort', 0, 100, self)
      progress.setAutoClose(True)
      progress.setMinimumDuration(0)
      def callback(x):
          progress.setValue(x * 100)
          QApplication.processEvents()
      frames = fileloader.load_file(video_path)
      callback(0.2)
      # Return if there is no image or rois in view
      if self.view.vb.img == None or len(self.view.vb.rois) == 0:
        qtutil.critical("there is no image or rois in view ")
        return

      # swap axis for aligned_frames
      frames_swap = np.swapaxes(np.swapaxes(frames, 0, 1), 1, 2)
      callback(0.4)
      # Collect ROI's and combine
      numROIs = len(self.view.vb.rois)
      arrRegion_masks = []
      for i in range(numROIs):
        roi = self.view.vb.rois[i]
        arrRegion_mask = roi.getROIMask(frames_swap, self.view.vb.img, axes=(0, 1))
        arrRegion_masks.append(arrRegion_mask)
      callback(0.6)
      combined_mask = np.sum(arrRegion_masks, axis=0)
      callback(0.8)
      # Make all rows with all zeros na
      # combined_mask[(combined_mask == 0)] = None
      self.mask = combined_mask
      # TODO: save mask as well
      # #combined_mask.astype(dtype_string).tofile(os.path.expanduser('/Downloads/')+"mask.raw")
      # print("mask saved to " + os.path.expanduser('/Downloads/')+"mask.raw")

      # In imageJ - Gap Between Images The number of bytes from the end of one image to the beginning of the next.
      # Set this value to width × height × bytes-per-pixel × n to skip n images for each image read. So use 4194304
      # Dont forget to set Endian value and set to 64 bit
      roi_frames = (frames * combined_mask[np.newaxis, :, :])
      callback(1)
      # name_before, ext = os.path.splitext(os.path.basename(video_path))
      # name_after = fileloader.get_name_after_no_overwrite(name_before, self.Defaults.manip, self.project)
      # path = str(os.path.join(self.project.path, name_after) + '.npy')
      # path = os.path.join(self.project.path, 'roi' + '.npy')
      path = pfs.save_project(video_path, self.project, roi_frames, self.Defaults.manip, 'video')
      output_paths = output_paths + [path]
      pfs.refresh_list(self.project, self.video_list,
                       self.params[self.Labels.video_list_indices_label],
                       self.Defaults.list_display_type,
                       self.params[self.Labels.last_manips_to_display_label])
    global_callback(1)
    return output_paths

  def setup_whats_this(self):
    super().setup_whats_this()
    self.create_roi_button.setWhatsThis("Click to enter ROI placement mode allowing you to create ROIs on the image "
                                        "which will be saved and can be accessed in the list below. Left click to "
                                        "add an ROI corner. Right click to complete the ROI. ROI corners can also be "
                                        "modified after creating the ROI by left clicking and dragging them. "
                                        "Additional corners can be added by left clicking an ROI edge. "
                                        "Right click a modified ROI and click save to save changes made to an ROI")
    self.crop_button.setWhatsThis("Select one or many ROIs below and then select one or many image stacks above. "
                                  "All selected image stacks will be cropped to the ROIs selected")
    self.roi_list.setWhatsThis("Select ROIs you've made. Double-click to change their name. For automation you must "
                               "pick ROI(s) that will be cropped to for all files in the pipeline. ROI corners can be "
                               "modified after creating the ROI by left clicking and dragging them. Additional corners "
                               "can be added by left clicking an ROI edge. "
                               "Right click a modified ROI and click save to save changes made to an ROI")


class MyPlugin(PluginDefault):
  def __init__(self, project, plugin_position):
    self.name = 'Crop to ROIs'
    self.widget = Widget(project, plugin_position)
    super().__init__(self.widget, self.widget.Labels, self.name)

  # def run(self):
  #   pass

  def check_ready_for_automation(self):
      if len(self.widget.view.vb.rois) <= 0:
        return False
      else:
        return True

  def automation_error_message(self):
      return "Select at least one ROI for each ROI cropper plugin"

