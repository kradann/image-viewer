from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from Model.ImageThreadLoaderModel import *


class ClickableViewModel(QObject):
    def __init__(self,model, img_path, main_model=None, parent=None):
        super().__init__(parent)
        self.model = model
        self.img_path = img_path
        self.selected = False
        self.preview_pos = None
        self.main_model = main_model


    def cut_image(self, pixmap: QPixmap, mode: str, pos):
        """Cut pixmap at position pos (QPoint) into two images, save them to disk."""
        x, y = pos.x(), pos.y()
        width, height = pixmap.width(), pixmap.height()

        if mode == 'vertical':
            rect_0 = (0, 0, x, height)
            rect_1 = (x, 0, width - x, height)
        else:  # horizontal
            rect_0 = (0, 0, width, y)
            rect_1 = (0, y, width, height - y)

        cropped_0 = pixmap.copy(*rect_0)
        cropped_1 = pixmap.copy(*rect_1)

        # Generate new path for second piece
        name_idx = 1
        while True:
            new_path = self.img_path.with_stem(f"{self.img_path.stem}_{name_idx}")
            if not new_path.exists():
                break
            name_idx += 1

        #TODO: Save and other I/O should be in Model
        # Save to disk
        cropped_0.save(str(self.img_path))
        cropped_1.save(str(new_path))

        # Regenerate thumbnail
        thumb_path = ImageLoaderThread.get_thumb_path(str(self.img_path))
        ImageLoaderThread.generate_thumbnail(str(self.img_path), str(thumb_path))



