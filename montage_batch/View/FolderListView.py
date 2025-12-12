from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QListWidgetItem

from View.HelpWindow import HelpWindow

def _apply_status_color(item, status):
    transparency = 125
    if status == "not_done":
        item.setBackground(QtGui.QColor(255, 0, 0, transparency))
    elif status == "in_progress":
        item.setBackground(QtGui.QColor(255, 255, 0, transparency))
    elif status == "done":
        item.setBackground(QtGui.QColor(0, 255, 0, transparency))
    else:
        item.setBackground(QtGui.QColor("#303436"))


class FolderListWidget(QtWidgets.QListWidget):
    def __init__(self, main_model,grid_view_model, parent=None, folder_list_view_model=None):
        super().__init__(parent)
        self.main_model = main_model
        self.grid_view_model = grid_view_model
        self.folder_list_view_model = folder_list_view_model
        self.highlight_color = QtGui.QColor(0, 120, 215, 180)
        self.current_item_name = None
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        #self.setStyleSheet(FOLDER_LIST_STYLE)
        self.setStyleSheet("""
            QListWidget::item:selected {
                background-color: rgba(0, 120, 215, 180);
                color: white;
            }
        """)

        self.help_window = None

        self.folder_list_view_model.highlight_folder_name.connect(self.highlight_by_name)
        #self.main_model.highlight_current_folder_name.connect(self.highlight_by_name)
        self.grid_view_model.load_subfolders_list.connect(self.load_list)
        font = QtGui.QFont("Courier New")
        font.setPointSize(10)
        self.setFont(font)

        #self.setMinimumWidth(430)

    def on_status_changed(self, folder_name, status):
        item = self._find_item_by_name(folder_name)
        if item:
            _apply_status_color(item, status)

    def apply_loaded_statuses(self, statuses):
        for i in range(self.count()):
            item = self.item(i)
            name = item.text().split()[0]
            status = statuses.get(name)
            self._apply_status_color(item, status)

    def _find_item_by_name(self, name):
        for i in range(self.count()):
            it = self.item(i)
            if it.text().split()[0] == name:
                return it
        return None

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
        menu = QtWidgets.QMenu()
        for status in ["Not Done", "In Progress", "Done"]:
            action = menu.addAction(status)
        remove = menu.addAction("Remove Status")
        help = menu.addAction("Help")
        chosen = menu.exec_(self.mapToGlobal(pos))

        if chosen:
            name = item.text().split()[0]
            if chosen.text() == "Remove Status":
                self.vm.set_status(name, None)
            elif chosen == help:
                self.show_help_window(item.text().split()[0])
            else:
                self.vm.set_status(name, chosen.text().lower().replace(" ", "_"))

    def highlight_by_name(self, name):
        item = self._find_item_by_name(name)
        if item:
            item.setBackground(QtGui.QColor(0, 120, 215, 180))
            self.setCurrentItem(item)
            self.current_item_name = name
            self.scrollToItem(item)
        else:
            self.current_item_name = None
            self.setCurrentItem(None)


    def load_list(self, subfolders):
        self.clear()
        for folder in subfolders:
            display_text = f"{folder:<45} {subfolders[folder]:>7}"  # left-align name, right-align number
            item = QListWidgetItem(display_text)
            self.addItem(item)

        if hasattr(self, "current_item_name") and self.current_item_name:
            self.highlight_by_name(self.current_item_name)


    def show_help_window(self,label_name):
        self.help_window = HelpWindow(label_name)


