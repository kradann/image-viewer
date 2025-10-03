from PyQt5 import QtWidgets
from View.Image_montage import ImageMontageApp



if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	window = ImageMontageApp()
	window.show()
	app.exec_()