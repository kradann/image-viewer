import time
from typing import Union

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QColor
from PyQt5.QtWidgets import QShortcut, QMessageBox, QLabel, QDialog, QAction

from View.FolderSelectionDialog import FolderSelectionDialog
from View.Styles import *
from View.ImageGridView import ImageGridView
from View.FolderListView import FolderListWidget

import subprocess

def get_git_info():
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.STDOUT
        ).decode().strip()

        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.STDOUT
        ).decode().strip()

        return branch, commit

    except Exception:
        return "unknown", "unknown"


class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self, main_model, grid_view_model, folder_list_view_model):
        super().__init__()
        #Customizing main window
        self.setWindowTitle("Image Batch Viewer")
        self.setObjectName("MainWindow")
        self.resize(1600, 900)

        #init main model
        self.main_model = main_model

        #init ViewModels and Views
        self.grid_view_model = grid_view_model
        self.folder_list_view_model = folder_list_view_model
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
        self.folder_list = FolderListWidget(self.main_model, self.grid_view_model, folder_list_view_model=self.folder_list_view_model)

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
        self.move_selected_button, _ = self.add_button("Move Selected Images\n (EU)", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)
        self.check_for_update_button ,_ = self.add_button("Check for Update", self.check_for_update)
        self.check_for_update_button.setEnabled(False)



        # Arrange right side vertically
        self.button_layout_wrapper.addStretch(1)
        self.button_layout_wrapper.addLayout(self.button_panel)
        self.button_layout_wrapper.addStretch(1)
        self.button_layout_wrapper.setAlignment(Qt.AlignCenter)

        # Column spinbox
        self.column_control_layout = QtWidgets.QHBoxLayout()
        self.column_control_layout.setAlignment(Qt.AlignCenter)

        self.column_label = QLabel("Columns: ")
        self.column_label.setStyleSheet(INFO_LABEL_STYLE)

        self.column_spinbox = QtWidgets.QSpinBox()
        self.column_spinbox.setAlignment(Qt.AlignRight)
        self.column_spinbox.setRange(3,10)
        self.column_spinbox.setValue(6)
        self.column_spinbox.valueChanged.connect(lambda value : self.grid_view_model.spinbox_value_changed(value, self.scroll_area.width(), self.grid_view.thumbnail_size[0]))

        self.column_control_layout.addWidget(self.column_label)
        self.column_control_layout.addWidget(self.column_spinbox)
        self.column_control_layout.addStretch(1)

        self.button_layout_wrapper.insertLayout(3, self.column_control_layout)

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
        self.eu_sign_types_widget = None
        self.us_sign_types_widget = None
        self.add_new_labels_widget = None
        self.setup_menubar()

        # === Styling ===
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)
        self.folder_list.setStyleSheet("background-color: #303436; color: white; font-size: 13px;")
        self.current_folder_label.setStyleSheet(INFO_LABEL_STYLE)
        self.info_label.setStyleSheet(INFO_LABEL_STYLE)
        self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)

        # connect signals
        self.folder_list_view_model.update_batch_info.connect(self.update_info_after_list_clicked)
        self.folder_list.itemClicked.connect(self.folder_list_view_model.folder_clicked)
        self.grid_view_model.add_image_to_grid_action.connect(self.on_add_image)
        self.grid_view_model.button_state_changed.connect(self.update_button_state)
        self.grid_view_model.change_current_folder.connect(self.change_current_folder_label)
        self.grid_view_model.info_message.connect(self.change_info_label)
        self.grid_view_model.show_wrong_folder_names_window.connect(self.show_wrong_folder_names)
        self.grid_view_model.not_enough_space.connect(self.show_not_enough_space_message)
        self.grid_view_model.show_folder_selection_dialog.connect(self.show_folder_selection_dialog)

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
        load_json_action.triggered.connect(self.on_load_json)
        file_menu.addAction(load_json_action)

        load_label_json = file_menu.addMenu("Set Sign Types")

        eu_sign_types_action = QtWidgets.QAction("EU Sign Types", self)
        eu_sign_types_action.triggered.connect(self.load_eu_sign_types)
        load_label_json.addAction(eu_sign_types_action)

        us_sign_types_action = QtWidgets.QAction("US Sign Types", self)
        us_sign_types_action.triggered.connect(self.load_us_sign_types)
        load_label_json.addAction(us_sign_types_action)

        add_new_labels_action = QtWidgets.QAction("Add New Labels", self)
        add_new_labels_action.triggered.connect(self.add_new_labels)
        load_label_json.addAction(add_new_labels_action)

        status_menu = self.menu_bar.addMenu("Status")

        load_status_action = QtWidgets.QAction("Load Status", self)
        status_menu.addAction(load_status_action)

        save_status_action = QtWidgets.QAction("Save Status", self)
        status_menu.addAction(save_status_action)

        version_menu = self.menu_bar.addMenu("Version")
        show_version = QAction("Show version info", self)
        show_version.triggered.connect(self.show_version_info)

        version_menu.addAction(show_version)

    def show_version_info(self):
        branch, commit = get_git_info()

        QMessageBox.information(
            self,
            "Version info",
            f"Branch: {branch}\nCommit: {commit}"
        )

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
        self.change_info_label("Loading Folders...", display_time=0)
        self.layout().setEnabled(False)

        selected_folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        self.grid_view.on_load_folder(selected_folder_path)

        self.layout().setEnabled(True)
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

    def on_load_json(self):
        json_data = QtWidgets.QFileDialog.getOpenFileName(self, "Select JSON", filter="JSON files (*.json);;All files (*)")
        self.grid_view.on_load_json(json_data)

    def load_eu_sign_types(self):
        self.grid_view_model.load_eu_sign_types()
        self.move_selected_button.setText("Move Selected Images\n (EU)")
        self.change_info_label("Labels changed to EU traffic signs.")

    def load_us_sign_types(self):
        self.grid_view_model.load_us_sign_types()
        self.move_selected_button.setText("Move Selected Images\n (US)")
        self.change_info_label("Labels changed to US traffic signs.")


    def add_new_labels(self):
        json_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select label JSON", filter="JSON files (*.json);;All files (*)")
        self.grid_view_model.load_labels_from_json(json_file_path)
        self.move_selected_button.setText("Move Selected Images\n (Custom)")
        self.change_info_label("New labels added and set")

    def update_info_after_list_clicked(self):
        self.update_batch_info()
        self.change_info_label("Folder Loaded")

    def update_batch_info(self):
        loader = self.grid_view_model.on_get_loader()
        if loader:
            self.batch_info_label.setText(
                f"Batch: {loader.current_batch_idx + 1} / {loader.number_of_batches // self.grid_view_model.on_get_batch_size() + 1}")


    def change_info_label(self, text=None, display_time=5000):
        label = self.info_label
        label.setText(text)
        # Save the current text
        current_text = text
        if display_time and display_time > 0:
            # After 5 seconds, clear ONLY IF the text hasn't changed in the meantime
            QTimer.singleShot(display_time, lambda: label.setText("") if label.text() == current_text else None)

    def change_current_folder_label(self, folder_name):
        self.current_folder_label.setText("Current folder: " + folder_name)

    def show_wrong_folder_names(self, wrong_folder_names):
        msg = "These are not valid subfolder names:\n" + "\n".join(wrong_folder_names)
        QMessageBox.information(self, "Subfolder name error", msg)

    def show_not_enough_space_message(self, value):
        msg = f"There are not enough space for {value} columns"
        QMessageBox.information(self, "Changing columns warning", msg)
        self.column_spinbox.setValue(value-1)

    def show_folder_selection_dialog(self, preferred_label):
        dialog = FolderSelectionDialog(preferred=preferred_label, grid_view_model=self.grid_view_model)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_folder:
            self.grid_view_model.move_selected(dialog.selected_folder)

    def closeEvent(self, event):
        self.grid_view_model.cleanup_thumbs()
        event.accept()

