import copy
import io
import json
import os
import shutil
from time import sleep
from typing import Union

from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QPushButton, QShortcut, QMenu, QAction
from PyQt5.QtGui import QKeySequence, QFont, QWheelEvent
from libdnf.utils import NullLogger

global window

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


class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths

    def run(self):
        for idx, path in enumerate(self.paths):
            try:
                img = Image.open(path)
                # img.thumbnail((128, 128))
                pixmap = pil_to_qpixmap(img)
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

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.cut_mode and self.preview_pos:
                self.cut_at_position(self.preview_pos)
            else:
                self.selected = not self.selected
                self.add_red_boarder()
                self.clicked.emit()

        elif event.button() == QtCore.Qt.RightButton:
            self.show_context_menu(event.pos())

    def add_red_boarder(self):
        self.setStyleSheet("border: 3px solid red;" if self.selected else "")

    def mouseMoveEvent(self, event):
        if self.cut_mode:
            self.preview_pos = event.pos()
            self.update()

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        vertical_cut = menu.addAction("Vertical Cut")
        horizontal_cut = menu.addAction("Horizontal Cut")
        action = menu.exec_(self.mapToGlobal(pos))

        if action == vertical_cut:
            self.cut_mode = 'vertical'
        elif action == horizontal_cut:
            self.cut_mode = 'horizontal'

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


class FolderListWidget(QtWidgets.QListWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
            self.left_click_handler = None
            self.right_click_handler = None
            self.status_dict = dict()

        def mousePressEvent(self, event):
            item = self.itemAt(event.pos())
            if item is not None:
                if event.button() == Qt.LeftButton:
                    if self.left_click_handler:
                        self.left_click_handler(item)
                elif event.button() == Qt.RightButton:
                    if self.right_click_handler:
                        self.right_click_handler(item)
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
            remove = menu.addAction("Remove priority")

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
                item.setBackground(QtGui.QColor("white"))
                self.status_dict[item_text.split()[0]] = None

        def load_priority_action(self):
            main_folder = self.window().main_folder
            if main_folder is not None:
                load_path = os.path.join(main_folder, main_folder.split('/')[-1] + "_priority_action.json")
                if not os.path.exists(load_path):
                    QtWidgets.QMessageBox.warning(self, "Hiba", f"A fájl nem található:\n{load_path}")
                    return

                try:
                    with open(load_path, "r") as f:
                        loaded_priority_action = json.load(f)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni:\n{e}")
                    return

            self.status_dict = loaded_priority_action
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
                    item.setBackground(QtGui.QColor("white"))
            self.window().change_info_label("Priority Loaded!")



        def save_priority_action(self):
            main_folder = self.window().main_folder
            if main_folder is not None:
                save_path = os.path.join(main_folder, main_folder.split('/')[-1] + "_priority_action.json")

                try:
                    with open(save_path, "w") as f:
                        json.dump(self.status_dict, f, indent=4)
                    QtWidgets.QMessageBox.information(self, "Siker", f"Státuszok elmentve ide:\n{save_path}")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni:\n{e}")
            self.window().change_info_label("Priority Saved!")




class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Batch Viewer")
        self.resize(1600, 900)
        self.num_of_col = 6
        self.batch_size = 1000
        self.thumbnail_size = 150, 150

        self.loader = None
        self.folder_path = None
        self.main_folder = None # Folder that stores the subfolders
        self.thread = None
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
        #self.button_layout = QtWidgets.QHBoxLayout()

        # Left Panel
        self.left_panel = QtWidgets.QHBoxLayout()

        self.folder_list = FolderListWidget()
        file_menu = self.menu_bar.addMenu("File")
        load_folder_action = QtWidgets.QAction("Load Folder",self)
        load_folder_action.triggered.connect(self.load_folder)
        file_menu.addAction(load_folder_action)

        priority_menu = self.menu_bar.addMenu("Priority")

        load_priority_action = QtWidgets.QAction("Load Priority", self)
        load_priority_action.triggered.connect(self.folder_list.load_priority_action)
        priority_menu.addAction(load_priority_action)

        save_priority_action = QtWidgets.QAction("Save Priority", self)
        save_priority_action.triggered.connect(self.folder_list.save_priority_action)
        priority_menu.addAction(save_priority_action)
        #self.folder_list.left_click_handler = self.folder_clicked
        #self.folder_list.right_click_handler = self.folder_right_clicked
        self.folder_list.setMinimumWidth(400)
        self.folder_list.itemClicked.connect(self.folder_clicked)

        # Scroll area (middle panel)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setMinimumWidth(1000)
        self.vertical_value = 0
        self.image_widget = QtWidgets.QWidget()
        self.image_layout = QtWidgets.QGridLayout(self.image_widget)
        self.scroll_area.setWidget(self.image_widget)
        self.scroll_area.setWidgetResizable(True)

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
        self.add_button("Next Folder", self.next_folder)
        self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Select all", self.select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)

        self.button_layout_wrapper.addWidget(self.batch_info_label)

        self.info_label = QtWidgets.QLabel("Bottom Batch Info")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 20px;")
        self.outer_layout.addWidget(self.info_label)


    def add_button(self, name: str, func, shortcut: Union[str, tuple] = None):
        button = QtWidgets.QPushButton(name)
        button.setFont(QFont("Arial", 10))
        button.setFixedSize(160, 40)
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
        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        print("loaded folder: {}".format(self.folder_path))
        if self.folder_path:
            self.main_folder = self.folder_path
            self.load_subfolders(self.folder_path)
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

    def change_info_label(self, text=None, text_color="black"):
        label = self.window().info_label
        label.setText(text)
        if text_color:
            label.setStyleSheet(f"color: {text_color}; font-size: 20px;")
        # Save the current text
        current_text = text
        # After 5 seconds, clear ONLY IF the text hasn't changed in the meantime
        QTimer.singleShot(5000, lambda: label.setText("") if label.text() == current_text else None)

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
            self.vertical_value = self.scroll_area.verticalScrollBar().value()
            self.loader = ImageBatchLoader(self.folder_path,
                                           batch_size=self.batch_size,
                                           start_batch_idx=self.loader.current_batch_idx)
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

    def select_all(self):
        for label in self.labels:
            label.selected = True
            self.selected_images.add(label.img_path)
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
        output_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder",
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
            self.refresh()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = ImageMontageApp()
    window.show()
    app.exec_()
