import json
from pathlib import Path

class FolderListModel:
	def __init__(self):
		self.status_dict = {}  # {folder_name: status}

	def set_status(self, folder_name, status):
		self.status_dict[folder_name] = status

	def get_status(self, folder_name):
		return self.status_dict.get(folder_name)

	def save(self, main_folder: Path):
		save_path = Path(main_folder) / f"{main_folder.name}_status_action.json"
		with open(save_path, "w") as f:
			json.dump(self.status_dict, f, indent=4)
		return save_path

	def load(self, main_folder: Path):
		load_path = Path(main_folder) / f"{main_folder.name}_status_action.json"
		with open(load_path, "r") as f:
			self.status_dict = json.load(f)
		return self.status_dict


