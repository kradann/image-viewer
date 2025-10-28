from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QDialog

from View.FolderSelectionDialog import FolderSelectionDialog
from Model.BatchLoaderModel import ImageBatchLoader
from Model.ImageThreadLoaderModel import ImageLoaderThread



def clear_images(labels):
    for label in labels:
        label.deleteLater()


class ImageGridViewModel(QObject):
    #TODO: Check which signal do i actually use :)
    button_state_changed = pyqtSignal(bool)
    image_added = pyqtSignal(int,int, str, object,bool)
    image_ready = pyqtSignal(int,int, str, object,bool)
    batch_loaded = pyqtSignal(str)
    folder_loaded = pyqtSignal(dict) #subfolders
    batch_should_be_shown = pyqtSignal()
    info_message = pyqtSignal(str)
    change_current_folder = pyqtSignal(str)
    add_image_to_grid_action = pyqtSignal(object, int,int)
    load_subfolders_list = pyqtSignal(dict)
    update_folder_list_signal = pyqtSignal(str,int)
    show_wrong_folder_names_window = pyqtSignal(list)
    not_enough_space = pyqtSignal(int)



    def __init__(self, mainmodel):
        super(ImageGridViewModel, self).__init__()
        self.main_model = mainmodel
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._check_button_state)
        self.timer.start(500)
        self.thread = None
        self.labels = list()
        self.isAllSelected = False
        self._load_generation = 0

        self.main_model.load_folder.connect(self.load_images)
        self.main_model.load_selected_images.connect(self.load_selected_images)
        self.main_model.clear_images.connect(self.clear_images)
        self.main_model.update_folder_list_label.connect(self.update_folder_list)
        self.main_model.change_info_label.connect(self.update_info_label)
        self.main_model.show_wrong_folder_names.connect(self.show_wrong_folder_names)

    def spinbox_value_changed(self, value, scroll_area_width, thumb_width):
        if (scroll_area_width - (value+2)*6) // thumb_width >= value: # space between thumbs
            self.main_model.set_num_of_col(value)
            self.load_batch()
        else:
            self.not_enough_space.emit(value)

    def _check_button_state(self):
        if not self.main_model:
            return
        can_enable = bool(self.main_model.main_folder and self.main_model.selected_images)
        self.button_state_changed.emit(can_enable)

    def add_image(self, idx, pixmap, path):
        row, col = self.main_model.get_position(idx)
        selected = self.main_model.is_selected(path)
        self.image_added.emit(row, col, path, pixmap, selected)

    def toggle_selection(self, path):
        self.main_model.toggle_selection(path)

    def load_batch(self):
        self.clear_images()

        if hasattr(self, 'thread') and self.thread is not None:
            self.thread.stop()
            self.thread.wait()

        self._load_generation += 1
        generation = self._load_generation

        batch = self.main_model.get_current_batch
        self.thread = ImageLoaderThread(batch)
        self.thread.image_loaded.connect(lambda idx, pixmap, path: self._on_image_loaded(idx,pixmap, path, generation))

        self.thread.start()

    def _on_image_loaded(self, idx, pixmap, path, generation):
        if generation != self._load_generation:
            return

        self.on_image_loaded(idx,pixmap,path)

    def on_image_loaded(self, idx, pixmap, path):
        # Compute row/col and selection state here
        row, col = divmod(idx, self.main_model.get_num_of_columns)  # or self.model.num_of_col
        is_selected = self.main_model.is_selected(path)  # ask model if selected
        self.image_ready.emit(row, col, path, pixmap, is_selected)


    def load_main_folder(self, path):
        subfolders = self.main_model.load_main_folder(path)
        self.load_images(subfolders,0)


    def update_info_label(self, text):
        self.info_message.emit(text)

    def update_folder_list(self):
        self.main_model.collect_subfolders()
        self.load_subfolders_list.emit(self.main_model.get_subfolders)


    def load_images(self, subfolders, batch_idx):
        self.main_model.clear_selected_images()

        self.main_model.set_loader(ImageBatchLoader(self.main_model.current_label_folder_paths, batch_size=1000, start_batch_idx=batch_idx))
        self.load_batch()
        self.info_message.emit("Folder loaded!")
        self.change_current_folder.emit(str(self.main_model.get_current_label))
        self.load_subfolders_list.emit(subfolders)

    def clear_images(self):
        for label in self.labels:
            label.deleteLater()
        self.labels = list()

    def add_image_to_grid(self, click, row, col):
        self.add_image_to_grid_action.emit(click, row, col)
        self.labels.append(click)

    def on_prev_folder(self):
        self.main_model.load_prev_folder()

    def on_next_folder(self):
        self.main_model.load_next_folder()

    def on_prev_batch(self):
        self.main_model.load_prev_batch()
        self.batch_should_be_shown.emit()

    def on_next_batch(self):
        self.main_model.load_next_batch()
        self.batch_should_be_shown.emit()

    def on_move_selected(self):
        dialog = FolderSelectionDialog()
        if dialog.exec_() != QDialog.Accepted or not dialog.selected_folder:
            return
        self.main_model.move_selected(dialog.selected_folder)

    def on_unselect_select_all(self):

        if not self.isAllSelected:
            self.isAllSelected = True
            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = True
                    self.main_model.add_image_to_selected(label.img_path)
                    label.add_red_boarder()

        else:
            self.isAllSelected = False
            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = False
                    self.main_model.discard_image_from_selected(label.img_path)
                    label.add_red_boarder()

        #self.load_batch()

    def on_show_only_selected(self):
        self.main_model.show_only_selected()

    def load_selected_images(self, dropped_images):
        self.thread = ImageLoaderThread(sorted(dropped_images))
        self.thread.image_loaded.connect(self.on_image_loaded)
        self.thread.start()

    def on_check_for_update(self):
        self.main_model.check_for_update()

    def show_wrong_folder_names(self, wrong_folder_names):
        self.show_wrong_folder_names_window.emit(wrong_folder_names)


    @staticmethod
    def cleanup_thumbs():
        ImageLoaderThread.cleanup_thumbs()



