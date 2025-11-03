from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QPushButton

class FolderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, preferred=None, grid_view_model=None):
        super().__init__()
        self.grid_view_model = grid_view_model
        self.setWindowTitle("Select Subfolder")
        self.setMinimumSize(400, 700)

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(self.grid_view_model.get_current_labels())
        layout.addWidget(self.list_widget)
        items = self.list_widget.findItems(preferred, QtCore.Qt.MatchExactly)
        if items:
            item = items[0]
            row = self.list_widget.row(item)
            take = self.list_widget.takeItem(row)
            self.list_widget.insertItem(0, take)
            take.setBackground(QtGui.QColor(0, 215, 120, 180))

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
