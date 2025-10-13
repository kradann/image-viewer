from typing import Union

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut

from View.Styles import *
from View.ImageGridView import ImageGridView
from View.FolderListView import FolderListWidget
from View.ClickableLabel import ClickableLabel

from ViewModel.FolderListViewModel import FolderListViewModel
from ViewModel.ImageGridViewModel import ImageGridViewModel
from ViewModel.ClickableViewModel import ClickableLabel

from Model.MainModel import MainModel
from Model.BatchLoaderModel import ImageBatchLoader



class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        #Customizing main window
        self.setWindowTitle("Image Batch Viewer")
        self.setObjectName("MainWindow")
        self.resize(1600, 900)

        #init main model
        self.mainModel = MainModel()

        #init ViewModels and Views
        self.FolderListViewModel = FolderListViewModel(self.mainModel)
        self.GridViewModel = ImageGridViewModel(self.mainModel)
        self.GridView = ImageGridView(parent=self, mainmodel=self.mainModel, GridViewModel=self.GridViewModel)
        self.GridView.setMouseTracking(True)

        #init layout
        self.main_layout = QtWidgets.QHBoxLayout()

        self.outer_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.outer_layout)

        # Left panel (folder list)
        self.left_panel = QtWidgets.QHBoxLayout()

        # Contains folder list and current folder label
        self.label_row_layout = QtWidgets.QHBoxLayout()

        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setLayout(self.left_panel)

        # Middle panel
        self.scroll_area = QtWidgets.QScrollArea()

        # Grid that displays images
        self.image_layout = QtWidgets.QGridLayout(self.GridView)

        # Init folder list
        self.folder_list = FolderListWidget(self.mainModel, self.GridViewModel)


        #Button container
        self.button_container = QtWidgets.QWidget()
        self.button_layout_wrapper = QtWidgets.QVBoxLayout(self.button_container)
        self.button_panel = QtWidgets.QVBoxLayout()

        #Labels
        self.current_folder_label = QtWidgets.QLabel("Current Folder")

        self.batch_info_label = QtWidgets.QLabel("Batch Info", self)
        self.info_label = QtWidgets.QLabel("Bottom Info")


        # Menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.outer_layout.setMenuBar(self.menu_bar)

        # Connect menu items to functions
        self.setup_menubar()

        # Scroll area
        self.scroll_area.setMinimumWidth(1000)
        self.vertical_value = 0

        self.scroll_area.setWidget(self.GridView)
        self.scroll_area.setWidgetResizable(True)

        # Buttons
        self.add_button("Previous Folder", self.prev_folder)
        self.add_button("Next Folder", self.next_folder)
        self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Unselect/Select all", self.un_select_select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.move_selected_button, _ = self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)
        self.add_button("Check for Update", self.check_for_update)

        # set alignments
        self.image_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.scroll_area.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.batch_info_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        self.label_row_layout.setAlignment(Qt.AlignLeft)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.current_folder_label.setFixedWidth(400)
        self.info_label.setFixedWidth(self.GridView.width())


        self.main_layout.addWidget(self.left_widget, stretch=5)
        self.main_layout.addWidget(self.button_container, stretch=1)

        # left panel (contains list of sign types)
        self.left_panel.addWidget(self.folder_list, stretch=1)
        self.left_panel.addWidget(self.scroll_area, stretch=5)


        # connect signals
        self.FolderListViewModel.updateInfo.connect(self.update_info_after_list_clicked)
        self.folder_list.itemClicked.connect(self.FolderListViewModel.folder_clicked)
        self.GridViewModel.AddImage.connect(self.on_add_image)
        self.GridViewModel.button_state_changed.connect(self.update_button_state)

        # set styles for each sections
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)
        self.folder_list.setStyleSheet("background-color: #303436; color: white; font-size: 13px;")
        self.scroll_area.setStyleSheet("background-color: white;")
        self.current_folder_label.setStyleSheet(INFO_LABEL_STYLE)
        self.info_label.setStyleSheet(INFO_LABEL_STYLE)
        self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)


        self.button_layout_wrapper.addStretch(1)
        self.button_layout_wrapper.addLayout(self.button_panel)
        self.button_layout_wrapper.addStretch(1)
        self.outer_layout.addLayout(self.main_layout)
        self.outer_layout.addLayout(self.label_row_layout)

        self.label_row_layout.addWidget(self.current_folder_label)
        self.label_row_layout.addWidget(self.info_label)
        self.button_layout_wrapper.addWidget(self.batch_info_label)




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

    def setup_menubar(self):
        file_menu = self.menu_bar.addMenu("File")

        load_folder_action = QtWidgets.QAction("Load Folder", self)
        load_folder_action.triggered.connect(self.on_load_folder)
        file_menu.addAction(load_folder_action)

        load_json_action = QtWidgets.QAction("Load JSON", self)
        file_menu.addAction(load_json_action)

        status_menu = self.menu_bar.addMenu("Status")

        load_status_action = QtWidgets.QAction("Load Status", self)
        status_menu.addAction(load_status_action)

        save_status_action = QtWidgets.QAction("Save Status", self)
        status_menu.addAction(save_status_action)

    def update_button_state(self, enabled: bool):
        if enabled:
            self.move_selected_button.setEnabled(True)
            self.move_selected_button.setStyleSheet("color: black; background-color: green;")
        else:
            self.move_selected_button.setEnabled(False)
            self.move_selected_button.setStyleSheet("color: black; background-color: #8B0000;")

    def on_add_image(self, click, row, col):
        self.image_layout.addWidget(click, row, col)

    def prev_folder(self):
        self.GridViewModel.on_prev_folder()
        self.change_info_label("Previous Folder Loaded")
        self.update_batch_info()

    def next_folder(self):
        self.GridViewModel.on_next_folder()
        self.change_info_label("Next Folder Loaded")
        self.update_batch_info()

    def previous_batch(self):
        self.GridViewModel.on_prev_batch()
        self.change_info_label("Previous Batch Loaded")
        self.update_batch_info()

    def next_batch(self):
        self.GridViewModel.on_next_batch()
        self.change_info_label("Next Batch Loaded")
        self.update_batch_info()

    def show_batch(self):
        self.GridView.show_batch()

    def un_select_select_all(self):
        self.GridViewModel.on_unselect_select_all()
    def show_only_selected(self):
        self.GridViewModel.on_show_only_selected()
    def move_selected(self):
        self.GridViewModel.on_move_selected()
    def load_v_value(self):
        self.scroll_area.verticalScrollBar().setValue(self.vertical_value)
    def check_for_update(self):
        self.GridViewModel.on_check_for_update()

    def on_load_folder(self):
        self.GridView.on_load_folder()
        self.change_info_label("Folder Loaded")
        self.update_batch_info()


    def update_info_after_list_clicked(self):
        self.update_batch_info()
        self.change_info_label("Folder Loaded")

    def update_batch_info(self):
        self.batch_info_label.setText(f"Batch: {self.mainModel.loader.current_batch_idx + 1} / {self.mainModel.loader.number_of_batches // 1000 + 1}")

    def change_info_label(self, text=None, text_color="#3cfb8b"):
        label = self.info_label
        label.setText(text)
        if text_color:
            label.setStyleSheet(f"color: {text_color}; font-size: 20px;")
        # Save the current text
        current_text = text
        # After 5 seconds, clear ONLY IF the text hasn't changed in the meantime
        QTimer.singleShot(5000, lambda: label.setText("") if label.text() == current_text else None)

    def closeEvent(self, event):
        print(11)
        self.GridViewModel.cleanup_thumbs()
        event.accept()

