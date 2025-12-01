from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
from pathlib import Path
import json




class HelpWindow(QWidget):
    def __init__(self, label_name, parent=None):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover)

        description_json_path = Path(__file__).parent.parent / "resources/description.json" if Path(
            __file__).parent.parent / "resources/description.json" else None
        self.label_name = label_name
        self.description_text = None
        self.images = None
        self.text = None
        self.description = None
        self.has_content = False
        self.label_key = None


        with open(description_json_path, 'r') as json_data:
            self.description = json.load(json_data)

        if self.description is not None:
            self.text = self.description.get(self.label_name )
            if self.text is None:
                for key in self.description:
                    if "{}" in key:
                        base = key.replace("{}", "")
                        print(base)
                        print(self.label_name.startswith(base))
                        if self.label_name.startswith(base):
                            self.text = self.description[key]
                            self.label_key = key

                self.label_name  = self.label_key




        self.folder_path = Path(__file__).parent.parent / 'resources/examples' / self.label_name  if (Path(__file__).parent.parent / 'resources/examples' / self.label_name ).exists() else None

        if self.folder_path:
            self.images = [file for file in self.folder_path.iterdir()]
            if self.images:
                self.has_content = True
                self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel(self.label_name)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        # Create a scroll area to hold the images
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)

        # Load and display images
        for image_path in self.images:
            image_label = QLabel(self)
            pixmap = QPixmap(str(image_path))

            # Scale the pixmap to a fixed size while keeping the aspect ratio
            scaled_pixmap = pixmap.scaled(200, 200, aspectRatioMode=QtCore.Qt.KeepAspectRatio,
                                          transformMode=QtCore.Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            scroll_layout.addWidget(image_label)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Label space below images
        if self.text is not None:
            self.description_text = QLabel(self.text, self)

        if self.description_text:
            layout.addWidget(self.description_text)

        self.setLayout(layout)

    def leaveEvent(self, event):
        """Close the window when mouse leaves"""
        QtCore.QTimer.singleShot(100, self.close_if_not_hovered)
        super().leaveEvent(event)

    def close_if_not_hovered(self):
        """Delayed close to avoid flickering"""
        if not self.underMouse():
            self.close()