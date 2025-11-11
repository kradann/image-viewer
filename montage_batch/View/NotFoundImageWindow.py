import logging

from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QFileDialog, QMessageBox
from pathlib import Path


class NotFoundImageWindow(QWidget):
    def __init__(self, not_found_images : list):
        super().__init__()
        self.setWindowTitle("Not Found Images")
        self.resize(500,300)

        self.text = '\n'.join(image_name for image_name in not_found_images)

        self.list_label= QLabel(self.text)

        self.save_button= QPushButton("Save Image Names")
        self.save_button.clicked.connect(self.on_save)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.list_label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_save(self):
        save_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save File")

        if save_path:
            try:
                file_path = Path(save_path) / "not_found_images.txt"

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Image names saved successfully to:\n{file_path}"
                )
            except Exception as e:
                logging.info(e)
                QMessageBox.warning(self, "Error", "Error while creating file")
