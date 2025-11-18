from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QMessageBox
from pathlib import Path

class LogWindow(QWidget):
    def __init__(self, log_file_path):
        super().__init__()
        self.setWindowTitle("Log Viewer")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.log_file_path = Path(log_file_path)
        print(self.log_file_path)
        print(2)
        if self.log_file_path.exists():
            print(3)
            self.display_log(self.log_file_path)

    def display_log(self, path: Path):
        try:
            text = path.read_text(encoding='utf-8')
            self.log_view.setPlainText(text)
            #self.log_view.moveCursor(self.log_view.textCursor().End)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read log file:\n{e}")