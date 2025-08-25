import hashlib
import os
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

refresh = None




class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)
    @staticmethod
    def get_thumb_path(image_path: str, cache_dir=".thumbs") -> str:
        os.makedirs(cache_dir, exist_ok=True)
        hash_name = hashlib.md5(image_path.encode("utf-8")).hexdigest()
        return os.path.join(cache_dir, f"{hash_name}.jpg")
    @staticmethod
    def generate_thumbnail(image_path: str, thumb_path: str, size=(800, 800)):
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img.thumbnail(size, Image.LANCZOS)
                img.save(thumb_path, "JPEG")
        except Exception as e:
            print(f"Thumbnail error for {image_path}: {e}")

    def __init__(self, paths, cache_dir=".thumbs"):
        super().__init__()

        self.paths = paths
        self.cache_dir = cache_dir

    def run(self):
        for idx, path in enumerate(self.paths):
            # print(f"[LoaderThread] Loading: {path}")
            thumb_path = self.get_thumb_path(path, cache_dir=self.cache_dir)

            if not os.path.exists(thumb_path):
                self.generate_thumbnail(path, thumb_path)

            try:
                # img = Image.open(path)
                # img.thumbnail((128, 128))
                pixmap = QtGui.QPixmap(thumb_path)
                # qimage = ImageQt(img)
                # pixmap = QtGui.QPixmap.fromImage(qimage)
                self.image_loaded.emit(idx, pixmap, path)
            except Exception as e:
                print(f"Error loading image {path}: {e}")

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
