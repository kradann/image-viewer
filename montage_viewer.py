import glob
import sys, os
import io

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QGridLayout, QPushButton, \
    QFileDialog, QScrollArea
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSlot, pyqtSignal, QObject
from PIL import Image


def pil_to_qpixmap(pil_image):
    """Convert PIL Image to QPixmap"""
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    qimg = QImage.fromData(buffer.getvalue(), "PNG")
    return QPixmap.fromImage(qimg)


class WorkerSignals(QObject):
    finished = pyqtSignal(str, QPixmap)


class ImageLoader(QRunnable):
    def __init__(self, path, signals):
        super().__init__()
        self.path = path
        self.signals = signals

    @pyqtSlot()
    def run(self):
        img = Image.open(self.path)
        img.thumbnail((128, 128))
        pixmap = pil_to_qpixmap(img)
        # qimg = QPixmap.fromImage(QImage(img))
        self.signals.finished.emit(self.path, pixmap)


class ImageGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.row = self.col = 0
        self.selected = set()

    def add_image(self, path, pixmap):
        label = QLabel()
        label.setPixmap(pixmap)
        label.setFixedSize(128, 128)
        label.setStyleSheet("border: 2px solid transparent;")
        label.mousePressEvent = lambda e, p=path, l=label: self.toggle_selection(p, l)
        self.layout.addWidget(label, self.row, self.col)
        self.col += 1
        if self.col >= 5:
            self.col = 0
            self.row += 1

    def toggle_selection(self, path, label):
        if path in self.selected:
            self.selected.remove(path)
            label.setStyleSheet("border: 2px solid transparent;")
        else:
            self.selected.add(path)
            label.setStyleSheet("border: 2px solid red;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Montage Tool")
        self.resize(800, 600)

        self.gallery = ImageGallery()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.gallery)

        self.load_btn = QPushButton("Load Folder")
        self.load_btn.clicked.connect(self.load_folder)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.load_btn)
        self.layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.threadpool = QThreadPool()

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            for path in glob.glob(os.path.join(folder, "*.png")):
                signals = WorkerSignals()
                signals.finished.connect(self.gallery.add_image)
                worker = ImageLoader(path, signals)
                self.threadpool.start(worker)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
