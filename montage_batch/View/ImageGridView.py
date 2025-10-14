from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal

from ViewModel.ClickableViewModel import ClickableLabel
from ViewModel.ImageGridViewModel import  ImageGridViewModel
from Model.ClickableModel import Clickable


class ImageGridView(QtWidgets.QWidget):
    AddImage = pyqtSignal(Clickable, int, int)

    def __init__(self, parent=None, mainmodel=None, gridviewmodel=None):
        super().__init__()
        self.setMouseTracking(True)
        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()
        self.drag_selecting = False
        self.parent_app = parent
        self.clicked_label = None
        self.thumbnail_size = 150, 150
        self.last_width = None
        self.mainModel = mainmodel
        self.GridViewModel = gridviewmodel
        self.ClickableModel = Clickable
        self.GridViewModel.imageReady.connect(self.add_image_to_layout)
        self.GridViewModel.batchShouldBeShown.connect(self.show_batch)
        #self.viewmodel.infoMessage.connect(self.change_info_label)

    def mousePressEvent(self, event):
        # print(1)
        if event.button() == QtCore.Qt.LeftButton:
            self.origin = event.pos()
            self.clicked_label = self.label_at(event.pos())  # select which image was clicked
            self.drag_selecting = True
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubber_band.show()
        # elif event.button() == QtCore.Qt.RightButton:
        # self.show_context_menu(event.pos())

    def mouseMoveEvent(self, event):
        if self.drag_selecting:
            # print(4)
            rect = QtCore.QRect(self.origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.drag_selecting:
            self.rubber_band.hide()
            selection_rect = self.rubber_band.geometry()
            drag_distance = (event.pos() - self.origin).manhattanLength()

            if drag_distance < 40 and self.clicked_label:  # no drag, just clicking
                self.clicked_label.selected = not self.clicked_label.selected
                self.clicked_label.add_red_boarder()
                print(self.clicked_label.img_path)
                self.GridViewModel.toggle_selection(self.clicked_label)
            else:
                # rubber band kijelölés
                for label in self.GridViewModel.labels:
                    label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
                    label_rect = QtCore.QRect(label_pos, label.size())
                    if selection_rect.intersects(label_rect):
                        label.selected = not label.selected
                        label.add_red_boarder()
                        self.GridViewModel.toggle_selection(label)

            self.drag_selecting = False
            self.clicked_label = None

    def label_at(self, pos):
        for label in self.GridViewModel.labels:
            label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
            label_rect = QtCore.QRect(label_pos, label.size())
            if label_rect.contains(pos):
                return label
        return None


    def add_image_to_layout(self, row, col, path, pixmap, is_selected):
        #print(path, row, col)
        label = ClickableLabel(img_path=path, mainmodel=self.mainModel)
        label.setFixedSize(*self.thumbnail_size)
        label.setPixmap(
            pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        label.setScaledContents(False)

        label.clicked.connect(lambda: self.vm.toggle_selection(path))

        if is_selected:
            label.selected = True
            label.add_red_boarder()

        self.GridViewModel.add_image_to_grid(label, row, col)

    def on_load_folder(self, parent=None):
        if parent is None:
            parent = self
        selected_folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if selected_folder_path:
            self.GridViewModel.load_main_folder(selected_folder_path)

    def show_batch(self):
        self.GridViewModel.load_batch()



