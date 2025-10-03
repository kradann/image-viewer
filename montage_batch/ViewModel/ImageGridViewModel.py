import pprint

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from Model.BatchLoaderModel import ImageBatchLoader
from Model.ImageThreadLoaderModel import ImageLoaderThread
from Model.ClickableModel import Clickable


def clear_images(labels):
    for label in labels:
        label.deleteLater()


class ImageGridViewModel(QObject):
    button_state_changed = pyqtSignal(bool)
    imageAdded = pyqtSignal(int,int, str, object,bool)
    imageReady = pyqtSignal(int,int, str, object,bool)
    batchLoaded = pyqtSignal(str)
    folderLoaded = pyqtSignal(dict) #subfolders
    batchShouldBeShown = pyqtSignal()
    infoMessage = pyqtSignal(str)
    AddImage = pyqtSignal(object, int,int)
    loadSubfoldersList = pyqtSignal(dict)

    def __init__(self, mainmodel, gridviewmodel):
        super(ImageGridViewModel, self).__init__()
        self.main_model = mainmodel
        self.gridviewmodel = gridviewmodel
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._check_button_state)
        self.timer.start(500)
        self.thread = None
        self.labels = list()

        self.main_model.LoadFolder.connect(self.load_images)

    def _check_button_state(self):
        if not self.main_model:
            return
        can_enable = bool(self.main_model.main_folder and self.main_model.selected_images)
        self.button_state_changed.emit(can_enable)

    def add_image(self, idx, pixmap, path):
        row, col = self.main_model.get_position(idx)
        selected = self.main_model.is_selected(path)
        self.imageAdded.emit(row, col, path, pixmap, selected)

    def toggle_selection(self, path):
        self.main_model.toggle_selection(path)

    def load_batch(self):
        batch = self.main_model.get_current_batch()
        self.thread = ImageLoaderThread(batch)
        self.thread.image_loaded.connect(self.on_image_loaded)
        self.thread.start()

        folder_name = self.main_model.current_folder_name()
        if folder_name:
            self.batchLoaded.emit(folder_name)

    def on_image_loaded(self, idx, pixmap, path):
        # Compute row/col and selection state here
        row, col = divmod(idx, 6)  # or self.model.num_of_col
        is_selected = False  # ask model if selected
        self.imageReady.emit(row, col, path, pixmap, is_selected)



    def load_main_folder(self, path):
        print(path)
        mode, subfolders = self.main_model.load_main_folder(path)
        print(2)
        self.load_images(mode, subfolders)

    def load_images(self, mode, subfolders):
        print("3")
        if mode == "single_region":
            self.main_model.set_loader(ImageBatchLoader(self.main_model.folder_path, batch_size=1000))
            self.batchShouldBeShown.emit()
            self.infoMessage.emit("Folder loaded!")
        elif mode == "multi_region":
            self.folderLoaded.emit(subfolders)
        self.loadSubfoldersList.emit(subfolders)

    def clear_images(self):
        for label in self.labels:
            label.deleteLater()
        self.labels = list()

    def add_image_to_grid(self, click, row, col):
        self.AddImage.emit(click, row, col)
        self.labels.append(click)

    @staticmethod
    def cleanup_thumbs():
        print(12)
        ImageLoaderThread.cleanup_thumbs()


