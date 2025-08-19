import hashlib
import os
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

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


class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)

    def __init__(self, paths, cache_dir=".thumbs"):
        super().__init__()

        self.paths = paths
        self.cache_dir = cache_dir

    def run(self):
        for idx, path in enumerate(self.paths):
            # print(f"[LoaderThread] Loading: {path}")
            thumb_path = get_thumb_path(path, cache_dir=self.cache_dir)

            if not os.path.exists(thumb_path):
                generate_thumbnail(path, thumb_path)

            try:
                # img = Image.open(path)
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
            new_path = "{}_{}.{}".format(first_part, name_idx, ext)
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
        # print(1)
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.clicked_label = self.label_at(event.pos())  # select which image was clicked
            self.drag_selecting = True
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubber_band.show()
        # elif event.button() == QtCore.Qt.RightButton:
        # self.show_context_menu(event.pos())

    def mouseMoveEvent(self, event):
        if self.drag_selecting:
            # print(4)
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
