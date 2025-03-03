
from PyQt5.QtCore import Qt


class Box:
	def __init__(self, x_1 : float,y_1 : float,x_2 : float,y_2 : float, electric : bool , label : str , active : bool ) :
		self.x_1 = x_1
		self.y_1 = y_1
		self.x_2 = x_2
		self.y_2 = y_2
		self.electric = electric
		self.active = active
		self.label = label
		self.color = Qt.gray

	def deactivate(self):
		self.active = False
		self.color = Qt.gray

	def activate(self):
		self.active = True
		self.color = Qt.cyan

	def __str__(self):
		return f"[\n x_1 : {self.x_1},\n y_1 : {self.y_1},\n x_2 : {self.x_2}, \n y_2 : {self.y_2}\n electric : {self.electric}, \n active : {self.active}, \n label : {self.label} \n color : {self.color}\n ]"
