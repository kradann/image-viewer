import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from http.client import responses
from typing import Union

import requests
from PIL import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence, QFont
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor
from PyQt5.QtWidgets import QPushButton, QShortcut, QDialog, QMessageBox

from NewFolderDialog import NewFolderNameDialog
from FolderList import FolderListWidget
from FolderSelectionDialog import FolderSelectionDialog
from ImageGrid import ImageGridWidget,ImageBatchLoader, ImageLoaderThread,ClickableLabel
from Styles import *

# from libdnf.utils import NullLogger

global window

sign_types = ["eu_speedlimit_100",
              "eu_speedlimit_110",
              "eu_speedlimit_120",
              "eu_speedlimit_130",
              "eu_speedlimit_30",
              "eu_speedlimit_40",
              "eu_speedlimit_50",
              "eu_speedlimit_60",
              "eu_speedlimit_70",
              "eu_speedlimit_80",
              "eu_speedlimit_90",
              "eu_overtaking_not_allowed",
              "eu_overtaking_not_allowed_by_trucks",
              "eu_end_of_restrictions",
              "eu_end_of_overtaking_restriction",
              "eu_end_of_overtaking_by_trucks_restriction",
              "eu_end_of_speedlimit_100",
              "eu_end_of_speedlimit_110",
              "eu_end_of_speedlimit_120",
              "eu_end_of_speedlimit_130",
              "eu_end_of_speedlimit_30",
              "eu_end_of_speedlimit_40",
              "eu_end_of_speedlimit_50",
              "eu_end_of_speedlimit_60",
              "eu_end_of_speedlimit_70",
              "eu_end_of_speedlimit_80",
              "eu_end_of_speedlimit_90",
              "eu_zone_of_speedlimit_20",
              "eu_zone_of_speedlimit_30",
              "eu_zone_of_speedlimit_40",
              "eu_end_of_zone_of_speedlimit_20",
              "eu_end_of_zone_of_speedlimit_30",
              "eu_end_of_zone_of_speedlimit_40",
              "eu_minimum_speed_100",
              "eu_minimum_speed_110",
              "eu_minimum_speed_120",
              "eu_minimum_speed_130",
              "eu_minimum_speed_30",
              "eu_minimum_speed_40",
              "eu_minimum_speed_50",
              "eu_minimum_speed_60",
              "eu_minimum_speed_70",
              "eu_minimum_speed_80",
              "eu_minimum_speed_90",
              "eu_end_of_eu_minimum_speed_100",
              "eu_end_of_eu_minimum_speed_110",
              "eu_end_of_eu_minimum_speed_120",
              "eu_end_of_eu_minimum_speed_130",
              "eu_end_of_eu_minimum_speed_30",
              "eu_end_of_eu_minimum_speed_40",
              "eu_end_of_eu_minimum_speed_50",
              "eu_end_of_eu_minimum_speed_60",
              "eu_end_of_eu_minimum_speed_70",
              "eu_end_of_eu_minimum_speed_80",
              "eu_end_of_eu_minimum_speed_90",
              "eu_city_limit_entry",
              "eu_city_limit_exit",
              "eu_residential_area",
              "eu_end_of_residential_area",
              "eu_no_entry",
              "eu_road_closed",
              "eu_axle_weight_restriction",
              "eu_weight_restriction",
              "eu_height_restriction",
              "eu_length_restriction",
              "eu_width_restriction",
              "eu_minimal_distance",
              "eu_minimal_distance_trucks",
              "eu_no_hazardous_material",
              "eu_hazardous_material_allowed",
              "eu_no_water_pollutants",
              "eu_water_pollutants_allowed",
              "eu_giveway",
              "eu_stop",
              "eu_priority_crossing_ahead",
              "eu_yield_to_right",
              "eu_priorityroad_ahead",
              "eu_priorityroad_ends",
              "eu_motorway",
              "eu_end_of_motorway",
              "eu_highway",
              "eu_end_of_highway",
              "eu_dangerous_situation",
              "eu_warning_of_curve",
              "eu_warning_of_double_curve",
              "eu_warning_of_cattle",
              "eu_warning_of_animals",
              "eu_road_constriction",
              "eu_road_bump",
              "eu_warning_of_wind",
              "eu_roadworks",
              "eu_warning_of_skidding",
              "eu_warning_of_bikes",
              "eu_warning_of_trains",
              "eu_warning_of_pedestrian_crossing",
              "eu_warning_of_pedestrians",
              "eu_warning_of_children",
              "eu_pedestrian_crossing",
              "eu_warning_of_slope",
              "eu_warning_of_traffic_jam",
              "eu_warning_of_roundabouts",
              "eu_warning_of_crossing",
              "eu_warning_of_ice",
              "eu_height_restriction",
              "eu_warning_of_tunnel",
              "eu_warning_of_two_way",
              "eu_warning_of_traffic_lights",
              "eu_warning_of_draw_bridge",
              "eu_warning_of_frogs",
              "eu_warning_of_planes",
              "eu_warning_of_gravel",
              "eu_warning_of_trees",
              "eu_rock_slides",
              "eu_merging_lane",
              "eu_warning_of_pier",
              "eu_warning_of_accidents",
              "eu_dir_sign_diagonal",
              "eu_roundabout",
              "eu_dir_sign_side",
              "eu_dir_sign_curve",
              "eu_dir_sign_up",
              "eu_one_way_street",
              "eu_oncoming_precedence",
              "eu_precedence_over_oncoming",
              "eu_no_turning",
              "eu_additional_vehicle_a",
              "eu_additional_vehicle_b",
              "eu_additional_hazardous",
              "eu_additional_rain",
              "eu_additional_snow",
              "eu_additional_rainsnow",
              "eu_additional_wet_road",
              "eu_additional_day_night",
              "eu_additional_arrow_to_exit",
              "eu_additiona_validity_ends_a",
              "eu_additiona_validity_ends_b",
              "eu_additiona_validity_ends_c",
              "eu_additiona_validity_ends_d",
              "eu_additional_stop_in_dist",
              "eu_additional_dist",
              "eu_additional_timeframe",
              "eu_additional_weight",
              "eu_additional_school",
              "eu_additional_zone",
              "eu_additional_tree",
              "eu_additional_trucks",
              "eu_additional_other",
              "eu_direction_position_indication_unknown",
              "eu_blue_ground_circle_unknown",
              "eu_blue_ground_rectangle_unknown",
              "eu_blue_border_rectangle_unknown",
              "eu_red_border_circle_unknown",
              "eu_red_border_up_triangle_unknown",
              "eu_white_ground_rectangle"]

