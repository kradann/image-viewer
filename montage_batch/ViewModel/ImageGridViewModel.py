from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from Model.BatchLoaderModel import ImageLoaderThread, ImageBatchLoader


class ImageGridViewModel(QObject):
	button_state_changed = pyqtSignal(bool)
	imageAdded = pyqtSignal(int,int, str, object,bool)
	imageReady = pyqtSignal(int,int, str, object,bool)
	batchLoaded = pyqtSignal(str)
	folderLoaded = pyqtSignal(list) #subfolders
	batchShouldBeShown = pyqtSignal()
	infoMessage = pyqtSignal(str)

	def __init__(self, mainmodel):
		super(ImageGridViewModel, self).__init__()
		self.main_model = mainmodel
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self._check_button_state)
		self.timer.start(500)
		self.thread = None

	def _check_button_state(self):
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



	def load_folder(self):
		mode, subfolders = self.main_model.load_folder()

		if mode == "single_region":
			self.loader = ImageBatchLoader(self.main_model.folder_path, batch_size=1000)
			self.batchShouldBeShown.emit()
			self.infoMessage.emit("Folder loaded!")
		elif mode == "multi_region":
			self.folderLoaded.emit(subfolders)