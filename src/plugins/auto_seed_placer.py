# # -*- coding: utf-8 -*-
# # !/usr/bin/env python3
#
# import csv
# import os
# from shutil import copyfile
#
# import numpy as np
# import qtutil
# from PyQt4 import QtCore
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
#
# from .util import fileloader
# from .util import project_functions as pfs
# from .util.mygraphicsview import MyGraphicsView
#
#
# # This the code for getting the seed locations from bregma.
#
# # Bregma is (0,0).
#
# # Units are mm.
#
# # ppmm is number of px per millimeter.  Should be 256 px /10.75 mm for last summer.
#
# # ppmm = size(If2,1)/8.6; #user defined
# # ii = 1; #clear pos
# #
# # pos(ii).name = 'M2'; pos(ii).y = 2.5; pos(ii).x = 1; ii = ii + 1;
# # pos(ii).name = 'M1'; pos(ii).y = 1.75; pos(ii).x = 1.5;  ii = ii + 1;
# # pos(ii).name = 'AC'; pos(ii).y = 0; pos(ii).x = .5; ii = ii + 1;
# # pos(ii).name = 'HL'; pos(ii).y = 0; pos(ii).x = 2;  ii = ii + 1;
# # pos(ii).name = 'BC'; pos(ii).y = -1; pos(ii).x = 3.5; ii = ii + 1;
# # pos(ii).name = 'RS'; pos(ii).y = -2.5; pos(ii).x = .5;  ii = ii + 1;
# # pos(ii).name = 'V1'; pos(ii).y = -2.5; pos(ii).x = 2.5; ii = ii + 1;
# #
# ##clear xx yy yy2
# # for i = 1:length(pos)
# #    xx(i) = yb + -ppmm*pos(i).y;
# #    yy(i) = xb - ppmm*pos(i).x;
# #    yy2(i) = xb + ppmm*pos(i).x;
# # end
# # xx = round([xx xx]);
# # yy = round([yy yy2]);
#
#
# class SeedItemModel(QAbstractListModel):
#     textChanged = pyqtSignal(str, str)
#
#     # dataChanged = pyqtSignal(int, int)
#
#     def __init__(self, parent=None):
#         super(SeedItemModel, self).__init__(parent)
#         self.seeds = []
#
#     def appendseed(self, name):
#         self.seeds.append(name)
#         row = len(self.seeds) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def edit_seed_name(self, name, index):
#         self.seeds.append(name)
#         row = len(self.seeds) - 1
#         self.dataChanged.emit(self.index(row), self.index(row))
#
#     def rowCount(self, parent):
#         return len(self.seeds)
#
#     def data(self, index, role):
#         if role == Qt.DisplayRole:
#             return self.seeds[index.row()]
#         return
#
#     def setData(self, index, value, role):
#         if role in [Qt.DisplayRole, Qt.EditRole]:
#             self.textChanged.emit(self.seeds[index.row()], value)
#             self.seeds[index.row()] = str(value)
#             return True
#         return super(SeedItemModel, self).setData(index, value, role)
#
#     def flags(self, index):
#         return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
#
#     def removeRow(self, seed_to_remove):
#         for seed in self.seeds:
#             if seed == seed_to_remove:
#                 del seed
#                 break
#
#
# class Widget(QWidget):
#     def __init__(self, project, parent=None):
#         super(Widget, self).__init__(parent)
#         # check project
#         if not project:
#             return
#         self.project = project
#
#         # define widgets and data
#         self.headers = None
#         self.data = None
#         self.view = MyGraphicsView(self.project)
#         self.table_widget = AutoSeedCoords(self.data, 0, 3)
#         self.left = QFrame()
#         self.right = QFrame()
#         self.video_list = QListView()
#         self.seed_list = QListView()
#         # self.open_dialogs = []
#
#         self.setup_ui()
#
#         self.video_list.setModel(QStandardItemModel())
#         self.video_list.selectionModel().selectionChanged[QItemSelection,
#                                                           QItemSelection].connect(self.selected_video_changed)
#         self.video_list.doubleClicked.connect(self.video_triggered)
#         for f in project.files:
#             if f['type'] != 'video':
#                 continue
#             self.video_list.model().appendRow(QStandardItem(str(f['name'])))
#         self.video_list.setCurrentIndex(self.video_list.model().index(0, 0))
#
#         # setup ROI and seed list widgets
#         model = SeedItemModel()
#         # todo: this wont update that specific changed value
#         model.textChanged.connect(self.update_project_seed)
#         self.seed_list.setModel(model)
#         self.seed_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
#
#         # A flag to see whether selected_seed_changed is being entered for the first time
#         self.selected_seed_changed_flag = 0
#         self.seed_list.selectionModel().selectionChanged[QItemSelection,
#                                                         QItemSelection].connect(self.selected_seed_changed)
#         seed_names = [f['name'] for f in project.files if f['type'] == 'seed']
#         for seed_name in seed_names:
#             if seed_name not in self.seed_list.model().seeds:
#                 model.appendseed(seed_name)
#         self.seed_list.setCurrentIndex(model.index(0, 0))
#
#         # setup seed table
#         if 'seed_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
#             self.data = None
#             self.headers = None
#         else:
#             text_file_path = [self.project.files[x]['path'] for x in range(len(self.project.files))
#                               if self.project.files[x]['type'] == 'seed_table']
#             assert(len(text_file_path) == 1)
#             text_file_path = text_file_path[0]
#             seed_table = []
#             with open(text_file_path, 'rt', encoding='ascii') as csvfile:
#                 seed_table_it = csv.reader(csvfile, delimiter=',')
#                 for row in seed_table_it:
#                     seed_table = seed_table + [row]
#             seed_table = np.array(seed_table)
#             self.headers = [str.strip(x) for x in seed_table[0,]]
#             seed_table_range = range(len(seed_table))[1:]
#             seed_names = [seed_table[x, 0] for x in seed_table_range]
#             seed_coord_x = [float(seed_table[x, 1]) for x in seed_table_range]
#             seed_coord_y = [float(seed_table[x, 2]) for x in seed_table_range]
#             self.data = {self.headers[0]: seed_names, self.headers[1]: seed_coord_x, self.headers[2]: seed_coord_y}
#             if text_file_path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
#                 self.project.files.append({
#                     'path': text_file_path,
#                     'type': 'seed_table',
#                     'source_video': self.video_path,
#                     'name': os.path.basename(text_file_path)
#                 })
#             self.table_widget.clear()
#             self.table_widget.setRowCount(len(self.data[self.headers[0]]))
#             self.table_widget.update(self.data)
#
#     def video_triggered(self, index):
#         pfs.video_triggered(self, index)
#     # def seed_item_edited(self, item):
#     #   new_name = item.text()
#     #   prev_name = item.data(Qt.UserRole)
#     #   # disconnect and reconnect signal
#     #   self.seed_list.itemChanged.disconnect()
#     #   item.setData(new_name, Qt.UserRole)
#     #   self.seed_list.model().itemChanged[QStandardItem.setData].connect(self.seed_item_edited)
#
#     def setup_ui(self):
#         vbox_view = QVBoxLayout()
#         vbox_view.addWidget(self.view)
#         self.left.setLayout(vbox_view)
#
#         vbox = QVBoxLayout()
#         list_of_manips = pfs.get_list_of_project_manips(self.project)
#         self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
#         self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
#         vbox.addWidget(self.toolbutton)
#         vbox.addWidget(QLabel('Choose video:'))
#         self.video_list.setStyleSheet('QListView::item { height: 26px; }')
#         self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
#         vbox.addWidget(self.video_list)
#         pb = QPushButton('Load anatomical coordinates (relative to selected origin)')
#         pb.clicked.connect(self.load_seed_table)
#         vbox.addWidget(pb)
#         vbox.addWidget(self.table_widget)
#         self.table_widget.itemChanged.connect(self.update_auto_seeds)
#         pb = QPushButton('Add these Seeds to project')
#         pb.clicked.connect(self.auto_seed)
#         vbox.addWidget(pb)
#         # vbox2 = QVBoxLayout()
#         # w = QWidget()
#         # w.setLayout(vbox2)
#         # vbox.addWidget(w)
#         vbox.addWidget(qtutil.separator())
#         vbox.addWidget(QLabel('seeds'))
#         vbox.addWidget(self.seed_list)
#         self.right.setLayout(vbox)
#
#         splitter = QSplitter(Qt.Horizontal)
#         splitter.setHandleWidth(3)
#         splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
#         splitter.addWidget(self.left)
#         splitter.addWidget(self.right)
#         hbox_global = QHBoxLayout()
#         hbox_global.addWidget(splitter)
#         self.setLayout(hbox_global)
#
#     def refresh_video_list_via_combo_box(self, trigger_item=None):
#         pfs.refresh_video_list_via_combo_box(self, trigger_item)
#
#     def remove_all_seeds(self):
#         seeds = self.view.vb.rois[:]
#         for seed in seeds:
#             if not seed.isSelected:
#                 self.view.vb.selectROI(seed)
#             self.view.vb.removeROI()
#
#     def selected_video_changed(self, selection):
#         if not selection.indexes():
#             return
#         self.video_path = str(os.path.join(self.project.path,
#                                            selection.indexes()[0].data(Qt.DisplayRole))
#                               + '.npy')
#         frame = fileloader.load_reference_frame(self.video_path)
#         self.view.show(frame)
#
#     def selected_seed_changed(self, selection):
#         if self.selected_seed_changed_flag == 0:
#             self.selected_seed_changed_flag = self.selected_seed_changed_flag + 1
#             return
#         if not selection.indexes() or self.view.vb.drawROImode:
#             return
#
#         self.remove_all_seeds()
#         seeds_selected = [str(self.seed_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
#                          for x in range(len(self.seed_list.selectionModel().selectedIndexes()))]
#         seeds_in_view = [self.view.vb.rois[x].name for x in range(len(self.view.vb.rois))]
#         seeds_to_add = [x for x in seeds_selected if x not in seeds_in_view]
#         for seed_to_add in seeds_to_add:
#             self.view.vb.loadROI([self.project.path + '/' + seed_to_add + '.seed'])
#
#     def load_seed_table(self):
#         text_file_path = QFileDialog.getOpenFileName(
#             self, 'Load images', QSettings().value('last_load_text_path'),
#             'Video files (*.csv *.txt)')
#         if not text_file_path:
#             return
#         QSettings().setValue('last_load_text_path', os.path.dirname(text_file_path))
#
#         seed_table = []  # numpy way: np.empty(shape=(4, ))
#         with open(text_file_path, 'rt', encoding='ascii') as csvfile:
#             seed_table_it = csv.reader(csvfile, delimiter=',')
#             for row in seed_table_it:
#                 seed_table = seed_table + [row]
#         seed_table = np.array(seed_table)
#         self.headers = [str.strip(x) for x in seed_table[0,]]
#         seed_table_range = range(len(seed_table))[1:]
#         seed_names = [str(seed_table[x, 0]) for x in seed_table_range]
#         seed_coord_x = [float(seed_table[x, 1]) for x in seed_table_range]
#         seed_coord_y = [float(seed_table[x, 2]) for x in seed_table_range]
#         self.data = {self.headers[0]: seed_names, self.headers[1]: seed_coord_x, self.headers[2]: seed_coord_y}
#         # for now only support having one seed_table associated per project
#         text_file_path_for_project = os.path.join(self.project.path, os.path.basename(text_file_path))
#         if 'seed_table' not in [self.project.files[x]['type'] for x in range(len(self.project.files))]:
#             if text_file_path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
#                 if not (os.path.normpath(text_file_path) ==
#                             os.path.normpath(text_file_path_for_project)):
#                     copyfile(text_file_path, text_file_path_for_project)
#                 self.project.files.append({
#                     'path': text_file_path_for_project,
#                     'type': 'seed_table',
#                     'source_video': self.video_path,
#                     'name': os.path.basename(text_file_path)
#                 })
#             else:
#                 # Replace old values if the same file with different values is given
#                 for i, item in enumerate(self.project.files):
#                     if item['path'] == text_file_path:
#                         self.project.files[i] = {
#                             'path': text_file_path_for_project,
#                             'type': 'seed_table',
#                             'source_video': self.video_path,
#                             'name': os.path.basename(text_file_path)
#                         }
#         else:
#             # Replace old table with new one
#             # todo: remove duplicates
#             for i, item in enumerate(self.project.files):
#                 if item['type'] == 'seed_table':
#                     self.project.files[i] = {
#                         'path': text_file_path_for_project,
#                         'type': 'seed_table',
#                         'source_video': self.video_path,
#                         'name': os.path.basename(text_file_path)
#                     }
#         self.table_widget.clear()
#         self.table_widget.setRowCount(len(self.data[self.headers[0]]))
#         self.table_widget.update(self.data)
#         self.auto_seed()
#
#     def auto_seed(self):
#         locs = zip(self.data[self.headers[0]], self.data[self.headers[1]],
#                    self.data[self.headers[2]])
#
#         # Warning: size must always be the second column
#         for quad in list(locs):
#             half_length = self.project['unit_per_pixel']
#             self.remove_all_seeds()
#             x1 = (quad[1] - half_length)
#             x2 = (quad[1] - half_length)
#             x3 = (quad[1] + half_length)
#             x4 = (quad[1] + half_length)
#             y1 = (quad[2] - half_length)
#             y2 = (quad[2] + half_length)
#             y3 = (quad[2] + half_length)
#             y4 = (quad[2] - half_length)
#
#             self.view.vb.addPolyRoiRequest()
#             self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x1, y1))
#             self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x2, y2))
#             self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x3, y3))
#             self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x4, y4))
#             self.view.vb.autoDrawPolygonRoi(quad[0], pos=QtCore.QPointF(x4, y4))
#             self.view.vb.autoDrawPolygonRoi(quad[0], finished=True)
#             assert(len(self.view.vb.rois) == 1)
#             seed = self.view.vb.rois[0]
#             self.update_project_seed(seed)
#
#     # def update_table(self):
#     #   locs = zip(self.data[self.headers[0]], self.data[self.headers[1]],
#     #              self.data[self.headers[2]], self.data[self.headers[3]])
#     #   model = AutoseedCoords(self.data, len(list(locs)), 4)
#     #   model.show()
#     #   # self.open_dialogs.append(model)
#
#     # def delete_seed(self):
#     #   seeds_selected = [str(self.seed_list.selectionModel().selectedIndexes()[x].data(Qt.DisplayRole))
#     #                    for x in range(len(self.seed_list.selectionModel().selectedIndexes()))]
#     #   if seeds_selected == None:
#     #     return
#     #   seeds_dict = [self.project.files[x] for x in range(len(self.project.files))
#     #                if (self.project.files[x]['type'] == 'seed' and self.project.files[x]['name'] in seeds_selected)]
#     #   self.project.files = [self.project.files[x] for x in range(len(self.project.files))
#     #                         if self.project.files[x] not in seeds_dict]
#     #   self.project.save()
#     #   self.view.vb.setCurrentseedindex(None)
#     #
#     #   for seed_to_remove in [seeds_dict[x]['name'] for x in range(len(seeds_dict))]:
#     #     self.seed_list.model().removeRow(seed_to_remove)
#
#     def update_project_seed(self, seed):
#         name = seed.name
#         if not name:
#             raise ValueError('seed has no name')
#         if self.view.vb.drawROImode:
#             return
#
#         path = os.path.join(self.project.path, name + '.seed')
#         self.view.vb.saveROI(path)
#         if path not in [self.project.files[x]['path'] for x in range(len(self.project.files))]:
#             self.project.files.append({
#                 'path': path,
#                 'type': 'seed',
#                 'source_video': self.video_path,
#                 'name': name
#             })
#         else:
#             for i, file in enumerate(self.project.files):
#                 if file['path'] == path:
#                     self.project.files[i]['source_video'] = self.video_path
#         self.project.save()
#
#         seed_names = [f['name'] for f in self.project.files if f['type'] == 'seed']
#         for seed_name in seed_names:
#             if seed_name not in self.seed_list.model().seeds:
#                 self.seed_list.model().appendseed(seed_name)
#
#     # even tried deleting everything...
#     # seed_names = [f['name'] for f in self.project.files if f['type'] == 'seed']
#     # for seed_name in seed_names:
#     #     if seed_name not in self.seed_list.model().seeds:
#     #         self.seed_list.model().appendseed(seed_name)
#
#     def update_auto_seeds(self, item):
#         col = item.column()
#         row = item.row()
#         try:
#             val = float(item.text())
#         except:
#             val = str(item.text())
#         if item.tableWidget().horizontalHeaderItem(col):
#             header = item.tableWidget().horizontalHeaderItem(col).text()
#             header = str(header)
#             col_to_change = self.data[header]
#             col_to_change[row] = val
#             self.data[header] = col_to_change
#             self.auto_seed()
#
#
# class AutoSeedCoords(QTableWidget):
#     def __init__(self, data=None, *args):
#         QTableWidget.__init__(self, *args)
#         self.data = data
#         self.update(self.data)
#
#     def setmydata(self):
#         horHeaders = self.data.keys()
#         for n, key in enumerate(sorted(horHeaders)):
#             for m, item in enumerate(self.data[key]):
#                 newitem = QTableWidgetItem(str(item))
#                 self.setItem(m, n, newitem)
#         self.setHorizontalHeaderLabels(sorted(horHeaders))
#
#     def update(self, data):
#         self.data = data
#         self.resizeColumnsToContents()
#         self.resizeRowsToContents()
#         self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
#         self.verticalHeader().setResizeMode(QHeaderView.Stretch)
#         if self.data is not None:
#             self.setmydata()
#
#
# class MyPlugin:
#     def __init__(self, project, plugin_position):
#         self.name = 'Auto seed placer'
#         self.widget = Widget(project)
#
#     def run(self):
#         pass
