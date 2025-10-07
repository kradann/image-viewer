import json
import os
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
from Model.FolderListModel import FolderListModel


class FolderListViewModel(QObject):
    statusChanged = pyqtSignal()
    statusesLoaded = pyqtSignal()
    infoMessage = pyqtSignal(str)
    updateInfo = pyqtSignal()

    def __init__(self, mainmodel):
        super().__init__()
        self.mainModel = mainmodel

    def set_status(self, folder_name, status):
        self.mainModel.set_status(folder_name, status)
        self.statusChanged.emit(folder_name, status)

    def load_statuses(self, main_folder):
        try:
            statuses = self.mainModel.load(Path(main_folder))
            self.statusesLoaded.emit(statuses)
            self.infoMessage.emit("Status Loaded")
        except Exception as e:
            self.infoMessage.emit(f"Failed to load: {e}")

    def save_statuses(self, main_folder):
        try:
            save_path = self.model.save(Path(main_folder))
            self.infoMessage.emit(f"Statuses saved to {save_path}")
        except Exception as e:
            self.infoMessage.emit(f"Failed to save: {e}")

    def folder_clicked(self, folder_name):
        self.mainModel.load_folder(folder_name.text().split()[0])
        self.updateInfo.emit()
