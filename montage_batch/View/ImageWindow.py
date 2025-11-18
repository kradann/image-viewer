from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5 import QtCore


class ImageWindow(QDialog):
    def __init__(self, image_path):
        super().__init__()

        self.setWindowTitle("Image Window")
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.image_path = str(image_path)
        self.pixmap = QPixmap(self.image_path)

        self.label = QLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setPixmap(self.pixmap)
        self.label.setMinimumWidth(self.pixmap.width())
        self.label.setMinimumHeight(self.pixmap.height())
        self.label.setScaledContents(False)

        self.path_label = QLabel(self.image_path)
        self.path_label.setWordWrap(True)
        self.path_label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.path_label)

    def resizeEvent(self, event):
        if not self.pixmap.isNull():
            available_width = self.width()
            available_height = self.height() - self.path_label.height()

            scaled = self.pixmap.scaled(
                available_width,
                available_height,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            self.label.setPixmap(scaled)

        super().resizeEvent(event)

