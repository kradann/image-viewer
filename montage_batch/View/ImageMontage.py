import logging
from typing import Union

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QKeySequence, QColor
from PyQt5.QtWidgets import QShortcut, QMessageBox, QLabel, QDialog, QAction, QHBoxLayout, QWidget, QVBoxLayout, \
    QSplitter

from View.FolderSelectionDialog import FolderSelectionDialog
from View.Styles import *
from View.ImageGridView import ImageGridView
from View.FolderListView import FolderListWidget
from View.LogWindow import LogWindow
from View.NotFoundImageWindow import NotFoundImageWindow
from View.LastMoveWindow import LastMoveWindow

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
        #self.left_widget.setMaximumWidth(430)
        self.left_widget.setMinimumWidth(30)
        self.left_widget.setLayout(self.left_panel)

        # Init folder list
        self.folder_list = FolderListWidget(self.main_model, self.grid_view_model, folder_list_view_model=self.folder_list_view_model)

        # Current folder label (below folder list)
        self.current_folder_label = QtWidgets.QLabel("Current Folder")

        # Add to left panel
        self.left_panel.addWidget(self.folder_list, stretch=1)
        #self.left_panel.addWidget(self.current_folder_label, stretch=1)

        # === Middle Panel ===
        self.middle_panel = QtWidgets.QVBoxLayout()
        self.image_layout = QtWidgets.QGridLayout(self.grid_view)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.grid_view)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumWidth(520)

        self.scroll_area.resizeEvent = self.on_scroll_area_resized

        self.vertical_value = 0 # Position on vertical axes
        self.image_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)

        # Info Label (below grid)
        self.info_label = QtWidgets.QLabel("Bottom Info")
        self.info_label.setAlignment(Qt.AlignCenter)

        # Add scroll_area and info label to middle panel
        self.middle_panel.addWidget(self.scroll_area)
        #self.middle_panel.addWidget(self.info_label, stretch=1)

        # === Right Panel ===
        # === Right Panel ===
        self.right_panel = QVBoxLayout()
        self.button_container = QWidget()
        self.button_layout_wrapper = QVBoxLayout(self.button_container)
        self.button_panel = QVBoxLayout()
        self.button_panel.setAlignment(Qt.AlignCenter)

        # --- NAVIGATION KONTAINER ---
        self.top_buttons_container = QWidget()
        self.top_buttons_container_layout = QVBoxLayout(self.top_buttons_container)
        self.top_buttons_container_layout.setAlignment(Qt.AlignCenter)
        self.top_buttons_container_layout.setSpacing(10)

        self.top_buttons_label = QLabel("Navigation")
        self.top_buttons_label.setAlignment(Qt.AlignCenter)
        self.top_buttons_label.setStyleSheet(
            "color: white; font-size: 14px; background-color: transparent;"
        )
        self.top_buttons_container_layout.addWidget(self.top_buttons_label)

        self.top_buttons_container.setStyleSheet(
            "background-color: rgba(64, 64, 64, 153); border-radius: 5px;"
        )

        # 1. sor: Previous / Next Folder
        nav_row_1 = QHBoxLayout()
        prev_folder_button, _ = self.add_button(
            "Previous\nFolder", self.prev_folder, size=(70, 90)
        )
        next_folder_button, _ = self.add_button(
            "Next\nFolder",
            self.next_folder,
            size=(70, 90),
            background_color="rgba(59, 170, 59, 200)",
            text_color="black",
        )
        nav_row_1.addWidget(prev_folder_button)
        nav_row_1.addWidget(next_folder_button)
        self.top_buttons_container_layout.addLayout(nav_row_1)

        # 2. sor: < Batch >
        nav_row_2 = QHBoxLayout()
        prev_batch_button, _ = self.add_button("<", self.previous_batch, size=(40, 40))
        prev_batch_button.setStyleSheet(ARROW_BUTTON_STYLE)
        self.batch_info_label = QLabel("Batch", self)
        self.batch_info_label.setAlignment(Qt.AlignCenter)
        next_batch_button, _ = self.add_button(">", self.next_batch, size=(40, 40))
        next_batch_button.setStyleSheet(ARROW_BUTTON_STYLE)
        nav_row_2.addWidget(prev_batch_button)
        nav_row_2.addWidget(self.batch_info_label)
        nav_row_2.addWidget(next_batch_button)
        self.top_buttons_container_layout.addLayout(nav_row_2)

        # 3. sor: Current Batch (NAVIGATION BENN)
        nav_row_3 = QHBoxLayout()
        current_batch_button, _ = self.add_button(
            "Current Batch", self.show_batch, size=(140, 40)
        )
        nav_row_3.addWidget(current_batch_button)
        self.top_buttons_container_layout.addLayout(nav_row_3)

        # Navigation blokk megy a fő button_panel-be
        self.button_panel.addWidget(self.top_buttons_container)
        self.button_panel.addSpacing(20)

        # --- SELECTION KONTAINER (Navigation mintájára) ---
        self.selection_container = QWidget()
        self.selection_container_layout = QVBoxLayout(self.selection_container)
        self.selection_container_layout.setAlignment(Qt.AlignCenter)
        self.selection_container_layout.setSpacing(10)

        self.selection_label = QLabel("Selection")
        self.selection_label.setAlignment(Qt.AlignCenter)
        self.selection_label.setStyleSheet(
            "color: white; font-size: 14px; background-color: transparent;"
        )
        self.selection_container_layout.addWidget(self.selection_label)

        # háttér, hasonló a Navigation-hoz
        self.selection_container.setStyleSheet(
            "background-color: rgba(64, 64, 64, 153); border-radius: 5px;"
        )

        # sor: Unselect / Select all
        selection_row = QHBoxLayout()
        unselect_button, _ = self.add_button(
            "Unselect\nall", self.un_select_all, size=(70, 90)
        )
        select_all_button, _ = self.add_button(
            "Select\nall", self.select_all, size=(70, 90),
            background_color="rgba(59, 170, 59, 200)",  # opcionális zöld
            text_color="black",
        )
        selection_row.addWidget(unselect_button)
        selection_row.addWidget(select_all_button)
        self.selection_container_layout.addLayout(selection_row)

        # Selection blokk a fő button_panel-be
        self.button_panel.addWidget(self.selection_container)
        self.button_panel.addSpacing(20)

        # --- SELECTED KONTAINER (Selected Check + Move) ---
        self.selected_container = QWidget()
        self.selected_container_layout = QVBoxLayout(self.selected_container)
        self.selected_container_layout.setAlignment(Qt.AlignCenter)
        self.selected_container_layout.setSpacing(10)

        self.selected_label = QLabel("Moving")
        self.selected_label.setAlignment(Qt.AlignCenter)
        self.selected_label.setStyleSheet(
            "color: white; font-size: 14px; background-color: transparent;"
        )
        self.selected_container_layout.addWidget(self.selected_label)

        # háttér, hasonló a Navigation/Selection-hoz
        self.selected_container.setStyleSheet(
            "background-color: rgba(64, 64, 64, 153); border-radius: 5px;"
        )

        # sor: Selected Check / Move Selected
        selected_row = QHBoxLayout()
        selected_check_button, _ = self.add_button(
            "Selected\nCheck", self.show_only_selected, size=(70, 90)
        )
        self.move_selected_button, _ = self.add_button(
            "Move\nSelected", self.move_selected, size=(70, 90),
            background_color="rgba(59, 170, 59, 200)",
            text_color="black",
        )
        selected_row.addWidget(selected_check_button)
        selected_row.addWidget(self.move_selected_button)
        self.selected_container_layout.addLayout(selected_row)

        # Selected blokk a fő button_panel-be
        self.button_panel.addWidget(self.selected_container)
        self.button_panel.addSpacing(20)

        # --- OTHER KONTAINER (Reload + Undo) ---
        self.other_container = QWidget()
        self.other_container_layout = QVBoxLayout(self.other_container)
        self.other_container_layout.setAlignment(Qt.AlignCenter)
        self.other_container_layout.setSpacing(10)

        self.other_label = QLabel("Other")
        self.other_label.setAlignment(Qt.AlignCenter)
        self.other_label.setStyleSheet(
            "color: white; font-size: 14px; background-color: transparent;"
        )
        self.other_container_layout.addWidget(self.other_label)

        # háttér, hasonló a többi blokkhoz
        self.other_container.setStyleSheet(
            "background-color: rgba(64, 64, 64, 153); border-radius: 5px;"
        )

        # sor: Reload / Undo
        other_row = QHBoxLayout()
        reload_scrolling_button, _ = self.add_button(
            "Reload\nscrolling", self.load_v_value, size=(70, 90)
        )
        undo_button, _ = self.add_button(
            "Undo", self.undo, size=(70, 90)
        )
        other_row.addWidget(reload_scrolling_button)
        other_row.addWidget(undo_button)
        self.other_container_layout.addLayout(other_row)

        # Other blokk a fő button_panel-be
        self.button_panel.addWidget(self.other_container)
        self.button_panel.addSpacing(20)
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
        self.column_label.setAlignment(Qt.AlignLeft)

        self.column_spinbox = QtWidgets.QSpinBox()
        self.column_spinbox.setAlignment(Qt.AlignRight)
        self.column_spinbox.setRange(3,10)
        self.column_spinbox.setValue(6)
        self.column_spinbox.valueChanged.connect(lambda value : self.grid_view_model.spinbox_value_changed(value, self.scroll_area.width(), self.grid_view.thumbnail_size[0]))

        self.column_control_layout.addWidget(self.column_label)
        self.column_control_layout.addWidget(self.column_spinbox)
        self.column_control_layout.setAlignment(Qt.AlignCenter)
        #self.button_layout_wrapper.insertLayout(3, self.column_control_layout)

        # Batch info label
        #self.batch_info_label = QtWidgets.QLabel("Batch Info", self)
        self.batch_info_label.setAlignment(Qt.AlignCenter)

        #Add buttons and batch info label to right side panel
        self.right_panel.addWidget(self.button_container)


        # === Combine Panels ===
        middle_widget = QtWidgets.QWidget()
        middle_widget.setLayout(self.middle_panel)
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(self.right_panel)
        right_widget.setMinimumWidth(200)

        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(middle_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setStretchFactor(2,2)
        self.splitter.setSizes([300,1075,225])
        #self.main_layout.addWidget(self.left_widget, stretch=2)
        #self.main_layout.addLayout(self.middle_panel, stretch=15)
        #self.main_layout.addLayout(self.right_panel, stretch=1)

        self.outer_layout.addWidget(self.splitter)

        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(10,5,10,10)
        self.bottom_bar.setSpacing(20)
        self.bottom_bar.setAlignment(Qt.AlignCenter)

        self.bottom_bar.addWidget(self.current_folder_label, stretch=1, alignment=Qt.AlignLeft)
        self.bottom_bar.addWidget(self.info_label, stretch=2, alignment=Qt.AlignCenter)
        self.bottom_bar.addLayout(self.column_control_layout, stretch=1)

        self.bottom_widget = QWidget()
        self.bottom_widget.setLayout(self.bottom_bar)

        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.splitter)
        self.main_splitter.addWidget(self.bottom_widget)

        self.main_splitter.setStretchFactor(0,1)
        self.main_splitter.setStretchFactor(1,0)

        self.outer_layout.addWidget(self.main_splitter)

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
        self.main_model.show_message.connect(self.on_show_message)
        self.folder_list_view_model.update_batch_info.connect(self.update_info_after_list_clicked)
        self.folder_list.itemClicked.connect(self.folder_list_view_model.folder_clicked)
        self.grid_view_model.add_image_to_grid_action.connect(self.on_add_image)
        self.grid_view_model.button_state_changed.connect(self.update_button_state)
        self.grid_view_model.change_current_folder.connect(self.change_current_folder_label)
        self.grid_view_model.info_message.connect(self.change_info_label)
        self.grid_view_model.show_wrong_folder_names_window.connect(self.show_wrong_folder_names)
        self.grid_view_model.not_enough_space.connect(self.show_not_enough_space_message)
        self.grid_view_model.show_folder_selection_dialog.connect(self.show_folder_selection_dialog)
        self.grid_view_model.load_finished_signal.connect(self.on_load_finished)
        self.grid_view_model.show_not_found_images.connect(self.show_not_found_images_info)
        self.grid_view_model.show_last_move_window.connect(self.show_last_move_window)

        # Create log folder if doesn't exists
        self.grid_view_model.create_log_folder()
        self.grid_view_model.create_log_file()

        #Create variables for pop up windows
        self.log_window = None
        self.not_found_images_window = None
        self.last_move_window = None

    def add_button(self, name: str, func, shortcut: Union[str, tuple] = None, size : tuple[int,int] = (160,40), background_color : str = None, text_color : str = None):
        button = QtWidgets.QPushButton(name)
        button.setFont(QFont("Arial", 10))
        button.setFixedSize(size[0], size[1])
        style_parts = [BUTTON_STYLE]
        if background_color:
            style_parts.append(f"background-color: {background_color};")

        if text_color:
            style_parts.append(f"color: {text_color}")

        button.setStyleSheet("".join(style_parts))
        if size == (160,40):
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

        directory_tree = file_menu.addMenu("Directory Tree")

        import_directory_tree = QtWidgets.QAction("Import", self)
        import_directory_tree.triggered.connect(self.on_import_dir_tree)
        directory_tree.addAction(import_directory_tree)

        export_directory_tree = QtWidgets.QAction("Export", self)
        export_directory_tree.triggered.connect(self.on_export_dir_tree)
        directory_tree.addAction(export_directory_tree)

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

        check_for_update = QAction("Check for update", self)
        check_for_update.triggered.connect(self.check_for_update)
        version_menu.addAction(check_for_update)

        log_menu = self.menu_bar.addMenu("Log")
        show_log_action = QAction("Show Log", self)
        show_log_action.triggered.connect(self.show_log)
        log_menu.addAction(show_log_action)

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

    def on_scroll_area_resized(self, event):
        QtWidgets.QScrollArea.resizeEvent(self.scroll_area, event)

        current_cols = self.column_spinbox.value()
        scroll_w = self.scroll_area.width()
        thumb_w = self.grid_view.thumbnail_size[0]

        max_cols = self.column_spinbox.maximum()
        min_cols = self.column_spinbox.minimum()

        def fits(cols):
            return (scroll_w - (cols + 2) * cols) // thumb_w >= cols

        new_cols = current_cols

        while new_cols < max_cols and fits(new_cols + 1):
            new_cols += 1

        if not fits(new_cols):
            while new_cols > min_cols and not fits(new_cols):
                new_cols -= 1

        if new_cols != current_cols:
            self.column_spinbox.setValue(new_cols)

    def prev_folder(self):
        try:
            self.change_info_label("Previous Folder Loading...", display_time=0)
            self.grid_view_model.on_prev_folder()
            self.change_info_label("Previous Folder Loaded")
            self.update_batch_info()
        except Exception as e:
            logging.error(f"Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Folder Load Error",
                f"An error occurred while loading the previous folder: \n\n{e}",
            )

    def next_folder(self):
        try:
            self.change_info_label("Next Folder Loading...", display_time=0)
            self.grid_view_model.on_next_folder()
            self.change_info_label("Next Folder Loaded")
            self.update_batch_info()
        except Exception as e:
            logging.error(f"Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Folder Load Error",
                f"An error occurred while loading the next folder: \n\n{e}",
            )

    def previous_batch(self):
        try:
            self.change_info_label("Previous Batch Loading...", display_time=0)
            self.grid_view_model.on_prev_batch()
            self.change_info_label("Previous Batch Loaded")
            self.update_batch_info()
        except Exception as e:
            logging.error(f"Previous Batch Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Previous Batch Error",
                f"An error occurred while loading the previous batch: \n\n{e}",
            )

    def next_batch(self):
        try:
            self.change_info_label("Next Batch Loading...", display_time=0)
            self.grid_view_model.on_next_batch()
            self.change_info_label("Next Batch Loaded")
            self.update_batch_info()
        except Exception as e:
            logging.error(f"Next Batch Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Next Batch Error",
                f"An error occurred while loading the next batch: \n\n{e}",
            )

    def show_batch(self):
        try:
            self.change_info_label("Current Batch Loading...", display_time=0)
            self.grid_view.show_batch()
            self.change_info_label("Current Batch Loaded")
        except Exception as e:
            logging.error(f"Show Batch Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Show Batch Error",
                f"An error occurred while loading the current batch: \n\n{e}",
            )

    def un_select_all(self):
        try:
            self.grid_view_model.on_un_select_all()
        except Exception as e:
            logging.error(f"Image Selecting Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Image Selecting Error",
                f"An error occurred while selecting or unselecting images: \n\n{e}",
            )

    def select_all(self):
        try:
            self.grid_view_model.on_select_all()
        except Exception as e:
            logging.error(f"Image Selecting Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Image Selecting Error",
                f"An error occurred while selecting or unselecting images: \n\n{e}",
            )

    def show_only_selected(self):
        try:
            self.vertical_value = self.scroll_area.verticalScrollBar().value()
            self.grid_view_model.on_show_only_selected()
        except Exception as e:
            logging.error(f"Show Only Selected Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Show Only Selected Error",
                f"An error occurred while loading selected images: \n\n{e}",
            )

    def move_selected(self):
        try:
            if self.vertical_value == 0:
                self.vertical_value = self.scroll_area.verticalScrollBar().value()
            self.grid_view_model.on_move_selected()
            self.grid_view_model.reload_current_label()

        except Exception as e:
            logging.error(f"Image moving Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Image moving Error",
                f"An error occurred while trying to move images: \n\n{e}",
            )

    def load_v_value(self):
        print(self.vertical_value)
        if self.vertical_value != 0 : self.scroll_area.verticalScrollBar().setValue(self.vertical_value)
        self.vertical_value = 0

    def check_for_update(self):
        self.grid_view_model.on_check_for_update()

    def show_log(self):
        try:
            self.log_window = LogWindow(self.grid_view_model.get_log_file_path())
            self.log_window.show()
        except Exception as e:
            logging.error(f"Log Window Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Log Window Error",
                f"An error occurred while loading log window: \n\n{e}",
            )

    def undo(self):
        try:
            self.grid_view_model.get_last_move()
        except Exception as e:
            logging.error(f"Undo Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Undo Error",
                f"An error occurred while undo last move: \n\n{e}",
            )

    def on_load_folder(self):
        try:
            self.change_info_label("Loading Folders...", display_time=0)
            #self.layout().setEnabled(False)
            selected_folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
            self.grid_view.on_load_folder(selected_folder_path)
            #self.layout().setEnabled(True)
        except Exception as e:
            logging.error(f"Folder Load Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Folder Load Error",
                f"An error occurred while loading the folder: \n\n{e} \n\nMake sure you are selecting the correct folder!",
            )

            self.change_info_label("Folder load failed")


    def on_load_finished(self):
        self.change_info_label("Folder Loaded")
        QTimer.singleShot(100,self.load_v_value)
        self.update_batch_info()

    def on_load_json(self):
        try:
            json_data = QtWidgets.QFileDialog.getOpenFileName(self, "Select JSON", filter="JSON files (*.json);;All files (*)")
            self.grid_view.on_load_json(json_data)
        except Exception as e:
            logging.error(f"Loading JSON Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Loading JSON Error",
                f"An error occurred while loading JSON: \n\n{e}"
            )

    def on_import_dir_tree(self):
        try:
            base_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Base Folder")
            dir_tree_path = QtWidgets.QFileDialog.getOpenFileName(self, "Select Directory Tree JSON", filter="JSON files (*.json);;All files (*)")
            self.grid_view_model.load_dir_tree(dir_tree_path, base_folder)
        except Exception as e:
            logging.error(f"Import Directory Tree Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Import Directory Tree Error",
                f"Error while importing directory tree \n\n {e}"
            )

    def on_export_dir_tree(self):
        try:
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder to save directory tree")
            if folder_path:
                self.grid_view_model.export_dir_tree(folder_path)
        except Exception as e:
            logging.error(f"Export Directory Tree Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Export Directory Tree Error",
                f"Error while exporting directory tree \n\n {e}"
            )


    #TODO: if image folder loaded switching sign types not works properly
    def load_eu_sign_types(self):
        try:
            self.change_info_label("Changing to EU Traffic Signs...", display_time=0)
            self.grid_view_model.load_eu_sign_types()
            self.move_selected_button.setText("Move Selected Images\n (EU)")
            self.change_info_label("Labels changed to EU traffic signs.")
        except Exception as e:
            logging.error(f"Load EU Sign Types Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Load EU Sign Types Error",
                f"Error while loading EU Sign Types\n\n {e}"
            )

    def load_us_sign_types(self):
        try:
            self.change_info_label("Changing to US Traffic Signs...", display_time=0)
            self.grid_view_model.load_us_sign_types()
            self.move_selected_button.setText("Move Selected Images\n (US)")
            self.change_info_label("Labels changed to US traffic signs.")
        except Exception as e:
            logging.error(f"Load US Sign Types Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Load US Sign Types Error",
                f"Error while loading US Sign Types\n\n {e}"
            )


    def add_new_labels(self):
        try:
            json_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select label JSON", filter="JSON files (*.json);;All files (*)")
            self.grid_view_model.load_labels_from_json(json_file_path)
            self.move_selected_button.setText("Move Selected Images\n (Custom)")
            self.change_info_label("New labels added and set")
        except Exception as e:
            logging.error(f"Load Custom Types Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Load Custom Types Error",
                f"Error while loading Custom Types\n\n {e}"
            )

    def update_info_after_list_clicked(self):
        self.update_batch_info()
        self.change_info_label("Folder Loaded")

    def update_batch_info(self):
        loader = self.grid_view_model.on_get_loader()
        if loader:
            self.batch_info_label.setText(
                f"{loader.current_batch_idx + 1} / {loader.number_of_batches // self.grid_view_model.on_get_batch_size() + 1}")


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
        try:
            dialog = FolderSelectionDialog(preferred=preferred_label, grid_view_model=self.grid_view_model)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_folder:
                self.grid_view_model.move_selected(dialog.selected_folder)
        except Exception as e:
            logging.error(f"Show Folder Selection Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Show Folder Selection Error",
                f"Error while loading folder selection window\n\n {e}"
            )

    def show_not_found_images_info(self, not_found_images):
        try:
            self.not_found_images_window = NotFoundImageWindow(not_found_images)
            self.not_found_images_window.show()
        except Exception as e:
            logging.error(f"Show Not Found Images Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Show Not Found Images Error",
                f"Error while loading not found images window\n\n {e}"
            )

    def show_last_move_window(self, text, main_folder):
        try:
            self.last_move_window = LastMoveWindow(text, main_folder)
            self.last_move_window.show()
            if self.last_move_window.exec_() == QDialog.Accepted:
                self.grid_view_model.undo_last_move()
        except Exception as e:
            logging.error(f"Show Last Move Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Show Last Move Error",
                f"Error while loading last move window\n\n {e}"
            )

    def on_show_message(self, title, text):
        QMessageBox.information(self, title,text)

    def closeEvent(self, event):
        try:
            self.grid_view_model.cleanup_thumbs()
            logging.info("Annotation tool closed")
            event.accept()
        except Exception as e:
            logging.error(f"Closing Error", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "Closing Error",
                f"Error while closing tool\n\n {e}"
            )


