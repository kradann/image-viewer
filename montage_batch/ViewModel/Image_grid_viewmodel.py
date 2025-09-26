from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from View.Grid_widget import ImageGridWidget


class ImageGridViewModel():
    button_state_changed = pyqtSignal(bool)

    def __init__(self):
        super(ImageGridViewModel, self).__init__()
        self.model = ImageGridWidget(self)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._check_button_state)
        self.timer.start(500)

    def _check_button_state(self):
        can_enable = bool(self.model.main_folder and self.model.selected_images)
        self.button_state_changed.emit(can_enable)