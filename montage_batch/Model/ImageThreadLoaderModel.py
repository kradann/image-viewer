import hashlib
import os
from pathlib import Path

from PIL import Image
from PyQt5 import QtCore, QtGui




class ImageLoaderThread(QtCore.QThread):
    image_loaded = QtCore.pyqtSignal(int, QtGui.QPixmap, str)
    @staticmethod
    def cleanup_thumbs():
        print(13)
        thumbs_dir = Path(__file__).resolve().parent.parent / ".thumbs"
        if thumbs_dir.exists() and thumbs_dir.is_dir():
            for f in thumbs_dir.iterdir():
                try:
                    if f.is_file():
                        f.unlink()
                except Exception as e:
                    print(f"Failed to delete {f}: {e}")

    @staticmethod
    def get_thumb_path(image_path: str, cache_dir: str = ".thumbs") -> Path:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        hash_name = hashlib.md5(str(image_path).encode("utf-8")).hexdigest()
        return cache_path / f"{hash_name}.jpg"

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
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        for idx, path in enumerate(self.paths):
            if not self._is_running:
                break
            # print(f"[LoaderThread] Loading: {path}")
            thumb_path = str(self.get_thumb_path(path, cache_dir=self.cache_dir))
            if not os.path.exists(thumb_path):
                self.generate_thumbnail(path, thumb_path)
            try:
                # img = Image.open(path)
                # img.thumbnail((128, 128))
                pixmap = QtGui.QPixmap(str(thumb_path))
                # qimage = ImageQt(img)
                # pixmap = QtGui.QPixmap.fromImage(qimage)
                if self._is_running:
                    self.image_loaded.emit(idx, pixmap, str(path))
            except Exception as e:
                print(f"Thumb path: {thumb_path}, Exists? {Path(thumb_path).exists()}")
                print(f"Error loading image {path}: {e}")