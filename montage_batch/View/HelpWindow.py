from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
from pathlib import Path
import json




class HelpWindow(QWidget):
    def __init__(self, label_name):
        super().__init__()

        self.folder_path = Path(__file__).parent.parent / 'resources/examples' / label_name if (Path(__file__).parent.parent / 'resources/examples' / label_name).exists() else None

        self.images = [file for file in self.folder_path.iterdir()]

        print(self.folder_path)
        print(self.images)
        description_json_path = Path(__file__).parent.parent / "resources/description.json" if Path(__file__).parent.parent / "resources/description.json" else None
        self.description = None
        with open(description_json_path, 'r') as json_data:
            self.description = json.load(json_data)
        self.text = self.description[label_name] if self.description is not None else None
        self.label = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

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
            self.label = QLabel(self.text, self)
        layout.addWidget(self.label)

        self.setLayout(layout)