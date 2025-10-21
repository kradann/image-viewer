import time
from pathlib import Path

from PyQt5 import Qt, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal

from View.Styles import GRID_PATH_STYLE
from View.ClickableLabel import ClickableLabel
from ViewModel.ClickableViewModel import ClickableViewModel
from ViewModel.ImageGridViewModel import  ImageGridViewModel



class ImageGridView(QtWidgets.QWidget):
    AddImage = pyqtSignal(ClickableLabel, int, int)
    change_info_label = pyqtSignal(str)

    def __init__(self, parent=None, main_model=None, grid_view_model=None):
        super().__init__()
        self.setMouseTracking(True)
        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QtCore.QPoint()
        self.drag_selecting = False
        self.parent_app = parent
        self.clicked_label = None
        self.thumbnail_size = 150, 150
        self.last_width = None
        self.main_model = main_model
        self.grid_view_model = grid_view_model
        self.clickable_viewmodel = ClickableViewModel
        self.grid_view_model.image_ready.connect(self.add_image_to_layout)
        self.grid_view_model.batch_should_be_shown.connect(self.show_batch)
        #self.viewmodel.infoMessage.connect(self.change_info_label)

    def mousePressEvent(self, event):
        # print(1)
        if event.button() == QtCore.Qt.LeftButton:
            self.origin = event.pos()
            self.clicked_label = self.label_at(event.pos())  # select which image was clicked
            self.drag_selecting = True
            self.rubber_band.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubber_band.show()
        elif event.button() == QtCore.Qt.RightButton:
            self.show_context_menu(event.pos())

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
                if hasattr(self.clicked_label, 'image_label'):
                    self.clicked_label = self.clicked_label.image_label
                self.clicked_label.selected = not self.clicked_label.selected
                self.clicked_label.add_red_boarder()

                self.grid_view_model.toggle_selection(self.clicked_label.img_path)
            else:
                # rubber band kijelölés
                for label in self.grid_view_model.labels:
                    if hasattr(label, 'image_label'):
                        label = label.image_label
                    label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
                    label_rect = QtCore.QRect(label_pos, label.size())
                    if selection_rect.intersects(label_rect):
                        label.selected = not label.selected
                        label.add_red_boarder()
                        self.grid_view_model.toggle_selection(label.img_path)

            self.drag_selecting = False
            self.clicked_label = None

    def label_at(self, pos):
        for label in self.grid_view_model.labels:
            label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
            label_rect = QtCore.QRect(label_pos, label.size())
            if label_rect.contains(pos):
                return label
        return None


    def add_image_to_layout(self, row, col, path, pixmap, is_selected):
        container = QtWidgets.QWidget()

        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.setAlignment(QtCore.Qt.AlignTop)

        path_label = QtWidgets.QLabel(str(path).split('/')[-2].replace('_','_\u200b')) #Added white space to be able to cut it into 2 lines
        path_label.setAlignment(QtCore.Qt.AlignCenter)
        path_label.setWordWrap(True)
        path_label.setFixedWidth(self.thumbnail_size[0])
        path_label.setMaximumHeight(30)
        path_label.setStyleSheet(GRID_PATH_STYLE)

        label = ClickableLabel(img_path=Path(path), vm=self.clickable_viewmodel, main_model=self.main_model)
        label.setFixedSize(*self.thumbnail_size)
        label.setPixmap(
            pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        label.setScaledContents(False)
        label.clicked.connect(lambda: self.vm.toggle_selection(path.img_path))

        container.image_label = label

        if is_selected:
            label.selected = True
            label.add_red_boarder()

        vbox.addWidget(path_label)
        vbox.addWidget(label)

        self.grid_view_model.add_image_to_grid(container, row, col)

    def on_load_folder(self, parent=None):
        if parent is None:
            parent = self
        selected_folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if selected_folder_path:
            self.grid_view_model.load_main_folder(selected_folder_path)

    def show_batch(self):
        self.grid_view_model.load_batch()



