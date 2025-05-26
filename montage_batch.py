import copy
import io
import os
import shutil
from typing import Union

from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QPushButton, QShortcut, QMenu, QAction
from PyQt5.QtGui import QKeySequence, QFont, QWheelEvent

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


class ImageMontageApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Batch Viewer")
        self.resize(1000, 800)
        self.num_of_col = 6
        self.batch_size = 1000
        self.thumbnail_size = 150, 150

        self.loader = None
        self.folder_path = None
        self.thread = None
        self.labels = list()
        self.selected_images = set()
        self.dropped_selected = set()

        # Layouts
        self.layout = QtWidgets.QVBoxLayout(self)
        self.button_layout = QtWidgets.QHBoxLayout()

        # Buttons
        self.add_button("Load Folder", self.load_folder)
        self.add_button("Next Folder", self.next_folder)
        self.add_button("Previous Batch", self.previous_batch)
        self.add_button("Next Batch", self.next_batch)
        self.add_button("Current Batch", self.show_batch)
        self.add_button("Select all", self.select_all)
        self.add_button("Selected Check", self.show_only_selected)
        self.add_button("Move Selected Images", self.move_selected)
        self.add_button("Reload scrolling", self.load_v_value)


        # Scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.vertical_value = 0
        self.image_widget = QtWidgets.QWidget()
        self.image_layout = QtWidgets.QGridLayout(self.image_widget)
        self.scroll_area.setWidget(self.image_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

    def add_button(self, name: str, func, shortcut: Union[str, tuple] = None):
        button = QtWidgets.QPushButton(name)
        button.setFont(QFont("Arial", 8))
        self.layout.addWidget(button)
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
            self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
            self.show_batch()
            self.setWindowTitle("Image Batch Viewer ({})".format(os.path.basename(self.folder_path)))

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
            self.setWindowTitle("Image Batch Viewer ({})".format(os.path.basename(self.folder_path)))

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

    def previous_batch(self):
        if self.loader:
            self.loader.previous_batch()
            self.show_batch()

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