sign_types.sort()

APP_VERSION = "0.1.0"
GITHUB_RELEASE_LINK = "https://api.github.com/repos/kradann/image-viewer/releases/latest"

def refresh_grid():
    global window
    window.refresh()


def pil_to_qpixmap(pil_image):
    """Convert PIL Image to QPixmap"""
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    qimg = QImage.fromData(buffer.getvalue(), "PNG")
    return QPixmap.fromImage(qimg)

def cleanup_thumbs():
    thumbs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".thumbs")
    print(thumbs_dir)
    if os.path.exists(thumbs_dir):
        for f in os.listdir(thumbs_dir):
            file_path = os.path.join(thumbs_dir, f)
            print(file_path)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")


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
        self.thread = None
        self.isAllSelected = False
        self.subfolders = None
        self.labels = list()
        self.selected_images = set()
        self.dropped_selected = set()
        self.batch_info_label = QtWidgets.QLabel("Batch Info")
        self.batch_info_label.setStyleSheet(BATCH_INFO_STYLE)
        self.batch_info_label.setAlignment(Qt.AlignCenter)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_selected_check_button)
        self.timer.start(500)

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

        status_menu = self.menu_bar.addMenu("Status")

        load_status_action = QtWidgets.QAction("Load Status", self)
        load_status_action.triggered.connect(self.folder_list.load_status_action)
        status_menu.addAction(load_status_action)

        save_status_action = QtWidgets.QAction("Save Status", self)
        save_status_action.triggered.connect(self.folder_list.save_status_action)
        status_menu.addAction(save_status_action)

        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)

        # self.folder_list.left_click_handler = self.folder_clicked
        # self.folder_list.right_click_handler = self.folder_right_clicked
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
        # self.add_button("Load Folder", self.load_folder)
        self.add_button("Previous Folder", self.prev_folder)
        self.add_button("Next Folder", self.next_folder)
        self.add_button("Make new Folder", self.make_new_folder)
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

    def load_folder(self):
        self.main_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")

        self.subfolders = [f for f in os.listdir(self.main_folder)
                           if os.path.isdir(os.path.join(self.main_folder, f))]
        self.subfolders.sort()
        # print("loaded folder: {}".format(self.folder_path))
        if self.main_folder:
            self.folder_path = os.path.join(self.main_folder, self.subfolders[0])
            self.load_subfolders(self.main_folder)
            self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
            self.show_batch()
            self.change_info_label("Folder loaded!")

    def load_subfolders(self, path):
        self.folder_list.clear()
        folder_infos = []
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                num_images = len(os.listdir(full_path))
                folder_infos.append((name, num_images))

        folder_infos.sort()  # order list names to abc

        for name, count in folder_infos:
            display_text = f"{name:<40} {count:>6}"  # left-align name, right-align number
            self.folder_list.addItem(display_text)

        # Set monospaced font for alignment
        font = QFont("Courier New", 10)
        self.folder_list.setFont(font)

    def folder_clicked(self, item):
        selected_subfolder = os.path.join(self.main_folder, item.text().split()[0])
        #self.folder_list.set_item_background(item, "black")
        print(selected_subfolder)
        self.folder_path = selected_subfolder
        self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
        self.show_batch()

    def make_new_folder(self):
        if self.main_folder:
            dialog = NewFolderNameDialog(self)
            if dialog.list_widget.count() == 0:
                dialog.list_widget.addItems(sign_types)
            if dialog.exec_() == QDialog.Accepted:
                new_folder_path = os.path.join(self.main_folder, dialog.user_input.text())

                try:
                    os.makedirs(new_folder_path, exist_ok=False)
                    self.load_subfolders(self.main_folder)
                    self.change_info_label("New folder created!")
                except FileExistsError:
                    QtWidgets.QMessageBox.warning(self, "Error", "This folder already exists!")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Can't create this folder:\n{e}")
            else:
                return

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

        subfolders = sorted([f.path for f in os.scandir(os.path.dirname(self.folder_path)) if f.is_dir()])
        prev_folder_idx = subfolders.index(self.folder_path) - 1
        print(prev_folder_idx)
        if prev_folder_idx > 0:
            while len(os.listdir(subfolders[prev_folder_idx])) == 0:
                if prev_folder_idx == len(subfolders) - 1:
                    break
                prev_folder_idx -= 1

            self.folder_path = subfolders[prev_folder_idx]

        if self.main_folder:
            self.loader = ImageBatchLoader(os.path.join(self.main_folder, self.subfolders[prev_folder_idx]),
                                           batch_size=self.batch_size)
            self.show_batch()
            self.folder_list.highlight_by_name(self.folder_path.split('/')[-1])

    def next_folder(self):
        if self.folder_path is None:
            return

        subfolders = sorted([f.path for f in os.scandir(os.path.dirname(self.folder_path)) if f.is_dir()])
        next_folder_idx = subfolders.index(self.folder_path) + 1

        if next_folder_idx <= len(subfolders) - 1:
            while len(os.listdir(subfolders[next_folder_idx])) == 0:
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
        if self.folder_path:
            print(self.folder_path)
            self.vertical_value = self.scroll_area.verticalScrollBar().value()
            self.loader = ImageBatchLoader(self.folder_path,
                                           batch_size=self.batch_size,
                                           start_batch_idx=self.loader.current_batch_idx)
            self.show_batch()
            self.load_subfolders(self.main_folder)

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
        self.window().current_folder_label.setText("Current folder: " + self.window().folder_path.split("/")[-1])

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
            #self.batch_info_label.setText( f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

    def previous_batch(self):
        if self.loader:
            self.loader.previous_batch()
            self.show_batch()
            #self.batch_info_label.setText( f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images()
        self.dropped_selected = copy.deepcopy(self.selected_images)

        self.thread = ImageLoaderThread(sorted(self.selected_images))
        self.thread.image_loaded.connect(self.add_image_to_layout)
        self.thread.start()

    def move_selected(self):
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
        dialog = FolderSelectionDialog(self, self.folder_path)
        if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
            return

        output_folder = os.path.join(self.main_folder, dialog.selected_folder)

        # move images to selected folders
        if self.selected_images:
            for img_path in sorted(self.selected_images):
                self.dropped_selected.discard(img_path)
                img_name = os.path.basename(img_path)
                dst_path = os.path.join(output_folder, img_name)
                self.change_info_label(
                    "moved from: {}, to: {}".format(img_path.split('/')[-2], dst_path.split('/')[-2]))
                # print("moved from: {}, to: {}".format(img_path, dst_path))
                shutil.move(img_path, dst_path)
        else:
            self.change_info_label("No selected images found!")

        # check if images left
        if len(self.dropped_selected) > 0:
            self.selected_images = copy.deepcopy(self.dropped_selected)
            self.show_only_selected()
        else:
            self.selected_images = set()
            self.refresh()

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

                new_path = os.path.abspath(file_name)
                subprocess.Popen([new_path])
                sys.exit(0)
            else:
                QMessageBox.information(self, "Update", "Already up to date!")
        except Exception as e:
            QMessageBox.information(self, "Update", f"An error occurred: {e}")


    def closeEvent(self, event):
        print(1)
        cleanup_thumbs()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = ImageMontageApp()
    window.show()
    app.exec_()
