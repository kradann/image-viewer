import os
from utils.box import Box
from typing import List

class BoxManager:
	def __init__(self, widget):
		self.widget = widget
		self.coord_list : List[Box] = []
		self.idx = 0

	def previous(self):
		Box.deactivate(self.coord_list[self.idx])
		self.idx -= 1
		self.idx %= len(self.coord_list)
		Box.activate(self.coord_list[self.idx])


	def next(self):
		self.coord_list[self.idx].deactivate()
		self.idx += 1
		self.idx %= len(self.coord_list)
		self.coord_list[self.idx].activate()

	def __str__(self):
		if self.coord_list:
			return "List empty"
		box_writer = [str(box) for box in self.coord_list]
		return "Dobozok:".join(box_writer)
