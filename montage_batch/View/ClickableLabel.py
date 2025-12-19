from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap

from View.ImageWindow import ImageWindow


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    cutRequested = QtCore.pyqtSignal(object,QPixmap , str, QPoint)

    # (pixmap, mode, pos)

    def __init__(self,img_path, vm=None, main_model=None , parent=None, grid_view_model=None):
        super().__init__(parent)

        self.img_path = img_path
        self.selected = False
        self.cut_mode = None
        self.preview_pos = None
        self.vm = vm
        self.grid_view_model = grid_view_model
        self.main_model = main_model
        self.setScaledContents(False)
        self.setMouseTracking(True)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.image_window = None
        #self.pixmap = None


    def mouseMoveEvent(self, event):
        if self.cut_mode:
            self.preview_pos = event.pos()
            self.update()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.show_context_menu(event.pos())
        elif event.button() == QtCore.Qt.LeftButton and self.cut_mode and self.preview_pos:
            print(type(event.pos()))
            self.cutRequested.emit(self, self.pixmap(), self.cut_mode, event.pos())
            self.grid_view_model.on_load_folder_by_name(self.img_path.parent.name)
        else:
            super().mousePressEvent(event)

    def add_red_boarder(self):
        self.setStyleSheet("border: 3px solid red;" if self.selected else "")
        self.repaint()
        self.update()


    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cut_mode and self.preview_pos:
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashLine)
            painter.setPen(pen)

            if self.cut_mode == 'vertical':
                painter.drawLine(self.preview_pos.x(), 0, self.preview_pos.x(), self.height())
            else:  # horizontal
                painter.drawLine(0, self.preview_pos.y(), self.width(), self.preview_pos.y())

            painter.end()

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu()
        vertical_cut = menu.addAction("Vertical Cut")
        horizontal_cut = menu.addAction("Horizontal Cut")
        open_image = menu.addAction("Open Image")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == vertical_cut:
            self.cut_mode = 'vertical'
        elif action == horizontal_cut:
            self.cut_mode = 'horizontal'
        elif action == open_image:
            self.image_window = ImageWindow(self.img_path)
            self.image_window.show()





