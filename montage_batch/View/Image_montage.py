from typing import Union

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut
from View.Old.FolderList import FolderListWidget
from View.Old.ImageGrid import ImageGridWidget
from View.Styles import *


class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Batch Viewer")
        self.setObjectName("MainWindow")
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.resize(1600, 900)
        self.num_of_col = 6
        self.batch_size = 1000
        self.thumbnail_size = 150, 150

        self.loader = None
        self.folder_path = None
        self.main_folder = None  # Folder that stores the subfolders
        self.first_check = True
        self.is_all_region = False  # user load multiple regions
        self.image_paths = None  # used when multiple regions
        self.regions = None # list regions in folder
        self.base_folder = None  # Only use for JSON
        self.thread = None
        self.isAllSelected = False
        self.subfolders = None # list of subfolders
        self.labels = list()
        self.selected_images = set()
        self.dropped_selected = set()
        self.batch_info_label = QtWidgets.QLabel("Batch Info")
        self.json = None
        self.json_data = None
        self.is_JSON_active = False
        self.timer = QtCore.QTimer(self)
        #self.timer.timeout.connect(self.update_selected_check_button)
        self.timer.start(500)

        self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)
        self.batch_info_label.setAlignment(Qt.AlignCenter)

        self.outer_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.outer_layout)

        self.menu_bar = QtWidgets.QMenuBar(self)
        self.outer_layout.setMenuBar(self.menu_bar)

        # Main layouts
        self.main_layout = QtWidgets.QHBoxLayout()
        self.outer_layout.addLayout(self.main_layout)

        # Left Panel
        self.left_panel = QtWidgets.QHBoxLayout()

        self.folder_list = FolderListWidget()
        file_menu = self.menu_bar.addMenu("File")
        load_folder_action = QtWidgets.QAction("Load Folder", self)
        #load_folder_action.triggered.connect(self.load_folder)
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

        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)

        self.folder_list.setMinimumWidth(400)
        #self.folder_list.itemClicked.connect(self.folder_clicked)
        self.folder_list.setStyleSheet("background-color: #303436; color: white; font-size: 13px;")

        # Scroll area (middle panel)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setMinimumWidth(1000)
        self.vertical_value = 0
        self.image_widget = ImageGridWidget(self)
        self.image_widget.setMouseTracking(True)
        self.image_layout = QtWidgets.QGridLayout(self.image_widget)
        self.scroll_area.setWidget(self.image_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: white;")

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
        '''self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Unselect/Select all", self.un_select_select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.move_selected_button, _ = self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)
        self.add_button("Check for Update", self.check_for_update)'''

        self.button_layout_wrapper.addWidget(self.batch_info_label)

        self.label_row_layout = QtWidgets.QHBoxLayout()

        self.current_folder_label = QtWidgets.QLabel("Current Folder")
        self.current_folder_label.setAlignment(Qt.AlignLeft)
        self.button_layout_wrapper.addWidget(self.current_folder_label)
        self.current_folder_label.setStyleSheet(INFO_LABEL_STYLE)
        self.label_row_layout.addWidget(self.current_folder_label)

        self.info_label = QtWidgets.QLabel("Bottom Info")
        self.info_label.setAlignment(Qt.AlignLeft)
        self.info_label.setStyleSheet(INFO_LABEL_STYLE)
        self.label_row_layout.addWidget(self.info_label)

        self.outer_layout.addLayout(self.label_row_layout)

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

    def prev_folder(self):
        pass

    def next_folder(self):
        pass