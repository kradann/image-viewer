import json
import os
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
from Model.FolderListModel import FolderListModel


class FolderListViewModel(QObject):
    status_changed = pyqtSignal()
    statuses_loaded = pyqtSignal()
    info_message = pyqtSignal(str)
    update_info = pyqtSignal()
    highlight_current_folder_name = pyqtSignal(str)

    def __init__(self, mainmodel, gridviewmodel):
        super().__init__()
        self.main_model = mainmodel
        self.grid_viewmodel = gridviewmodel

        self.main_model.load_folder_with_click.connect(self.folder_clicked)

    def set_status(self, folder_name, status):
        self.main_model.set_status(folder_name, status)
        self.status_changed.emit(folder_name, status)

    def load_statuses(self, main_folder):
        try:
            statuses = self.main_model.load(Path(main_folder))
            self.statuses_loaded.emit(statuses)
            self.info_message.emit("Status Loaded")
        except Exception as e:
            self.info_message.emit(f"Failed to load: {e}")

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
                self.update_info.emit()
