import json
import logging

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QMessageBox, QHBoxLayout, QPushButton, QDialog
from pathlib import Path

class LastMoveWindow(QDialog):
    def __init__(self, last_move_text, main_folder):
        super().__init__()
        self.setWindowTitle("Last Move")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.main_folder = main_folder

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.confirm_button)
        layout.addLayout(self.button_layout)
        self.display_log(last_move_text)

    def display_log(self, text):
        try:
            lines = []
            for key, value in text.items():
                lines.append(f"from: {str(Path(key).relative_to(self.main_folder))} to {str(Path(value).relative_to(self.main_folder))}")
            text = '\n'.join(lines)
            self.log_view.setPlainText(text)
            #self.log_view.moveCursor(self.log_view.textCursor().End)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load window:\n{e}")
            logging.log(e)