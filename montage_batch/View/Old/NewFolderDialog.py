from PyQt5 import QtWidgets


class NewFolderNameDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Folder Name")
        self.setMinimumSize(300, 800)
        self.user_input = None

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.list_widget = QtWidgets.QListWidget(self)
        #self.list_widget.addItems(sign_types) #import cycle
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.list_widget.itemDoubleClicked.connect(self.accept)

    def accept(self):
        selected_folder = self.list_widget.currentItem()
        if selected_folder:
            self.user_input = selected_folder
            super().accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No text entered")