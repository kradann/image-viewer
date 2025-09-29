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

	def __init__(self, mainmodel):
		super().__init__()
		self.mainModel = mainmodel


	def set_status(self, folder_name, status):
		self.model.set_status(folder_name, status)
		self.statusChanged.emit(folder_name, status)

	def load_statuses(self, main_folder):
		try:
			statuses = self.model.load(Path(main_folder))
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