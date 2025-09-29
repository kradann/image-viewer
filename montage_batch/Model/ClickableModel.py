
from pathlib import Path
from PyQt5.QtGui import QPixmap, QImage
from Model.ImageThreadLoaderModel import ImageLoaderThread  # assuming you keep it

class Clickable:
    def __init__(self, img_path):
        self.img_path = Path(img_path)

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
        name_idx = 2
        while True:
            new_path = self.img_path.with_stem(f"{self.img_path.stem}_{name_idx}")
            if not new_path.exists():
                break
            name_idx += 1

        # Save to disk
        cropped_0.save(str(self.img_path))
        cropped_1.save(str(new_path))

        # Regenerate thumbnail
        thumb_path = ImageLoaderThread.get_thumb_path(str(self.img_path))
        ImageLoaderThread.generate_thumbnail(str(self.img_path), thumb_path)

        return str(self.img_path), str(new_path), str(thumb_path)
