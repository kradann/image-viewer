import hashlib
import os
from pathlib import Path

from PIL import Image
from PyQt5 import QtCore, QtGui


class ImageBatchLoader(object):
    def __init__(self, source, batch_size=20, start_batch_idx=0):
        self.batch_size = batch_size
        self.image_paths = self.collect_image_paths(source)
        #pprint.pprint(self.image_paths)
        self.current_batch_idx = start_batch_idx
        self.label = None
        self.number_of_batches = len(self.image_paths)

    def collect_image_paths(self, source):
        image_paths = []
        if isinstance(source, list):
            for region in source:
                region_path = Path(region)
                for file in region_path.rglob("*"):
                    if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                        image_paths.append(file)
        else:
            source_path = Path(source)
            for file in source_path.rglob("*"):
                if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                    image_paths.append(file)
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
        
class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)
    @staticmethod
    def get_thumb_path(image_path: str, cache_dir=".thumbs") -> str:
        os.makedirs(cache_dir, exist_ok=True)
        hash_name = hashlib.md5(str(image_path).encode("utf-8")).hexdigest()
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
                self.image_loaded.emit(idx, pixmap, str(path))
            except Exception as e:
                print(f"Thumb path: {thumb_path}, Exists? {Path(thumb_path).exists()}")
                print(f"Error loading image {path}: {e}")