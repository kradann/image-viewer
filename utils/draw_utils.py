from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush


def get_image_coordinates(widget, pos):
    # Get the position of the click relative to the QLabel
    relative_pos = pos - widget.image.pos()

    # Get the size of the QLabel and the Pixmap
    label_width = widget.image.width()
    label_height = widget.image.height()
    pixmap_width = widget.pixmap.width()
    pixmap_height = widget.pixmap.height()

    # Calculate the position of the Pixmap within the QLabel
    if widget.image.hasScaledContents():
        x_ratio = pixmap_width / label_width
        y_ratio = pixmap_height / label_height
        return relative_pos.x() * x_ratio, relative_pos.y() * y_ratio
    else:
        widget.x_offset = (label_width - pixmap_width) // 2
        widget.y_offset = (label_height - pixmap_height) // 2
        return relative_pos.x() - widget.x_offset, relative_pos.y() - widget.y_offset