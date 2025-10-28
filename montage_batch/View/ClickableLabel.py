from PyQt5 import QtWidgets, QtCore, QtGui


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    cutRequested = QtCore.pyqtSignal(object, str, object)

    # (pixmap, mode, pos)

    def __init__(self,img_path, vm=None, main_model=None , parent=None):
        super().__init__(parent)

        self.img_path = img_path
        self.selected = False
        self.cut_mode = None
        self.preview_pos = None
        self.vm = vm
        self.main_model = main_model
        self.setScaledContents(False)
        self.setMouseTracking(True)
        self.setFrameShape(QtWidgets.QFrame.Box)
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
            self.vm.cut_image(self,self.pixmap(), self.cut_mode, event.pos())
            self.main_model.load_folder_by_folder_name(self.img_path.parent.name)
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
        info = menu.addAction("Info")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == vertical_cut:
            self.cut_mode = 'vertical'
        elif action == horizontal_cut:
            self.cut_mode = 'horizontal'





