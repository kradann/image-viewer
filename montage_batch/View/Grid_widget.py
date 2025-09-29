from PyQt5 import Qt, QtCore, QtWidgets

from ViewModel.ClickableViewModel import ClickableLabel
from ViewModel.ImageGridViewModel import  ImageGridViewModel


class ImageGridWidget(QtWidgets.QWidget):
	def __init__(self,parent=None, mainmodel=None):
		super().__init__()
		self.setMouseTracking(True)
		self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
		self.origin = QtCore.QPoint()
		self.drag_selecting = False
		self.parent_app = parent
		self.clicked_label = None
		self.mainModel = mainmodel
		self.viewmodel = ImageGridViewModel(self.mainModel)
		self.viewmodel.imageReady.connect(self.add_image_to_layout)
		self.viewmodel.batchLoaded.connect(self.update_folder_label)
		self.viewmodel.batchShouldBeShown.connect(self.show_batch)
		#self.viewmodel.infoMessage.connect(self.change_info_label)

	def mousePressEvent(self, event):
		# print(1)
		if event.button() == Qt.LeftButton:
			self.origin = event.pos()
			self.clicked_label = self.label_at(event.pos())  # select which image was clicked
			self.drag_selecting = True
			self.rubber_band.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
			self.rubber_band.show()
		# elif event.button() == QtCore.Qt.RightButton:
		# self.show_context_menu(event.pos())

	def mouseMoveEvent(self, event):
		if self.drag_selecting:
			# print(4)
			rect = QtCore.QRect(self.origin, event.pos()).normalized()
			self.rubber_band.setGeometry(rect)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton and self.drag_selecting:
			self.rubber_band.hide()
			selection_rect = self.rubber_band.geometry()
			drag_distance = (event.pos() - self.origin).manhattanLength()

			if drag_distance < 40 and self.clicked_label:  # no drag, just clicking
				self.clicked_label.selected = not self.clicked_label.selected
				self.clicked_label.add_red_boarder()
				if self.clicked_label.selected:
					self.parent_app.selected_images.add(self.clicked_label.img_path)
				else:
					self.parent_app.selected_images.discard(self.clicked_label.img_path)
			else:
				# rubber band kijelölés
				for label in self.parent_app.labels:
					label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
					label_rect = QtCore.QRect(label_pos, label.size())
					if selection_rect.intersects(label_rect):
						label.selected = not label.selected
						label.add_red_boarder()
						if label.selected:
							self.parent_app.selected_images.add(label.img_path)
						else:
							self.parent_app.selected_images.discard(label.img_path)

			self.drag_selecting = False
			self.clicked_label = None

	def label_at(self, pos):
		for label in self.parent_app.labels:
			label_pos = label.mapTo(self, QtCore.QPoint(0, 0))
			label_rect = QtCore.QRect(label_pos, label.size())
			if label_rect.contains(pos):
				return label
		return None

	def on_image_added(self, row, col, path, pixmap, is_selected):
		label = ClickableLabel(path)
		label.setPixmap(pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
		label.clicked.connect(lambda: self.vm.toggle_selection(path))

		if is_selected:
			label.selected = True
			label.add_red_boarder()

		self.image_layout.addWidget(label, row, col)
		self.labels.append(label)

	def update_folder_label(self, folder_name):
		self.current_folder_label.setText(f"Current folder: {folder_name}")

	def add_image_to_layout(self, row, col, path, pixmap, is_selected):
		label = ClickableLabel(path)
		label.setPixmap(pixmap.scaled(*self.thumbnail_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
		label.clicked.connect(lambda: self.vm.toggle_selection(path))

		if is_selected:
			label.selected = True
			label.add_red_boarder()

		self.image_layout.addWidget(label, row, col)
		self.labels.append(label)

	def on_load_folder(self):
		folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
		if folder:
			self.viewmodel.load_folder(folder)

	def show_batch(self):
		self.clear_images()
		self.viewmodel.load_batch()

