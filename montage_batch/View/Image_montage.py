import time
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
        self.main_model = MainModel()

        #init ViewModels and Views
        self.folder_list_view_model = FolderListViewModel(self.main_model)
        self.grid_view_model = ImageGridViewModel(self.main_model)
        self.grid_view = ImageGridView(parent=self, main_model=self.main_model, grid_view_model=self.grid_view_model)
        self.grid_view.setMouseTracking(True)

        # === Main Layout ===
        self.outer_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.outer_layout)
        self.main_layout = QtWidgets.QHBoxLayout() # left | middle | right
        self.outer_layout.addLayout(self.main_layout)

        # === Left Panel ===
        self.left_panel = QtWidgets.QVBoxLayout()
        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setMaximumWidth(430)
        self.left_widget.setLayout(self.left_panel)

        # Init folder list
        self.folder_list = FolderListWidget(self.main_model, self.grid_view_model)

        # Current folder label (below folder list)
        self.current_folder_label = QtWidgets.QLabel("Current Folder")

        # Add to left panel
        self.left_panel.addWidget(self.folder_list, stretch=9)
        self.left_panel.addWidget(self.current_folder_label, stretch=1)

        # === Middle Panel ===
        self.middle_panel = QtWidgets.QVBoxLayout()
        self.image_layout = QtWidgets.QGridLayout(self.grid_view)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setMinimumWidth(1000)
        self.scroll_area.setWidget(self.grid_view)
        self.scroll_area.setWidgetResizable(True)
        self.vertical_value = 0 # Position on vertical axes
        self.image_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)

        # Info Label (below grid)
        self.info_label = QtWidgets.QLabel("Bottom Info")
        self.info_label.setAlignment(Qt.AlignCenter)

        # Add scroll_area and info label to middle panel
        self.middle_panel.addWidget(self.scroll_area, stretch=8)
        self.middle_panel.addWidget(self.info_label, stretch=1)

        # === Right Panel ===
        self.right_panel = QtWidgets.QVBoxLayout()
        self.button_container = QtWidgets.QWidget()
        self.button_layout_wrapper = QtWidgets.QVBoxLayout(self.button_container)
        self.button_panel = QtWidgets.QVBoxLayout()

        # Add buttons
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



        # Arrange right side vertically
        self.button_layout_wrapper.addStretch(1)
        self.button_layout_wrapper.addLayout(self.button_panel)
        self.button_layout_wrapper.addStretch(1)
        self.button_layout_wrapper.setAlignment(Qt.AlignCenter)

        # Batch info label
        self.batch_info_label = QtWidgets.QLabel("Batch Info", self)
        self.batch_info_label.setAlignment(Qt.AlignCenter)

        #Add buttons and batch info label to right side panel
        self.right_panel.addWidget(self.button_container, stretch=8)
        self.right_panel.addWidget(self.batch_info_label, stretch=1)

        # === Combine Panels ===
        self.main_layout.addWidget(self.left_widget, stretch=2)
        self.main_layout.addLayout(self.middle_panel, stretch=6)
        self.main_layout.addLayout(self.right_panel, stretch=1)

        # === Menu Bar ===
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.outer_layout.setMenuBar(self.menu_bar)
        self.setup_menubar()

        # === Styling ===
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)
        self.folder_list.setStyleSheet("background-color: #303436; color: white; font-size: 13px;")
        self.current_folder_label.setStyleSheet(INFO_LABEL_STYLE)
        self.info_label.setStyleSheet(INFO_LABEL_STYLE)
        self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)

        # connect signals
        self.folder_list_view_model.update_info.connect(self.update_info_after_list_clicked)
        self.folder_list.itemClicked.connect(self.folder_list_view_model.folder_clicked)
        self.grid_view_model.add_image_to_grid_action.connect(self.on_add_image)
        self.grid_view_model.button_state_changed.connect(self.update_button_state)
        self.grid_view_model.change_current_folder.connect(self.change_current_folder_label)
        self.grid_view_model.info_message.connect(self.change_info_label)

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
        self.grid_view_model.on_prev_folder()
        self.change_info_label("Previous Folder Loaded")
        self.update_batch_info()

    def next_folder(self):
        self.grid_view_model.on_next_folder()
        self.change_info_label("Next Folder Loaded")
        self.update_batch_info()

    def previous_batch(self):
        self.grid_view_model.on_prev_batch()
        self.change_info_label("Previous Batch Loaded")
        self.update_batch_info()

    def next_batch(self):
        self.grid_view_model.on_next_batch()
        self.change_info_label("Next Batch Loaded")
        self.update_batch_info()

    def show_batch(self):
        self.grid_view.show_batch()

    def un_select_select_all(self):
        self.grid_view_model.on_unselect_select_all()

    def show_only_selected(self):
        self.grid_view_model.on_show_only_selected()

    def move_selected(self):
        self.vertical_value = self.scroll_area.verticalScrollBar().value()
        self.grid_view_model.on_move_selected()

    def load_v_value(self):
        self.scroll_area.verticalScrollBar().setValue(self.vertical_value)

    def check_for_update(self):
        self.grid_view_model.on_check_for_update()

    def on_load_folder(self):
        self.change_info_label("Loading Folders...", time=0)
        self.grid_view.on_load_folder()
        self.change_info_label("Folders Loaded")
        self.update_batch_info()
        #commented because it's easier to debug
        '''
        try:
            self.change_info_label("Loading Folders...", time=0)
            self.GridView.on_load_folder()
            self.change_info_label("Folder Loaded")
            self.update_batch_info()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Folder Load Error",
                f"An error occurred while loading the folder: \n\n{e} \n\nMake sure you are selecting the correct folder!",
            )

            self.change_info_label("Folder load failed")
        '''


    def update_info_after_list_clicked(self):
        self.update_batch_info()
        self.change_info_label("Folder Loaded")

    def update_batch_info(self):
        if self.main_model.loader:
            self.batch_info_label.setText(f"Batch: {self.main_model.loader.current_batch_idx + 1} / {self.main_model.loader.number_of_batches // 1000 + 1}")

    def change_info_label(self, text=None, text_color="#3cfb8b", time=5000):

        label = self.info_label
        label.setText(text)
        # Save the current text
        current_text = text
        if time and time > 0:
            # After 5 seconds, clear ONLY IF the text hasn't changed in the meantime
            QTimer.singleShot(time, lambda: label.setText("") if label.text() == current_text else None)

    def change_current_folder_label(self, folder_name):
        self.current_folder_label.setText("Current folder: " + folder_name)

    def closeEvent(self, event):
        print(11)
        self.grid_view_model.cleanup_thumbs()
        event.accept()

