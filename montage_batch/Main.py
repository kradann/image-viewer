from PyQt5 import QtWidgets
from Model.MainModel import MainModel

from ViewModel.ImageGridViewModel import ImageGridViewModel
from ViewModel.FolderListViewModel import FolderListViewModel

from View.ImageMontage import ImageMontageApp



if __name__ == "__main__":
	app = QtWidgets.QApplication([])

	main_model = MainModel()
	grid_view_model = ImageGridViewModel(main_model)
	folder_list_view_model = FolderListViewModel(main_model, grid_view_model)


	window = ImageMontageApp(main_model, grid_view_model, folder_list_view_model)
	window.show()

	app.exec_()