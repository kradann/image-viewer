from PIL.ImageChops import offset
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore
from pathlib import Path
import json




class HelpWindow(QWidget):
    def __init__(self, label_name, parent=None):
        super().__init__()
        self.setMouseTracking(True)

        description_json_path = Path(__file__).parent.parent / "resources/description.json" if Path(
            __file__).parent.parent / "resources/description.json" else None
        self.label_name = label_name
        self.description_text = None
        self.example_images = None
        self.counterexample_images = None
        self.text = None
        self.description = None
        self.label_key = None
        self.example_folder_path = None
        self.counterexample_folder_path = None
        self.has_content = False

        if description_json_path.exists():
            with open(description_json_path, 'r') as json_data:
                self.description = json.load(json_data)
        else:
            QMessageBox.warning(self, "Description JSON", "No description JSON found")

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



        if self.label_name:
            self.example_folder_path = Path(__file__).parent.parent / 'resources/examples' / self.label_name  if (Path(__file__).parent.parent / 'resources/examples' / self.label_name).exists() else None
            self.counterexample_folder_path = Path(__file__).parent.parent / 'resources/counterexamples' / self.label_name  if (Path(__file__).parent.parent / 'resources/counterexamples' / self.label_name).exists() else None

        if self.example_folder_path:
            self.example_images = [file for file in self.example_folder_path.iterdir()]

        if self.counterexample_folder_path:
            self.counterexample_images = [file for file in self.counterexample_folder_path.iterdir()]

        if (self.example_images or self.counterexample_images or self.text) and self.description :
            self.init_ui()
            self.show()
        else:
            QMessageBox.warning(self, "No description", f"No Description found for {label_name}")

    def init_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel(self.label_name)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        print("Examples:", self.example_images)
        print("CounterExamples:", self.counterexample_images)
        print("text:", self.text)

        # Create a scroll area to hold the images
        example_scroll_area = QScrollArea(self)
        example_scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)

        # Load and display images
        for image_path in self.example_images:
            image_label = QLabel(self)
            pixmap = QPixmap(str(image_path))

            # Scale the pixmap to a fixed size while keeping the aspect ratio
            scaled_pixmap = pixmap.scaled(200, 200, aspectRatioMode=QtCore.Qt.KeepAspectRatio,
                                          transformMode=QtCore.Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            scroll_layout.addWidget(image_label)

        example_scroll_area.setWidget(scroll_content)
        layout.addWidget(example_scroll_area)

        # Create a scroll area to hold the images
        counterexample_scroll_area = QScrollArea(self)
        counterexample_scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)

        # Load and display images
        for image_path in self.counterexample_images:
            image_label = QLabel(self)
            pixmap = QPixmap(str(image_path))

            # Scale the pixmap to a fixed size while keeping the aspect ratio
            scaled_pixmap = pixmap.scaled(200, 200, aspectRatioMode=QtCore.Qt.KeepAspectRatio,
                                          transformMode=QtCore.Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            scroll_layout.addWidget(image_label)

        counterexample_scroll_area.setWidget(scroll_content)
        layout.addWidget(counterexample_scroll_area)

        # Label space below images
        if self.text is not None:
            self.description_text = QLabel(self.text, self)

        if self.description_text:
            layout.addWidget(self.description_text)

        self.setLayout(layout)
