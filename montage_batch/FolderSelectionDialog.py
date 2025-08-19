from PyQt5 import QtWidgets
import os
from PyQt5.QtWidgets import QPushButton


class FolderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, folder_path=""):
        super().__init__(parent)
        self.setWindowTitle("Select Subfolder")
        self.setMinimumSize(400, 500)
        self.folder_path = folder_path

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(
            sorted([f.path.split('/')[-1] for f in os.scandir(os.path.dirname(self.folder_path)) if f.is_dir()]))
        layout.addWidget(self.list_widget)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.selected_folder = None
        self.list_widget.itemDoubleClicked.connect(self.accept)

    def accept(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.selected_folder = selected_item.text()
        super().accept()
