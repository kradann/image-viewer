import copy
import json
import pprint
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union, final

import requests
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence, QFont
from PyQt5.QtWidgets import QShortcut, QDialog, QMessageBox

from FolderList import FolderListWidget
from FolderSelectionDialog import FolderSelectionDialog
from ImageGrid import ImageGridWidget, ImageBatchLoader, ImageLoaderThread
from sign_types_dialog import SignTypeDialog, eu_sign_types, us_sign_types
from NewFolderDialog import NewFolderNameDialog
from Styles import *

global window

def refresh_grid():
    global window
    window.refresh()


APP_VERSION = "0.1.0"
GITHUB_RELEASE_LINK = "https://api.github.com/repos/kradann/image-viewer/releases/latest"




def cleanup_thumbs():
    thumbs_dir = Path(__file__).resolve().parent / ".thumbs"
    if thumbs_dir.exists() and thumbs_dir.is_dir():
        for f in thumbs_dir.iterdir():
            try:
                if f.is_file():
                    f.unlink()
            except Exception as e:
                print(f"Failed to delete {f}: {e}")


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
        self.timer.timeout.connect(self.update_selected_check_button)
        self.timer.start(500)
        self.used_sign_types = None

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
        load_folder_action.triggered.connect(self.load_folder)
        file_menu.addAction(load_folder_action)
        load_json_action = QtWidgets.QAction("Load JSON", self)
        load_json_action.triggered.connect(self.load_json)
        file_menu.addAction(load_json_action)

        status_menu = self.menu_bar.addMenu("Status")

        load_status_action = QtWidgets.QAction("Load Status", self)
        load_status_action.triggered.connect(self.folder_list.load_status_action)
        status_menu.addAction(load_status_action)

        save_status_action = QtWidgets.QAction("Save Status", self)
        save_status_action.triggered.connect(self.folder_list.save_status_action)
        status_menu.addAction(save_status_action)

        sign_type_menu = self.menu_bar.addMenu("Sign Types")
        eu_sign_type_action = QtWidgets.QAction("EU sign types", self)
        eu_sign_type_action.triggered.connect(lambda: self.set_sign_type(type='eu'))
        sign_type_menu.addAction(eu_sign_type_action)

        us_sign_type_action = QtWidgets.QAction("US sign types", self)
        us_sign_type_action.triggered.connect(lambda: self.set_sign_type(type='us'))
        sign_type_menu.addAction(us_sign_type_action)


        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)

        self.folder_list.setMinimumWidth(400)
        self.folder_list.itemClicked.connect(self.folder_clicked)
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
        self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Unselect/Select all", self.un_select_select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.move_selected_button, _ = self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)
        self.add_button("Check for Update", self.check_for_update)

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

        while self.used_sign_types is None:
            self.set_sign_type()

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

    def set_sign_type(self, type=None):
        if type is None:
            dialog = SignTypeDialog()
            if dialog.exec_() != QDialog.Accepted or not dialog.selected_type:
                return

            self.used_sign_types = dialog.selected_type

        elif type=="eu":
            self.used_sign_types = eu_sign_types
        else:
            self.used_sign_types = us_sign_types

        if self.used_sign_types == eu_sign_types:
            self.change_info_label("Sign type changed to EU")
        else:
            self.change_info_label("Sign type changed to US")


    def load_folder(self):
        self.folder_list.clear()
        self.clear_images()
        self.main_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.main_folder:
            self.is_JSON_active = False
            self.subfolders = [f.name for f in Path(self.main_folder).iterdir() if f.is_dir()]
            self.subfolders.sort()

            if any(sub in self.used_sign_types for sub in self.subfolders):
                self.is_all_region = False
                self.folder_path = Path(self.main_folder) / self.subfolders[0]
                self.load_subfolders(self.main_folder)
                self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
                self.show_batch()
                self.change_info_label("Folder loaded!")
            else:
                sign_types_in_all_region = self.collect_sign_types()
                sign_types_in_all_region.sort()
                pprint.pprint(sign_types_in_all_region)
                self.folder_list.clear()
                self.subfolders = sign_types_in_all_region
                for sign_type in self.subfolders:
                    self.folder_list.addItem(sign_type)
                self.is_all_region = True

    def collect_sign_types(self):
        main = Path(self.main_folder)
        self.regions = [d for d in main.iterdir() if d.is_dir()]

        all_sign_types = set()
        for region in self.regions:
            for sign_type in region.iterdir():
                if sign_type.is_dir():
                    all_sign_types.add(sign_type.name)

        return sorted(all_sign_types)

    def load_subfolders(self, path=None):
        self.folder_list.clear()
        if not self.is_JSON_active and not self.is_all_region:
            folder_infos = []
            wrong_subfolder_name = []

            for name in self.subfolders:
                if name in self.used_sign_types:
                    full_path = Path(path) / name
                    if full_path.is_dir():
                        num_images = len(list(Path(full_path).iterdir()))
                        folder_infos.append((name, num_images))
                else:
                        wrong_subfolder_name.append(name)

            if wrong_subfolder_name and self.first_check:
                self.first_check = False
                msg = "These are not valid subfolder names:\n" + "\n".join(wrong_subfolder_name)
                QMessageBox.information(self, "Subfolder name error", msg)

            folder_infos.sort()  # order list names to abc
            self.subfolders = []
            for name, count in folder_infos:
                self.subfolders.append(name)
                display_text = f"{name:<40} {count:>6}"  # left-align name, right-align number
                self.folder_list.addItem(display_text)

            # Set monospaced font for alignment
            font = QFont("Courier New", 10)
            self.folder_list.setFont(font)
        elif not self.is_JSON_active and self.is_all_region:
            print(15)
            for sign_type in self.subfolders:
                self.folder_list.addItem(sign_type)

    def folder_clicked(self, item):
        if not self.is_JSON_active and not self.is_all_region:
            selected_subfolder = Path(self.main_folder) / item.text().split()[0]
            # self.folder_list.set_item_background(item, "black")
            print(selected_subfolder)
            self.folder_path = selected_subfolder
            self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
            self.show_batch()
        elif self.is_all_region and not self.is_JSON_active:
            selected_subfolder_name = item.text()
            self.image_paths = [Path(region, selected_subfolder_name) for region in self.regions]
            self.loader = ImageBatchLoader(self.image_paths, batch_size=self.batch_size)
            self.show_batch()

        elif self.is_JSON_active and not self.is_all_region:
            selected_values = item.text()
            self.set_loader_for_json(selected_values)
            self.show_batch()

    def change_info_label(self, text=None, text_color="#3cfb8b"):
        label = self.window().info_label
        label.setText(text)
        if text_color:
            label.setStyleSheet(f"color: {text_color}; font-size: 20px;")
        # Save the current text
        current_text = text
        # After 5 seconds, clear ONLY IF the text hasn't changed in the meantime
        QTimer.singleShot(5000, lambda: label.setText("") if label.text() == current_text else None)

    def prev_folder(self):
        if self.main_folder is None:
            return

        subfolders = sorted([f.name for f in Path(self.folder_path).parent.iterdir() if f.is_dir()])
        prev_folder_idx = subfolders.index(self.folder_path) - 1
        print(prev_folder_idx)
        if prev_folder_idx > 0:
            while not any(f.is_file() for f in Path(subfolders[prev_folder_idx]).iterdir()):
                if prev_folder_idx == len(subfolders) - 1:
                    break
                prev_folder_idx -= 1

            self.folder_path = subfolders[prev_folder_idx]

        if self.main_folder:
            self.loader = ImageBatchLoader(Path(self.main_folder) / self.subfolders[prev_folder_idx],
                                           batch_size=self.batch_size)
            self.show_batch()
            self.folder_list.highlight_by_name(self.folder_path.split('/')[-1])

    def next_folder(self):
        if self.folder_path is None:
            return

        subfolders = sorted([f.name for f in Path(self.folder_path).parent.iterdir() if f.is_dir()])
        next_folder_idx = subfolders.index(self.folder_path) + 1

        if next_folder_idx <= len(subfolders) - 1:
            while not any(f.is_file() for f in Path(subfolders[next_folder_idx]).iterdir()):
                if next_folder_idx == len(subfolders) - 1:
                    break
                next_folder_idx += 1

            self.folder_path = subfolders[next_folder_idx]

        print("loaded folder: {}".format(self.folder_path))
        if self.folder_path:
            self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
            self.show_batch()
            self.folder_list.highlight_by_name(self.folder_path.split('/')[-1])

    def load_v_value(self):
        self.scroll_area.verticalScrollBar().setValue(self.vertical_value)

    def refresh(self):
        if not self.is_JSON_active:
            if self.folder_path and not self.is_all_region:
                print(self.folder_path)
                self.vertical_value = self.scroll_area.verticalScrollBar().value()
                self.loader = ImageBatchLoader(self.folder_path,
                                               batch_size=self.batch_size,
                                               start_batch_idx=self.loader.current_batch_idx)
                self.show_batch()
                self.load_subfolders(self.main_folder)
            elif self.is_all_region:
                self.vertical_value = self.scroll_area.verticalScrollBar().value()
                self.loader = ImageBatchLoader(self.image_paths, batch_size=self.batch_size,
                                               start_batch_idx=self.loader.current_batch_idx)
                self.show_batch()
                self.load_subfolders()
        else:
            self.vertical_value = self.scroll_area.verticalScrollBar().value()
            self.set_loader_for_json(self.folder_list.currentItem().text())
            self.show_batch()

    def clear_images(self):
        for label in self.labels:
            label.deleteLater()
        self.labels = list()

    def show_batch(self):
        if not self.loader:
            return

        self.clear_images()
        batch = self.loader.get_batch()
        self.batch_info_label.setText(
            f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

        self.thread = ImageLoaderThread(batch)
        self.thread.image_loaded.connect(self.add_image_to_layout)
        self.thread.start()
        if not self.is_JSON_active and self.window().folder_path:
            self.window().current_folder_label.setText("Current folder: " + str(self.window().folder_path).split("/")[-1])

    def add_image_to_layout(self, idx, pixmap, _path):
        label = ClickableLabel(_path)
        label.setPixmap(pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        label.clicked.connect(lambda: self.toggle_selection(label))

        if _path in self.selected_images:
            label.selected = True
            label.add_red_boarder()

        row = idx // self.num_of_col
        col = idx % self.num_of_col
        self.image_layout.addWidget(label, row, col)
        self.labels.append(label)

    def add_image_to_layout_no_toggle(self, idx, pixmap, _path):
        label = ClickableLabel(_path)
        label.setPixmap(pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

        row = idx // self.num_of_col
        col = idx % self.num_of_col
        self.image_layout.addWidget(label, row, col)
        self.labels.append(label)

    def toggle_selection(self, label):
        path = label.img_path
        if label.selected:
            self.selected_images.add(path)
        else:
            self.selected_images.discard(path)

    def update_selected_check_button(self):
        if self.main_folder:
            if self.selected_images:
                self.move_selected_button.setEnabled(True)
                self.move_selected_button.setStyleSheet("color: black; background-color: green;")
            else:
                self.move_selected_button.setEnabled(False)
                self.move_selected_button.setStyleSheet("color: black; background-color: #8B0000;")

    def un_select_select_all(self):
        if not self.isAllSelected:
            self.isAllSelected = True
            for label in self.labels:
                label.selected = True
                self.selected_images.add(label.img_path)
        else:
            self.isAllSelected = False
            for label in self.labels:
                label.selected = False
                self.selected_images.discard(label.img_path)
        self.show_batch()

    def next_batch(self):
        if self.loader:
            self.loader.next_batch()
            self.show_batch()
            # self.batch_info_label.setText( f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

    def previous_batch(self):
        if self.loader:
            self.loader.previous_batch()
            self.show_batch()
            # self.batch_info_label.setText( f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images()
        self.dropped_selected = copy.deepcopy(self.selected_images)

        self.thread = ImageLoaderThread(sorted(self.selected_images))
        self.thread.image_loaded.connect(self.add_image_to_layout)
        self.thread.start()

    def move_selected(self):
        if not self.is_JSON_active and not self.is_all_region:
            # check if folder loadded
            if self.main_folder is None:
                self.change_info_label("Error: No folder selected")
                return

            # load subfolders
            '''subfolders = [f for f in os.listdir(self.main_folder) if os.path.isdir(os.path.join(self.main_folder, f))]
            subfolders.sort()'''

            if not self.subfolders:
                QtWidgets.QMessageBox.warning(self, "Error", "No subfolders found")
                return

            # create selection dialog
            dialog = FolderSelectionDialog(self, sign_types=self.used_sign_types)
            if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
                return

            output_folder = Path(self.main_folder) / dialog.selected_folder
            output_folder.mkdir(parents=True, exist_ok=True)

            # move images to selected folders
            if self.selected_images:
                for img_path in sorted(self.selected_images):
                    self.dropped_selected.discard(img_path)
                    img_path = Path(img_path)
                    dst_path = output_folder / img_path.name
                    base, ext = Path(img_path.name).stem, Path(img_path.name).suffix

                    counter = 1
                    while dst_path.exists():
                        dst_path = dst_path.parent / f"{base}_{counter}{ext}"
                        counter += 1

                    self.change_info_label(
                        "moved from: {}, to: {}".format(img_path.parent.name, dst_path.parent.name))
                    # print("moved from: {}, to: {}".format(img_path, dst_path))
                    shutil.move(str(img_path), str(dst_path))

            else:
                self.change_info_label("No selected images found!")

            # check if images left
            if len(self.dropped_selected) > 0:
                self.selected_images = copy.deepcopy(self.dropped_selected)
                self.show_only_selected()
            else:
                self.selected_images = set()
                self.refresh()
            #self.load_subfolders(self.main_folder)
        elif not self.is_JSON_active and self.is_all_region:
            dialog = FolderSelectionDialog(self, sign_types=self.used_sign_types)
            if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
                return
            if self.selected_images:
                for img_path in sorted(self.selected_images):
                    self.dropped_selected.discard(img_path)
                    print(f"image path: {img_path}")
                    img_path = Path(img_path)

                    output_folder = Path(img_path.parent.parent) / dialog.selected_folder
                    print(output_folder)

                    output_folder.mkdir(parents=True, exist_ok=True)
                    dst_path = output_folder / img_path.name
                    base, ext = Path(img_path.name).stem, Path(img_path.name).suffix

                    counter = 1
                    while dst_path.exists():
                        dst_path = dst_path.parent / f"{base}_{counter}{ext}"
                        counter += 1

                    print(f"dst_path: {dst_path}\n base: {base}\n ext: {ext}")
                    self.change_info_label(
                        "moved from: {}, to: {}".format(img_path.parent.name, dst_path.parent.name))
                    shutil.move(str(img_path), str(dst_path))
            else:
                self.change_info_label("No selected images found!")
            if len(self.dropped_selected) > 0:
                print(12)
                self.selected_images = copy.deepcopy(self.dropped_selected)
                self.show_only_selected()
            else:
                print(13)
                self.selected_images = set()
                self.refresh()
            #self.load_subfolders()
        elif self.is_JSON_active and not self.is_all_region:
            dialog = FolderSelectionDialog(self, self.loader.label, sign_types=self.used_sign_types)
            if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
                return
            if self.selected_images:
                for img_path in sorted(self.selected_images):
                    img_path = Path(img_path)
                    image_name = img_path.name
                    self.dropped_selected.discard(img_path)
                    dst_path = img_path.parent.parent / dialog.selected_folder
                    dst_path.mkdir(parents=True, exist_ok=True)

                    final_path = dst_path / image_name
                    base, ext = Path(image_name).stem, Path(image_name).suffix

                    counter = 1
                    while final_path.exists():
                        final_path = dst_path / f"{base}_{counter}{ext}"
                        counter += 1

                    self.change_info_label(
                        f"moved from: {img_path.parent.parent.name}/{img_path.parent.name}, "
                        f"to: {dst_path.parent.name}/{dst_path.name}"
                    )
                    shutil.move(str(img_path), str(final_path))
                    if str(img_path) in self.json_data:
                        del self.json_data[str(img_path)]
            else:
                self.change_info_label("No selected images found!")
            if len(self.dropped_selected) > 0:
                self.selected_images = copy.deepcopy(self.dropped_selected)
                self.show_only_selected()
            else:
                self.selected_images = set()
                self.refresh()
            self.load_subfolders()

    def check_for_update(self):
        try:
            response = requests.get(GITHUB_RELEASE_LINK, timeout=10)

            if response.status_code == 404:
                QMessageBox.information(self, "Update", "No releases found")
                return

            data = response.json()
            latest_release = data["tag_name"]

            if latest_release != APP_VERSION:
                QMessageBox.information(self, "Update", f"New version {latest_release} available!")

                assets = data.get("assets", [])
                if not assets:
                    QMessageBox.information(self, "Update", "No release asset found!")
                    return

                download_url = assets[0]["browser_download_url"]
                file_name = assets[0]["name"]

                r = requests.get(download_url, stream=True)
                with open(file_name, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                QMessageBox.information(self, "Update", f"Downloaded {file_name} successfully!")

                new_path = Path(file_name).resolve()
                subprocess.Popen([new_path])
                sys.exit(0)
            else:
                QMessageBox.information(self, "Update", "Already up to date!")
        except Exception as e:
            QMessageBox.information(self, "Update", f"An error occurred: {e}")

    def load_json(self):

        self.json = QtWidgets.QFileDialog.getOpenFileName(self, "Select JSON", "", "JSON files (*.json);;All files (*)")
        if self.json:
            try:
                with open(self.json[0], "r", encoding="utf-8") as json_file:
                    self.json_data = json.load(json_file)
                values_set = sorted(set(self.json_data.values()))

                self.is_JSON_active = True
                self.is_all_region = False
                self.base_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Base Folder")

                self.folder_list.clear()
                for value in values_set:
                    self.folder_list.addItem(value)

                print(values_set)
            except Exception as e:
                QMessageBox.information(self, "Error", f"Unable to load JSON: {e}")

    def set_loader_for_json(self, selected_values):
        base = Path(self.base_folder)
        matched_images = [
            str(base / img_path)
            for img_path, label in self.json_data.items()
            if label == selected_values and (base / img_path).exists()
        ]
        print(f"Found {len(matched_images)} images with label {selected_values}")
        self.loader = ImageBatchLoader.__new__(ImageBatchLoader)  # create empty
        self.loader.image_paths = matched_images
        self.loader.batch_size = self.batch_size
        self.loader.current_batch_idx = 0
        self.loader.number_of_batches = len(matched_images)
        self.loader.label = selected_values

    def closeEvent(self, event):
        if self.is_JSON_active:
            with open(self.json[0], "w", encoding="utf-8") as json_file:
                json.dump(self.json_data, json_file, indent=2, ensure_ascii=False)
        cleanup_thumbs()
        event.accept()


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def __init__(self, img_path, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.selected = False
        self.cut_mode = None  # 'vertical' or 'horizontal'
        self.preview_pos = None
        self.pixmap_backup = None
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        if self.cut_mode:
            self.preview_pos = event.pos()
            self.update()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.show_context_menu(event.pos())
        elif event.button() == QtCore.Qt.LeftButton and self.cut_mode and self.preview_pos:
            self.cut_at_position(event.pos())  # csak az adott label pixmap-jét vágjuk
        else:
            super().mousePressEvent(event)

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        vertical_cut = menu.addAction("Vertical Cut")
        horizontal_cut = menu.addAction("Horizontal Cut")
        action = menu.exec_(self.mapToGlobal(pos))

        if action == vertical_cut:
            self.cut_mode = 'vertical'
        elif action == horizontal_cut:
            self.cut_mode = 'horizontal'

    def add_red_boarder(self):
        self.setStyleSheet("border: 3px solid red;" if self.selected else "")

    def cut_at_position(self, pos):
        pixmap = self.pixmap()
        # if pixmap is None:
        # return
        print("asd")
        if self.pixmap_backup is None:
            self.pixmap_backup = pixmap.copy()

        x = pos.x()
        y = pos.y()
        width = pixmap.width()
        height = pixmap.height()

        if self.cut_mode == 'vertical':
            rect_0 = QtCore.QRect(0, 0, x, height)
            rect_1 = QtCore.QRect(x, 0, width, height)
        else:  # horizontal
            rect_0 = QtCore.QRect(0, 0, width, y)
            rect_1 = QtCore.QRect(0, y, width, height)
        # print(rect_0, rect_1)
        cropped_0 = pixmap.copy(rect_0)
        cropped_1 = pixmap.copy(rect_1)

        p = Path(self.img_path)

        name_idx = 2
        while True:
            new_path = p.with_stem(f"{p.stem}_{name_idx}")
            if not new_path.exists():
                break
            name_idx += 1

        # print(self.img_path)
        # print(new_path)

        cropped_0.save(self.img_path)
        cropped_1.save(str(new_path))
        # cropped_1.save("./mama.png")
        # self.setPixmap(cropped.scaled(150, 150, QtCore.Qt.KeepAspectRatio))

        self.cut_mode = None
        self.preview_pos = None
        self.update()
        thumb_path = ImageLoaderThread.get_thumb_path(self.img_path)
        ImageLoaderThread.generate_thumbnail(self.img_path, thumb_path)
        self.setPixmap(QtGui.QPixmap(thumb_path))
        refresh_grid()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cut_mode and self.preview_pos:
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashLine)
            painter.setPen(pen)

            if self.cut_mode == 'vertical':
                painter.drawLine(self.preview_pos.x(), 0, self.preview_pos.x(), self.height())
            else:  # horizontal
                painter.drawLine(0, self.preview_pos.y(), self.width(), self.preview_pos.y())

            painter.end()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = ImageMontageApp()
    window.show()
    app.exec_()
