import logging
from pathlib import Path, PosixPath

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QDialog, QApplication


from View.FolderSelectionDialog import FolderSelectionDialog
from Model.BatchLoaderModel import ImageBatchLoader
from Model.ImageThreadLoaderModel import ImageLoaderThread
from Model.FolderScanThread import scan_and_count_labels



def clear_images(labels):
    for label in labels:
        label.deleteLater()


class ImageGridViewModel(QObject):
    button_state_changed = pyqtSignal(bool) # updates move selected button visually

    #Signals to main view
    not_enough_space = pyqtSignal(int)  # notifies main view to show not enough space warning
    show_folder_selection_dialog = pyqtSignal(str)  # notifies main view to show folder selection dialog
    add_image_to_grid_action = pyqtSignal(object, int, int)  # notifies main view to add widget to image_layout
    show_not_found_images = pyqtSignal(list) #notifies main view to show list of not found images name when importing directory tree
    show_last_move_window = pyqtSignal(dict, PosixPath)

    #Signals to grid view
    # notifies grid view to add image to grid (row, column, image path, pixmap of image, is image selected)
    image_ready = pyqtSignal(int,int, str, object,bool)
    show_base_folder_dialog = pyqtSignal()  # notifies grid view to show base folder dialog
    show_batch = pyqtSignal() #notifies grid view to display current batch

    #Signals to folder list view
    load_subfolders_list = pyqtSignal(dict) #notifies folder list view to load the folder list

    # Signals to change labels
    info_message = pyqtSignal(str)  # updates info label
    change_current_folder = pyqtSignal(str)  # updates current folder label

    # notifies main view to display the wrong folder names dialog (currently not using this)
    show_wrong_folder_names_window = pyqtSignal(list)

    load_finished_signal = pyqtSignal()


    def __init__(self, main_model):
        super(ImageGridViewModel, self).__init__()
        self.main_model = main_model
        self.thread = None
        self.labels = list()
        self.is_all_selected = False
        self.is_all_unselected = False
        self._load_generation = 0
        self._load_finished_emitted = False

        self.pending_widgets = []
        self.process_timer = QtCore.QTimer()
        self.process_timer.timeout.connect(self.process_pending_widgets)

        #Timer for checking button state frequently
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._check_button_state)
        self.timer.start(500)

        self.main_model.load_folder.connect(self.load_images)
        self.main_model.load_selected_images.connect(self.load_selected_images)
        self.main_model.clear_images.connect(self.clear_images)
        self.main_model.update_folder_list.connect(self.update_folder_list)
        self.main_model.change_info_label.connect(self.update_info_label)
        self.main_model.show_wrong_folder_names.connect(self.show_wrong_folder_names)
        self.main_model.set_base_folder_signal.connect(self.show_dialog_for_base_folder)


    def spinbox_value_changed(self, value, scroll_area_width, thumb_width):
        if (scroll_area_width - (value+2)*value) // thumb_width >= value: # space between thumbs
            self.main_model.set_num_of_col(value)
            self.load_batch()
        else:
            self.not_enough_space.emit(value)

    def _check_button_state(self):
        if not self.main_model:
            return
        can_enable = bool((self.main_model.main_folder or self.main_model.get_base_folder) and self.main_model.selected_images)
        self.button_state_changed.emit(can_enable)


    def toggle_selection(self, path):
        self.main_model.toggle_selection(path)

    def load_batch(self):
        try:
            self.clear_images()

            if hasattr(self, 'thread') and self.thread is not None:
                self.thread.stop()
                self.thread.wait()  # Wait for thread to finish
                self.thread.deleteLater()  # Clean up thread
                self.thread = None

            self._load_generation += 1
            self._load_finished_emitted = False
            generation = self._load_generation

            batch = self.main_model.get_current_batch
            self.thread = ImageLoaderThread(batch)
            self.thread.image_loaded.connect(lambda idx, data, path: self._on_single_image_loaded(idx,data, path, generation))
            self.thread.load_finished.connect(lambda : self.on_load_finished(generation))

            self.thread.start()
        except Exception as e:
            logging.error(e)

    def _on_single_image_loaded(self, idx, data, path, generation):
        if generation != self._load_generation:
            return
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        row, col = divmod(idx, self.main_model.get_num_of_columns)  # or self.model.num_of_col
        is_selected = self.main_model.is_selected(path)  # ask model if selected
        self.pending_widgets.append((row, col, path, pixmap, is_selected))

        if not self.process_timer.isActive():
            self.process_timer.start(5)
        #self.on_image_loaded(batch_data)

    def process_pending_widgets(self):
        if not self.pending_widgets:
            self.process_timer.stop()
            # Notify that all widgets have been processed (only once)
            if not self._load_finished_emitted:
                self._load_finished_emitted = True
                QtCore.QTimer.singleShot(0, self.load_finished_signal)
            return

        batch_size = 5
        for _ in range(min(batch_size, len(self.pending_widgets))):
            if not self.pending_widgets:
                break

            row, col, path, pixmap, is_selected = self.pending_widgets.pop(0)
            self.image_ready.emit(row,col,path,pixmap,is_selected)

        if self.pending_widgets:
            QApplication.processEvents()
    '''
    def on_image_loaded(self, batch_data):
        # Compute row/col and selection state here
        for idx, data, path in batch_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            row, col = divmod(idx, self.main_model.get_num_of_columns)  # or self.model.num_of_col
            is_selected = self.main_model.is_selected(path)  # ask model if selected
            self.image_ready.emit(row, col, path, pixmap, is_selected)'''

    def on_load_finished(self, generation):
        # Thread finished loading, but don't signal yet - wait for widget processing
        pass

    def load_finished(self):
        self.load_finished_signal.emit()

    def load_json(self, json_data):
        self.main_model.load_json(json_data)

    def load_main_folder(self, path):
        self.main_model.load_main_folder(path)



    def update_info_label(self, text):
        self.info_message.emit(text)

    def update_folder_list(self, counts):
        if self.main_model.get_is_json: #TODO: Rethink
            self.main_model.collect_labels_from_json()
        else:
            if not counts:
                _ , counts = scan_and_count_labels(self.main_model.get_main_folder, self.get_current_labels())
            self.main_model.set_subfolders(counts)
        self.load_subfolders_list.emit(self.main_model.get_subfolders)

    def on_load_folder_by_name(self, folder_name):
        self.main_model.load_folder_by_folder_name(folder_name)

    def load_images(self, subfolders, batch_idx, is_json):
        self.main_model.clear_selected_images()


        self.main_model.set_loader(ImageBatchLoader(self.main_model.current_label_folder_paths, batch_size=500, start_batch_idx=batch_idx, is_json=is_json))
        self.load_batch()
        self.info_message.emit("Folder loaded!")
        self.change_current_folder.emit(str(self.main_model.get_current_label))
        self.load_subfolders_list.emit(subfolders)

    def clear_images(self):
        self.pending_widgets.clear()
        if self.process_timer.isActive():
            self.process_timer.stop()

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
        self.show_batch.emit()

    def on_next_batch(self):
        self.main_model.load_next_batch()
        self.show_batch.emit()

    def on_move_selected(self):
        preferred_label = self.main_model.get_current_label if self.main_model.get_is_json else None
        self.show_folder_selection_dialog.emit(preferred_label)


    def move_selected(self, selected_folder):
        self.main_model.move_selected(selected_folder)

    def on_select_all(self):
        if self.main_model.is_unselect_all_active():
            self.main_model.restore_selection_for_unselect_all()

        if not self.main_model.is_select_all_active():
            # FIRST CLICK: save current selection, then select all
            self.main_model.save_selection_for_select_all()
            self.main_model.selected_images.clear()

            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = True
                    self.main_model.add_image_to_selected(label.img_path)
                    label.add_red_boarder()
        else:
            # SECOND CLICK: restore saved selection
            self.main_model.restore_selection_for_select_all()

            # update UI according to restored selection
            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = self.main_model.is_selected(label.img_path)
                    label.add_red_boarder()


    def on_un_select_all(self):
        if self.main_model.is_select_all_active():
            self.main_model.restore_selection_for_select_all()

        if not self.main_model.is_unselect_all_active():
            # first click: save current selection, then unselect all
            self.main_model.save_selection_for_unselect_all()
            self.main_model.clear_selected_images()

            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = False
                    label.add_red_boarder()
        else:
            # second click: restore saved selection
            self.main_model.restore_selection_for_unselect_all()

            # update UI according to restored selection
            for container in self.labels:
                if hasattr(container, "image_label"):
                    label = container.image_label
                    label.selected = self.main_model.is_selected(label.img_path)
                    label.add_red_boarder()

    def on_show_only_selected(self):
        self.main_model.show_only_selected()

    def load_selected_images(self, dropped_images):
        if hasattr(self, 'thread') and self.thread is not None:
            self.thread.stop()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None

        self.thread = ImageLoaderThread(sorted(dropped_images))
        self.thread.image_loaded.connect(lambda idx, data, path: self._on_single_image_loaded(idx,data, path, self._load_generation))
        self.thread.start()

    def on_check_for_update(self):
        self.main_model.check_for_update()

    def show_wrong_folder_names(self, wrong_folder_names):
        self.show_wrong_folder_names_window.emit(wrong_folder_names)

    def show_dialog_for_base_folder(self):
        self.show_base_folder_dialog.emit()

    def set_base_folder(self, base_folder_path):
        self.main_model.set_base_folder(base_folder_path)

    def get_current_labels(self):
        return self.main_model.get_current_label_list

    def on_get_loader(self):
        return self.main_model.get_loader

    def on_get_batch_size(self):
        return self.main_model.get_batch_size

    def load_eu_sign_types(self):
        self.main_model.load_labels_from_json(str(Path(__file__).parent.parent / 'resources/sign_types/EU_sign_types.json'))

    def load_us_sign_types(self):
        self.main_model.load_labels_from_json(str(Path(__file__).parent.parent / 'resources/sign_types/US_sign_types.json'))

    def load_labels_from_json(self, path):
        self.main_model.load_labels_from_json(path)

    def create_log_folder(self):
        self.main_model.create_log_folder()

    def create_log_file(self):
        self.main_model.create_log_file()

    def get_log_file_path(self):
        return self.main_model.get_log_file_path

    def load_dir_tree(self, dir_tree_path, base_folder):
        self.main_model.load_dir_tree(dir_tree_path)

        if self.main_model.dir_tree_data:
            not_found_images = self.main_model.move_file_dir_tree(Path(base_folder))
            if not_found_images:
                self.show_not_found_images.emit(not_found_images)

    def export_dir_tree(self, folder_path):
        self.main_model.make_directory_tree(folder_path)

    def get_last_move(self):
        last_move = self.main_model.last_move
        main_folder = self.main_model.main_folder
        if last_move and main_folder:
            self.show_last_move_window.emit(last_move, main_folder)

    def undo_last_move(self):
        self.main_model.undo_last_move()
        _, counts = scan_and_count_labels(self.main_model.get_main_folder, self.get_current_labels())
        self.main_model.set_subfolders(counts)
        self.reload_current_label()


    def reload_current_label(self):
        self.main_model.load_folder_by_folder_name(self.main_model.get_current_label, self.main_model.get_loader.current_batch_idx)
        self.show_batch.emit()
    @staticmethod
    def cleanup_thumbs():
        ImageLoaderThread.cleanup_thumbs()



