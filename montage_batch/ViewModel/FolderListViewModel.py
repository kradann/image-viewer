from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal



class FolderListViewModel(QObject):
    status_changed = pyqtSignal()
    statuses_loaded = pyqtSignal()

    info_message = pyqtSignal(str) #notifies main view to change info label
    update_batch_info = pyqtSignal() #updates batch info after loading folder
    highlight_folder_name = pyqtSignal(str)

    def __init__(self, main_model, grid_view_model):
        super().__init__()
        self.main_model = main_model
        self.grid_viewmodel = grid_view_model

        self.main_model.load_folder_with_click.connect(self.folder_clicked)
        self.main_model.highlight_current_folder_name.connect(self.on_highlight_by_name)

    def set_status(self, folder_name, status):
        self.main_model.set_status(folder_name, status)
        self.status_changed.emit(folder_name, status)

    #TODO: Not MVVM safe
    def load_statuses(self, main_folder):
        try:
            statuses = self.main_model.load(Path(main_folder))
            self.statuses_loaded.emit(statuses)
            self.info_message.emit("Status Loaded")
        except Exception as e:
            self.info_message.emit(f"Failed to load: {e}")

    # TODO: Not MVVM safe
    def save_statuses(self, main_folder):
        try:
            save_path = self.model.save(Path(main_folder))
            self.info_message.emit(f"Statuses saved to {save_path}")
        except Exception as e:
            self.info_message.emit(f"Failed to save: {e}")

    def folder_clicked(self, folder_name):
        if not isinstance(folder_name, str):
            folder_name = folder_name.text().split()[0]
            if folder_name != self.main_model.get_current_label:
                self.main_model.load_folder_by_folder_name(folder_name)
                #self.highlight_current_folder_name.emit(str(self.main_model.get_folder_path().name))
                self.update_batch_info.emit()

    def on_highlight_by_name(self, name):
        self.highlight_folder_name.emit(name)

