import json, os

from PyQt5 import QtWidgets, QtCore, QtGui
from ViewModel.FolderListViewModel import FolderListViewModel

def _apply_status_color(item, status):
	transparency = 125
	if status == "not_done":
		item.setBackground(QtGui.QColor(255, 0, 0, transparency))
	elif status == "in_progress":
		item.setBackground(QtGui.QColor(255, 255, 0, transparency))
	elif status == "done":
		item.setBackground(QtGui.QColor(0, 255, 0, transparency))
	else:
		item.setBackground(QtGui.QColor("#303436"))


class FolderListWidget(QtWidgets.QListWidget):
	def __init__(self, mainmodel, parent=None):
		super().__init__(parent)
		self.mainmodel = mainmodel
		self.highlight_color = QtGui.QColor(0, 120, 215, 180)
		self.current_item_name = None  # store name, not the QListWidgetItem

		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.show_context_menu)

		self.FolderListViewModel = FolderListViewModel(self.mainmodel)

		self.FolderListViewModel.statusChanged.connect(self.on_status_changed)
		self.FolderListViewModel.statusesLoaded.connect(self.apply_loaded_statuses)
		self.setMinimumWidth(400)

	def on_status_changed(self, folder_name, status):
		item = self._find_item_by_name(folder_name)
		if item:
			_apply_status_color(item, status)

	def apply_loaded_statuses(self, statuses):
		for i in range(self.count()):
			item = self.item(i)
			name = item.text().split()[0]
			status = statuses.get(name)
			self._apply_status_color(item, status)

	def _find_item_by_name(self, name):
		for i in range(self.count()):
			it = self.item(i)
			if it.text().split()[0] == name:
				return it
		return None

	def show_context_menu(self, pos):
		item = self.itemAt(pos)
		if not item:
			return
		menu = QtWidgets.QMenu()
		for status in ["Not Done", "In Progress", "Done"]:
			action = menu.addAction(status)
		remove = menu.addAction("Remove Status")
		chosen = menu.exec_(self.mapToGlobal(pos))

		if chosen:
			name = item.text().split()[0]
			if chosen.text() == "Remove Status":
				self.vm.set_status(name, None)
			else:
				self.vm.set_status(name, chosen.text().lower().replace(" ", "_"))

	def update_folder_list(self, subfolders):
		self.clear()
		for folder in subfolders:
			self.addItem(folder)
