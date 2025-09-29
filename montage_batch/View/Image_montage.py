from typing import Union

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut


from View.Old.FolderList import FolderListWidget
from View.Old.ImageGrid import ImageGridWidget

from View.Styles import *
from View.Grid_widget import ImageGridWidget
from View.Folder_list import FolderListWidget
from View.ClickableLabel import ClickableLabel

from ViewModel.FolderListViewModel import FolderListViewModel
from ViewModel.ImageGridViewModel import ImageGridViewModel
from ViewModel.ClickableViewModel import ClickableLabel

from Model.mainmodel import MainModel



class ImageMontageApp(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Image Batch Viewer")
		self.setObjectName("MainWindow")
		self.resize(1600, 900)
		self.thumbnail_size = 150, 150
		self.mainModel = MainModel()
		self.GridViewModel = ImageGridViewModel(self.mainModel)
		self.FolderListViewModel = FolderListViewModel(self.mainModel)
		self.ClickableViewModel = ClickableLabel(self.mainModel)
		#UI setup
		self.batch_info_label = QtWidgets.QLabel("Batch Info", self)

		self.batch_info_label.setAlignment(Qt.AlignCenter)

		self.outer_layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(self.outer_layout)
		# Menu bar
		self.menu_bar = QtWidgets.QMenuBar(self)
		self.outer_layout.setMenuBar(self.menu_bar)

		# Main layouts
		self.main_layout = QtWidgets.QHBoxLayout()
		self.outer_layout.addLayout(self.main_layout)

		# Left Panel
		self.left_panel = QtWidgets.QHBoxLayout()
		# folder list
		self.folder_list = FolderListWidget(self.mainModel)
		file_menu = self.menu_bar.addMenu("File")
		load_folder_action = QtWidgets.QAction("Load Folder", self)
		load_folder_action.triggered.connect(self.mainModel.load_folder)
		file_menu.addAction(load_folder_action)
		load_json_action = QtWidgets.QAction("Load JSON", self)
		#load_json_action.triggered.connect(self.load_json)
		file_menu.addAction(load_json_action)
		status_menu = self.menu_bar.addMenu("Status")
		load_status_action = QtWidgets.QAction("Load Status", self)
		#load_status_action.triggered.connect(self.folder_list.load_status_action)
		status_menu.addAction(load_status_action)

		save_status_action = QtWidgets.QAction("Save Status", self)
		#save_status_action.triggered.connect(self.folder_list.save_status_action)
		status_menu.addAction(save_status_action)


		#self.folder_list.itemClicked.connect(self.folder_clicked)


		# Scroll area (middle panel)
		self.scroll_area = QtWidgets.QScrollArea()
		self.scroll_area.setMinimumWidth(1000)
		self.vertical_value = 0
		self.image_widget = ImageGridWidget(mainmodel=self.mainModel)
		self.image_widget.setMouseTracking(True)
		self.image_layout = QtWidgets.QGridLayout(self.image_widget)
		self.scroll_area.setWidget(self.image_widget)
		self.scroll_area.setWidgetResizable(True)


		self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self.image_widget)
		self.origin = QtCore.QPoint()
		self.drag_selecting = False

		#left panel (contains list of sign types)
		self.left_panel.addWidget(self.folder_list, stretch=1)
		self.left_panel.addWidget(self.scroll_area, stretch=5)

		self.left_widget = QtWidgets.QWidget()
		self.left_widget.setLayout(self.left_panel)
		self.main_layout.addWidget(self.left_widget, stretch=5)

		# Right panel
		self.button_container = QtWidgets.QWidget()
		self.button_layout_wrapper = QtWidgets.QVBoxLayout(self.button_container)
		self.button_panel = QtWidgets.QVBoxLayout()

		# Add stretch before and after the buttons to center vertically
		self.button_layout_wrapper.addStretch(1)
		self.button_layout_wrapper.addLayout(self.button_panel)
		self.button_layout_wrapper.addStretch(1)

		self.main_layout.addWidget(self.button_container, stretch=1)

		# Buttons
		self.add_button("Previous Folder", self.prev_folder)
		self.add_button("Next Folder", self.next_folder)
		self.add_button("Previous Batch", self.previous_batch)
		self.add_button("Next Batch", self.next_batch)
		self.add_button("Current Batch", self.show_batch)
		self.add_button("Unselect/Select all", self.un_select_select_all)
		self.add_button("Selected Check", self.show_only_selected)
		self.move_selected_button, _ = self.add_button("Move Selected Images", self.image_widget.on_load_folder)
		self.add_button("Reload scrolling", self.load_v_value)
		self.add_button("Check for Update", self.check_for_update)

		self.GridViewModel.button_state_changed.connect(self.update_button_state)

		self.label_row_layout = QtWidgets.QHBoxLayout()
		self.current_folder_label = QtWidgets.QLabel("Current Folder")
		self.current_folder_label.setAlignment(Qt.AlignLeft)

		self.info_label = QtWidgets.QLabel("Bottom Info")
		self.info_label.setAlignment(Qt.AlignLeft)

		self.button_layout_wrapper.addWidget(self.batch_info_label)
		self.button_layout_wrapper.addWidget(self.current_folder_label)
		self.label_row_layout.addWidget(self.current_folder_label)
		self.label_row_layout.addWidget(self.info_label)

		self.outer_layout.addLayout(self.label_row_layout)

		#set styles for each sections
		self.setStyleSheet(MAIN_WINDOW_STYLE)
		self.menu_bar.setStyleSheet(MENU_BAR_STYLE)
		self.folder_list.setStyleSheet("background-color: #303436; color: white; font-size: 13px;")
		self.scroll_area.setStyleSheet("background-color: white;")
		self.current_folder_label.setStyleSheet(INFO_LABEL_STYLE)
		self.info_label.setStyleSheet(INFO_LABEL_STYLE)
		self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)



	def add_button(self, name: str, func, shortcut: Union[str, tuple] = None):
		button = QtWidgets.QPushButton(name)
		button.setFont(QFont("Arial", 10))
		button.setFixedSize(160, 40)
		button.setStyleSheet(BUTTON_STYLE)
		self.button_panel.addWidget(button)
		button.clicked.connect(func)

		q_shortcut = None
		if shortcut is not None:
			if isinstance(shortcut, tuple):
				for s in shortcut:
					q_shortcut = QShortcut(QKeySequence(s), self)
					q_shortcut.activated.connect(func)
			else:
				q_shortcut = QShortcut(QKeySequence(shortcut), self)
				q_shortcut.activated.connect(func)
		return button, q_shortcut

	def update_button_state(self, enabled: bool):
		if enabled:
			self.move_selected_button.setEnabled(True)
			self.move_selected_button.setStyleSheet("color: black; background-color: green;")
		else:
			self.move_selected_button.setEnabled(False)
			self.move_selected_button.setStyleSheet("color: black; background-color: #8B0000;")

	def prev_folder(self):
		pass

	def next_folder(self):
		pass
	def previous_batch(self):
		pass
	def next_batch(self):
		pass
	def show_batch(self):
		pass
	def un_select_select_all(self):
		pass
	def show_only_selected(self):
		pass
	def move_selected(self):
		pass
	def load_v_value(self):
		pass
	def check_for_update(self):
		pass
