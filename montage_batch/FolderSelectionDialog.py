from PyQt5 import QtWidgets, QtCore, QtGui
import os
from PyQt5.QtWidgets import QPushButton



class FolderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, preffered=None, sign_types=None):
        super().__init__(parent)
        self.setWindowTitle("Select Subfolder")
        self.setMinimumSize(400, 500)
        self.sign_types = sign_types

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(self.sign_types)
        layout.addWidget(self.list_widget)
        items = self.list_widget.findItems(preffered, QtCore.Qt.MatchExactly)
        if items:
            item = items[0]
            row = self.list_widget.row(item)
            take = self.list_widget.takeItem(row)
            self.list_widget.insertItem(0, take)
            take.setBackground(QtGui.QColor(0, 120, 215, 180))

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
