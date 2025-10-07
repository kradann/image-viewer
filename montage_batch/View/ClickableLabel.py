from PyQt5 import QtWidgets, QtCore, QtGui


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    cutRequested = QtCore.pyqtSignal(object, str, object)
    # (pixmap, mode, pos)

    def __init__(self, model , img_path, vm=None, parent=None):
        super().__init__(parent)
        self.model = model
        self.img_path = img_path
        self.selected = False
        self.cut_mode = None
        self.preview_pos = None
        self.vm = vm
        self.setScaledContents(False)

        if self.vm:
            self.cutRequested.connect(self.vm.cut_image)
            self.vm.imageCut.connect(self.on_image_cut)

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
