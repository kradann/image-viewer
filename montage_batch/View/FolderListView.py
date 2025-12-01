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

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        #self.setStyleSheet(FOLDER_LIST_STYLE)
        self.setStyleSheet("""
            QListWidget::item:selected {
                background-color: rgba(0, 120, 215, 180);
                color: white;
            }
        """)

        self.hover_timer = QtCore.QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_hover_popup)
        self.pending_label_name = None

        self.hover_help_window = None
        self.last_hovered_label_name = None

        self.folder_list_view_model.highlight_folder_name.connect(self.highlight_by_name)
        #self.main_model.highlight_current_folder_name.connect(self.highlight_by_name)
        self.grid_view_model.load_subfolders_list.connect(self.load_list)
        font = QtGui.QFont("Courier New")
        font.setPointSize(10)
        self.setFont(font)

        self.setMinimumWidth(430)

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
        pass
        #self.help_window = HelpWindow(label_name)
        #self.help_window.show()

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())

        if item:
            label_name = item.text().split()[0]

            #Check if mouse moved on same label
            if self.last_hovered_label_name != label_name:
                self.last_hovered_label_name = label_name
                self.pending_label_name = label_name
                self.hover_timer.start(300)

        else:
            if not self.hover_help_window:
                self.hover_timer.stop()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        # stop timer
        self.hover_timer.stop()


        if self.hover_help_window:
            QtCore.QTimer.singleShot(200, self.check_and_close_popup)

        super().leaveEvent(event)

    def check_and_close_popup(self):
        """Check if mouse is over popup before closing"""
        if self.hover_help_window and not self.hover_help_window.underMouse():
            self.hover_help_window.close()
            self.hover_help_window = None

    def show_hover_popup(self):
        if self.pending_label_name:
            if self.hover_help_window:
                self.hover_help_window.close()
            self.hover_help_window = HelpWindow(self.pending_label_name, parent=self)

            if self.hover_help_window.has_content:
                pos = QtGui.QCursor.pos()
                self.hover_help_window.move(pos + QtCore.QPoint(20,20))
                self.hover_help_window.show()
            else:
                self.hover_help_window = None
            self.pending_label_name = None
