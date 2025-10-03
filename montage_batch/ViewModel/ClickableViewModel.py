from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal


class ClickableLabel(QtWidgets.QLabel):
    clicked = pyqtSignal()
    imageCut = pyqtSignal(str, str, str)
    imagePathChanged = pyqtSignal(str)
    # (pixmap, mode, pos)

    def __init__(self, img_path, mainmodel=None, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self.selected = False
        self.cut_mode = None
        self.preview_pos = None
        self.mainmodel = mainmodel
        self.setFrameShape(QtWidgets.QFrame.Box)


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.show_context_menu(event.pos())
        elif event.button() == QtCore.Qt.LeftButton and self.cut_mode and self.preview_pos:
            self.cutRequested.emit(self.pixmap(), self.cut_mode, event.pos())
        else:
            super().mousePressEvent(event)

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        vertical_cut = menu.addAction("Vertical Cut")
        horizontal_cut = menu.addAction("Horizontal Cut")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == vertical_cut:
            self.cut_mode = 'vertical'
        elif action == horizontal_cut:
            self.cut_mode = 'horizontal'

    def on_image_cut(self, original, new, thumb_path):
        self.cut_mode = None
        self.preview_pos = None
        self.setPixmap(QtGui.QPixmap(thumb_path))
        self.update()

    def add_red_boarder(self):
        self.setStyleSheet("border: 3px solid red;" if self.selected else "")
