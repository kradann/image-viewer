from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

from Model.sign_types import SIGN_TYPES
from Model.BatchLoaderModel import ImageBatchLoader, ImageLoaderThread
from Model.FolderListModel import FolderListModel
from Model.ImageThreadLoaderModel import ImageLoaderThread
from Model.ClickableModel import Clickable



class MainModel(QtWidgets.QMainWindow):
	def __init__(self, loader=None):
		super(MainModel, self).__init__()
		self.loader = loader
		self.folder_path = None
		self.main_folder = None  # Folder that stores the subfolders / Folder that stored the folders of the regions
		self.first_check = True
		self.is_all_region = False  # user load multiple regions
		self.image_paths = None  # used when multiple regions
		self.regions = None  # list regions in folder
		self.base_folder = None  # Only use for JSON
		self.thread = None
		self.isAllSelected = False
		self.subfolders = None  # list of subfolders
		self.labels = list()
		self.selected_images = set()
		self.dropped_selected = set()
		self.json = None
		self.json_data = None
		self.is_JSON_active = False
		self.num_of_col = 6
		self.batch_size = 1000



	'''def load_folder(self):
		#self.folderListView.clear()
		#self.clear_images()
		self.main_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
		if self.main_folder:
			self.is_JSON_active = False
			self.subfolders = [f.name for f in Path(self.main_folder).iterdir() if f.is_dir()]
			self.subfolders.sort()

			if any(sub in SIGN_TYPES for sub in self.subfolders):
				self.is_all_region = False
				self.folder_path = Path(self.main_folder) / self.subfolders[0]
				self.load_subfolders(self.main_folder)
				self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
				self.show_batch()
				self.change_info_label("Folder loaded!")
			else:
				sign_types_in_all_region = self.collect_sign_types()
				sign_types_in_all_region.sort()
				#pprint.pprint(sign_types_in_all_region)
				self.folderListView.clear()
				self.subfolders = sign_types_in_all_region
				for sign_type in self.subfolders:
					self.folderListView.addItem(sign_type)
				self.is_all_region = True'''

	def load_folder(self, path : str):
		if not path:
			return None, []
		self.main_folder = Path(path)
		self.subfolders = [f.name for f in self.main_folder.iterdir() if f.is_dir()]
		self.subfolders.sort()

		if any(sub in SIGN_TYPES for sub in self.subfolders):
			self.is_all_region = False
			self.folder_path = self.main_folder / self.subfolders[0]
			return "single_region", self.subfolders
		else:
			sign_types_in_all_region = self.collect_sign_types()
			self.subfolders = sorted(sign_types_in_all_region)
			self.is_all_region = True
			return "multi_region", self.subfolders

	def collect_sign_types(self):
		regions = [d for d in Path(self.main_folder).iterdir() if d.is_dir()]
		all_sign_types = set()
		for region in regions:
			for sign_type in region.iterdir():
				if sign_type.is_dir():
					all_sign_types.add(sign_type)
		return all_sign_types



	def load_subfolders(self, path=None):
		self.folderListView.clear()
		if not self.is_JSON_active and not self.is_all_region:
			folder_infos = []
			wrong_subfolder_name = []

			for name in self.subfolders:
				if name in SIGN_TYPES:
					full_path = Path(path) / name
					if full_path.is_dir():
						num_images = len(list(Path(full_path).iterdir()))
						folder_infos.append((name, num_images))
				else:
						wrong_subfolder_name.append(name)

			if wrong_subfolder_name and self.first_check:
				self.first_check = False
				msg = "These are not valid subfolder names:\n" + "\n".join(wrong_subfolder_name)
				QMessageBox.information(self, "Subfolder name error", msg)

			folder_infos.sort()  # order list names to abc
			self.subfolders = []
			for name, count in folder_infos:
				self.subfolders.append(name)
				display_text = f"{name:<40} {count:>6}"  # left-align name, right-align number
				self.folderListView.addItem(display_text)

			# Set monospaced font for alignment
			font = QFont("Courier New", 10)
			self.folderListView.setFont(font)
		elif not self.is_JSON_active and self.is_all_region:
			print(15)
			for sign_type in self.subfolders:
				self.folderListView.addItem(sign_type)

	def get_current_batch(self):
		return self.loader.get_batch()

	def current_folder_name(self):
		return Path(self.loader.folder).name if self.loader else None

	def clear_images(self):
		for label in self.labels:
			label.deleteLater()
		self.labels = list()

	def is_selected(self, path):
		return path in self.selected_images

	def toggle_selection(self, path):
		if path in self.selected_images:
			self.selected_images.remove(path)
		else:
			self.selected_images.add(path)

	def get_position(self, idx):
		return idx // self.num_of_col, idx % self.num_of_col

	def get_batch(self):
		return self.loader.get_batch() if self.loader else []

	def batch_info(self):
		if not self.loader:
			return "No Batch"
		return f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}"

