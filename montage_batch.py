import copy
import io
import json
import os
import shutil
import hashlib
import time
from time import sleep
from typing import Union

import PIL.Image
from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor, QBrush
from PyQt5.QtWidgets import QLabel, QPushButton, QShortcut, QMenu, QAction, QInputDialog, QDialog
from PyQt5.QtGui import QKeySequence, QFont, QWheelEvent
#from libdnf.utils import NullLogger

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
"eu_white_ground_rectangle",]

sign_types.sort()

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

def get_thumb_path(image_path: str, cache_dir=".thumbs") -> str:
    os.makedirs(cache_dir, exist_ok=True)
    hash_name = hashlib.md5(image_path.encode("utf-8")).hexdigest()
    return os.path.join(cache_dir, f"{hash_name}.jpg")

def generate_thumbnail(image_path: str, thumb_path: str, size=(800, 800)):
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail(size, Image.LANCZOS)
            img.save(thumb_path, "JPEG")
    except Exception as e:
        print(f"Thumbnail error for {image_path}: {e}")

def cleanup_thumbs():
    thumbs_dir = ".thumbs"
    if os.path.exists(thumbs_dir):
        for f in os.listdir(thumbs_dir):
            file_path = os.path.join(thumbs_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)

    def __init__(self, paths, cache_dir=".thumbs"):
        super().__init__()
        self.paths = paths
        self.cache_dir = cache_dir

    def run(self):
        for idx, path in enumerate(self.paths):
            #print(f"[LoaderThread] Loading: {path}")
            thumb_path = get_thumb_path(path, cache_dir=self.cache_dir)

            if not os.path.exists(thumb_path):
                generate_thumbnail(path, thumb_path)

            try:
                #img = Image.open(path)
                # img.thumbnail((128, 128))
                pixmap = QtGui.QPixmap(thumb_path)
                # qimage = ImageQt(img)
                # pixmap = QtGui.QPixmap.fromImage(qimage)
                self.image_loaded.emit(idx, pixmap, path)
            except Exception as e:
                print(f"Error loading image {path}: {e}")


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
        if pixmap is None:
            return

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
        print(rect_0, rect_1)
        cropped_0 = pixmap.copy(rect_0)
        cropped_1 = pixmap.copy(rect_1)

        first_part = ".".join(self.img_path.split(".")[:-1])
        ext = self.img_path.split(".")[-1]

        name_idx = 2
        while True:
            new_path ="{}_{}.{}".format(first_part, name_idx, ext)
            if not os.path.exists(new_path):
                break
            else:
                name_idx += 1

        # print(self.img_path)
        # print(new_path)

        cropped_0.save(self.img_path)
        cropped_1.save(new_path)
        # cropped_1.save("./mama.png")
        # self.setPixmap(cropped.scaled(150, 150, QtCore.Qt.KeepAspectRatio))

        self.cut_mode = None
        self.preview_pos = None
        self.update()
        thumb_path = get_thumb_path(self.img_path)
        generate_thumbnail(self.img_path, thumb_path)
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


class ImageBatchLoader(object):
    def __init__(self, folder_path, batch_size=20, start_batch_idx=0):
        self.folder_path = folder_path
        self.batch_size = batch_size
        self.image_paths = self.collect_image_paths()
        self.current_batch_idx = start_batch_idx
        self.number_of_batches = len(self.image_paths)

    def collect_image_paths(self):
        image_paths = list()
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    image_paths.append(os.path.join(root, file))
        return sorted(image_paths)

    def get_batch(self):
        start_idx = self.current_batch_idx * self.batch_size
        end_idx = start_idx + self.batch_size
        return self.image_paths[start_idx:end_idx]

    def next_batch(self):
        if (self.current_batch_idx + 1) * self.batch_size < len(self.image_paths):
            self.current_batch_idx += 1
        print("batch idx: {}".format(self.current_batch_idx))


    def previous_batch(self):
        if self.current_batch_idx > 0:
            self.current_batch_idx -= 1
        print("batch idx: {}".format(self.current_batch_idx))

class ImageGridWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()
        self.drag_selecting = False
        self.parent_app = parent
        self.clicked_label = None

    def mousePressEvent(self, event):
        #print(1)
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.clicked_label = self.label_at(event.pos())  # select which image was clicked
            self.drag_selecting = True
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubber_band.show()
        #elif event.button() == QtCore.Qt.RightButton:
            #self.show_context_menu(event.pos())

    def mouseMoveEvent(self, event):
        if self.drag_selecting:
            #print(4)
            rect = QtCore.QRect(self.origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_selecting:
            self.rubber_band.hide()
            selection_rect = self.rubber_band.geometry()
            drag_distance = (event.pos() - self.origin).manhattanLength()

            if drag_distance < 40 and self.clicked_label:  # no drag, just clicking
                self.clicked_label.selected = not self.clicked_label.selected
                self.clicked_label.add_red_boarder()
                if self.clicked_label.selected:
                    self.parent_app.selected_images.add(self.clicked_label.img_path)
                else:
                    self.parent_app.selected_images.discard(self.clicked_label.img_path)
            else:
                # rubber band kijelölés
                for label in self.parent_app.labels:
                    label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
                    label_rect = QtCore.QRect(label_pos, label.size())
                    if selection_rect.intersects(label_rect):
                        label.selected = True
                        label.add_red_boarder()
                        self.parent_app.selected_images.add(label.img_path)

            self.drag_selecting = False
            self.clicked_label = None

    def label_at(self, pos):
        for label in self.parent_app.labels:
            label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
            label_rect = QtCore.QRect(label_pos, label.size())
            if label_rect.contains(pos):
                return label
        return None

class FolderListWidget(QtWidgets.QListWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
            self.status_dict = dict()

        def mousePressEvent(self, event):
            super().mousePressEvent(event)

        #handle right click
        def show_context_menu(self, pos):
            item = self.itemAt(pos)
            if not item:
                return

            menu = QtWidgets.QMenu(self)
            #options when right click
            not_done = menu.addAction("Not Done")
            in_progress = menu.addAction("In Progress")
            done = menu.addAction("Done")
            remove = menu.addAction("Remove Status")
            delete_folder = menu.addAction("Delete Folder")

            action = menu.exec_(self.mapToGlobal(pos))

            transparency = 125
            item_text = item.text()
            #color background
            if action == not_done:
                item.setBackground(QtGui.QColor(255,0,0,transparency))
                self.status_dict[item_text.split()[0]] = "not_done"
            elif action == in_progress:
                item.setBackground(QtGui.QColor(255,255,0,transparency))
                self.status_dict[item_text.split()[0]] = "in_progress"
            elif action == done:
                item.setBackground(QtGui.QColor(0,255,0,transparency))
                self.status_dict[item_text.split()[0]] = "done"
            elif action == remove:
                item.setBackground(QtGui.QColor("#303436"))
                self.status_dict[item_text.split()[0]] = None
            elif action == delete_folder:
                reply = QtWidgets.QMessageBox.question(self, "Confirm Deletion",
                                                       f"Are you sure you want to delete <b>{item_text.split()[0]}</b>?",
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    folder_path = os.path.join(self.window().main_folder, item_text.split()[0])
                    try:
                        if os.path.isdir(folder_path):
                            shutil.rmtree(folder_path)
                            self.takeItem(self.row(item))
                            QtWidgets.QMessageBox.information(self, "Success", f"Deleted <b>{item_text.split()[0]}</b>.")
                        else:
                            QtWidgets.QMessageBox.warning(self, "Error", f"'{folder_path}' is not a folder.")
                    except Exception as e:
                        QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete folder:\n{str(e)}")

            self.setCurrentItem(None) #remove selection from folder

        def load_status_action(self):
            main_folder = self.window().main_folder
            loaded_status_action = None
            if main_folder is not None:
                load_path = os.path.join(main_folder, main_folder.split('/')[-1] + "_status_action.json")
                if not os.path.exists(load_path):
                    QtWidgets.QMessageBox.warning(self, "Hiba", f"A fájl nem található:\n{load_path}")
                    return

                try:
                    with open(load_path, "r") as f:
                        loaded_status_action = json.load(f)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni:\n{e}")
                    return
            if loaded_status_action is not None:
                self.status_dict = loaded_status_action
                transparency = 125
                for i in range(self.count()):
                    item = self.item(i)
                    text = item.text().split()[0]
                    status = self.status_dict.get(text, None)
                    if status == "not_done":
                        item.setBackground(QtGui.QColor(255, 0, 0, transparency))
                    elif status == "in_progress":
                        item.setBackground(QtGui.QColor(255, 255, 0, transparency))
                    elif status == "done":
                        item.setBackground(QtGui.QColor(0, 255, 0, transparency))
                    else:
                        item.setBackground(QtGui.QColor("#303436"))
                self.window().change_info_label("Status Loaded!")

        def save_status_action(self):
            main_folder = self.window().main_folder
            if main_folder is not None:
                save_path = os.path.join(main_folder, main_folder.split('/')[-1] + "_status_action.json")

                try:
                    with open(save_path, "w") as f:
                        json.dump(self.status_dict, f, indent=4)
                    QtWidgets.QMessageBox.information(self, "Siker", f"Státuszok elmentve ide:\n{save_path}")
                    self.window().change_info_label("Status Saved!")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni:\n{e}")

class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Batch Viewer")
        self.resize(1600, 900)
        self.num_of_col = 6
        self.batch_size = 1000
        self.thumbnail_size = 150, 150

        self.setPalette(get_dark_palette())

        self.loader = None
        self.folder_path = None
        self.main_folder = None # Folder that stores the subfolders
        self.thread = None
        self.isAllSelected = False
        self.subfolders = None
        self.labels = list()
        self.selected_images = set()
        self.dropped_selected = set()
        self.batch_info_label = QtWidgets.QLabel("Batch Info")
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
        load_folder_action = QtWidgets.QAction("Load Folder",self)
        load_folder_action.triggered.connect(self.load_folder)
        file_menu.addAction(load_folder_action)

        status_menu = self.menu_bar.addMenu("Status")

        load_status_action = QtWidgets.QAction("Load Status", self)
        load_status_action.triggered.connect(self.folder_list.load_status_action)
        status_menu.addAction(load_status_action)

        save_status_action = QtWidgets.QAction("Save Status", self)
        save_status_action.triggered.connect(self.folder_list.save_status_action)
        status_menu.addAction(save_status_action)

        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #181a1b;
                font-size: 18px;
                
            }

            QMenuBar::item {
                color: #3cfb8b;
                background-color: #181a1b;
            }

            QMenuBar::item:selected {
                background-color: #444444;
            }

            QMenu {
                background-color: #181a1b;
                color: #00ff00;
                font-size: 16px;
            }

            QMenu::item:selected {
                background-color: #444444;
            }
        """)

        #self.folder_list.left_click_handler = self.folder_clicked
        #self.folder_list.right_click_handler = self.folder_right_clicked
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
        #self.add_button("Load Folder", self.load_folder)
        self.add_button("Previous Folder", self.prev_folder)
        self.add_button("Next Folder", self.next_folder)
        self.add_button("Make new Folder", self.make_new_folder)
        self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Unselect/Select all", self.un_select_select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)

        self.button_layout_wrapper.addWidget(self.batch_info_label)

        self.info_label = QtWidgets.QLabel("Bottom Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 20px; color: #3cfb8b")
        self.outer_layout.addWidget(self.info_label)

    def add_button(self, name: str, func, shortcut: Union[str, tuple] = None):
        button = QtWidgets.QPushButton(name)
        button.setFont(QFont("Arial", 10))
        button.setFixedSize(160, 40)
        button.setStyleSheet("color: #3cfb8b; background-color: #303436;")
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
                          if os.path.isdir(os.path.join(self.main_folder,f))]
        self.subfolders.sort()
        #print("loaded folder: {}".format(self.folder_path))
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

        folder_infos.sort() # order list names to abc

        for name, count in folder_infos:
            display_text = f"{name:<40} {count:>6}"  # left-align name, right-align number
            self.folder_list.addItem(display_text)

        # Set monospaced font for alignment
        font = QFont("Courier New", 10)
        self.folder_list.setFont(font)

    def folder_clicked(self, item):
        selected_subfolder = os.path.join(self.main_folder, item.text().split()[0])
        print(selected_subfolder)
        self.folder_path = selected_subfolder
        self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
        self.show_batch()


    def make_new_folder(self):
        if self.main_folder:
            dialog = NewFolderNameDialog(self)
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
            self.loader = ImageBatchLoader(os.path.join(self.main_folder, self.subfolders[prev_folder_idx]), batch_size=self.batch_size)
            self.show_batch()


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

            self.folder_path =  subfolders[next_folder_idx]

        print("loaded folder: {}".format(self.folder_path))
        if self.folder_path:
            self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
            self.show_batch()

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
            f"{self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

        self.thread = ImageLoaderThread(batch)
        self.thread.image_loaded.connect(self.add_image_to_layout)
        self.thread.start()

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
            self.batch_info_label.setText(f"{self.loader.current_batch_idx+1} / {self.loader.number_of_batches//1000+1}")


    def previous_batch(self):
        if self.loader:
            self.loader.previous_batch()
            self.show_batch()
            self.batch_info_label.setText(f"{self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}")

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images()
        self.dropped_selected = copy.deepcopy(self.selected_images)

        self.thread = ImageLoaderThread(sorted(self.selected_images))
        self.thread.image_loaded.connect(self.add_image_to_layout)
        self.thread.start()

    def move_selected(self):
        '''output_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder",
                                                                   directory=self.folder_path)
        if output_folder == "" or output_folder is None:
            return

        for img_path in sorted(self.selected_images):
            self.dropped_selected.discard(img_path)
            img_name = os.path.basename(img_path)
            dst_path = os.path.join(output_folder, img_name)
            print("moved from: {}, to: {}".format(img_path, dst_path))
            shutil.move(img_path, dst_path)

        if len(self.dropped_selected) > 0:
            self.selected_images = copy.deepcopy(self.dropped_selected)
            self.show_only_selected()
        else:
            self.selected_images = set()
            self.refresh()'''

        # check if folder laoded
        if self.main_folder is None:
            self.change_info_label("Error: No folder selected")
            return

        #load subfolders
        '''subfolders = [f for f in os.listdir(self.main_folder) if os.path.isdir(os.path.join(self.main_folder, f))]
        subfolders.sort()'''

        if not self.subfolders:
            QtWidgets.QMessageBox.warning(self, "Error", "No subfolders found")
            return

        #create selection dialog
        dialog = FolderSelectionDialog(self)
        if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
            return

        output_folder = os.path.join(self.main_folder, dialog.selected_folder)

        #move images to selected folders
        if self.selected_images:
            for img_path in sorted(self.selected_images):
                self.dropped_selected.discard(img_path)
                img_name = os.path.basename(img_path)
                dst_path = os.path.join(output_folder, img_name)
                self.change_info_label("moved from: {}, to: {}".format(img_path.split('/')[-2], dst_path.split('/')[-2]))
                #print("moved from: {}, to: {}".format(img_path, dst_path))
                shutil.move(img_path, dst_path)
        else:
            self.change_info_label("No selected images found!")

        #check if images left
        if len(self.dropped_selected) > 0:
            self.selected_images = copy.deepcopy(self.dropped_selected)
            self.show_only_selected()
        else:
            self.selected_images = set()
            self.refresh()

    def closeEvent(self, event):
        cleanup_thumbs()
        event.accept()

class NewFolderNameDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Folder Name")
        self.setMinimumSize(300,800)
        self.user_input = None

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.addItems(sign_types)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.list_widget.itemDoubleClicked.connect(self.accept)


    def accept(self):
        selected_folder = self.list_widget.currentItem()
        if selected_folder:
            self.user_input = selected_folder
            super().accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No text entered")


class FolderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Subfolder")
        self.setMinimumSize(400, 500)

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(sorted([f.path.split('/')[-1] for f in os.scandir(os.path.dirname(window.folder_path)) if f.is_dir()]))
        layout.addWidget(self.list_widget)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.selected_folder = None
        self.list_widget.itemDoubleClicked.connect(self.accept)

    def accept(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.selected_folder = selected_item.text()
        super().accept()

def get_dark_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 48))  # Background color
    palette.setColor(QPalette.WindowText, Qt.white)  # Text color
    palette.setColor(QPalette.ButtonText, Qt.black)  # Buttontext color
    return palette

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = ImageMontageApp()
    window.show()
    app.exec_()
