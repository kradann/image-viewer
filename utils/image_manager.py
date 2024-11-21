import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush

from qt_annotation_tool import AnnotationTool
from utils.file_manager import FileManager
from utils.utils import valid_coordinates, out_of_bounds


class ImageManager(object):
    def __init__(self, widget: AnnotationTool, file_manager: FileManager):
        self.widget = widget
        self.file_manager = file_manager
        self.image = QtWidgets.QLabel()
        self.pixmap = QtGui.QPixmap(320, 320)
        self.pixmap.fill(Qt.white)  # Fill with white color
        self.image.setPixmap(self.pixmap)

        # draw rectangle
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        self.x_back_scale = None
        self.y_back_scale = None

        self.valid = True


    def load_image(self, file_path):
        self.pixmap = QtGui.QPixmap(file_path)
        ori_width, ori_height = self.pixmap.width(), self.pixmap.height()

        if self.pixmap.isNull():
            # the file is not a valid image, remove it from the list
            self.pixmap = QtGui.QPixmap(320, 320)
            self.pixmap.fill(Qt.white)  # Fill with white color
            self.image.setPixmap(self.pixmap)
            print("file is removed from the list because it is not valid ({})".format(file_path))
            self.file_manager.remove_file_from_list(file_path)
            self.valid = False
        else:
            self.pixmap = self.pixmap.scaled(self.image.size(), QtCore.Qt.KeepAspectRatio)
            current_width, current_height = self.pixmap.width(), self.pixmap.height()
            self.x_back_scale = ori_width / current_width
            self.y_back_scale = ori_height / current_height
            self.image.setPixmap(self.pixmap)
            self.valid = True


# draw rectangle
def mouse_press_event(widget, event):
    if event.button() == Qt.LeftButton:
        widget.start_x, widget.start_y = get_image_coordinates(widget, event.pos())
        widget.end_x = widget.start_x
        widget.end_y = widget.start_y

        widget.start_dx = widget.start_x - event.x()
        widget.start_dy = widget.start_y - event.y()
        widget.end_dx = 0
        widget.end_dy = 0

        widget.update()
        widget.update_image()
    if event.button() == Qt.RightButton:
        widget.crossPos = get_image_coordinates(widget, event.pos())  # Store the position of the right-click
        widget.right_button_pressed = True
        widget.update()  # Trigger a repaint to draw the cross


def mouse_move_event(widget, event):
    if widget.right_button_pressed:
        widget.cursorPos = get_image_coordinates(widget, event.pos())
        widget.draw_cross(widget.cursorPos[0], widget.cursorPos[1])
        widget.update()
    if event.buttons() & Qt.LeftButton:
        widget.end_x, widget.end_y = get_image_coordinates(widget, event.pos())
        widget.end_dx = widget.end_x - event.x()
        widget.end_dy = widget.end_y - event.y()
        widget.update()
        widget.update_image()


def mouse_release_event(widget, event):
    if event.button() == Qt.LeftButton:
        widget.end_x, widget.end_y = get_image_coordinates(widget, event.pos())
        widget.end_dx = widget.end_x - event.x()
        widget.end_dy = widget.end_y - event.y()

        widget.update()
        widget.update_image()

        if valid_coordinates(widget.start_x, widget.start_y, widget.end_x, widget.end_y):
            widget.top_left_x = min(widget.start_x, widget.end_x)
            widget.top_left_y = min(widget.start_y, widget.end_y)
            widget.bottom_right_x = max(widget.start_x, widget.end_x)
            widget.bottom_right_y = max(widget.start_y, widget.end_y)

            if out_of_bounds(widget):
                widget.coords_label.setText("Coordinates: Invalid coordinates!")
                widget.clear_coords()
            elif widget.top_left_x == widget.bottom_right_x or widget.top_left_y == widget.bottom_right_y:  # check if shape is rectangle
                widget.coords_label.setText("Coordinates: Invalid values, shape is not rectangle")
                widget.clear_coords()
            else:
                widget.coords_label.setText(
                    "Coordinates: ({}, {}), ({}, {})".format(widget.top_left_x, widget.top_left_y,
                                                             widget.bottom_right_x,
                                                             widget.bottom_right_y))
        else:
            print("(at least) One of the coordinates is None")

    if event.button() == Qt.RightButton:
        widget.right_button_pressed = False
        widget.cursorPos = event.pos()
        x, y = get_image_coordinates(widget, event.pos())
        widget.draw_cross(x, y)
        widget.update()


def update_image(widget):
    temp_pixmap = widget.pixmap.copy()
    painter = QPainter(temp_pixmap)
    painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
    painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

    if valid_coordinates(widget.start_x, widget.start_y, widget.end_x, widget.end_y):
        top_left_x = min(widget.start_x, widget.end_x)
        top_left_y = min(widget.start_y, widget.end_y)

        width = abs(widget.end_x - widget.start_x)
        height = abs(widget.end_y - widget.start_y)

        painter.drawRect(QRect(top_left_x, top_left_y, width, height))

    painter.end()
    widget.image.setPixmap(temp_pixmap)


def draw_cross(widget, x, y):
    temp_pixmap = widget.pixmap.copy()
    painter = QPainter(temp_pixmap)
    if widget.crossPos and widget.right_button_pressed:
        # widget.drawCross(painter, widget.crossPos)
        painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))

        # Draw horizontal line following the cursor
        # painter.drawLine(0, widget.cursorPos.y() - 13, widget.width(), widget.cursorPos.y() - 13)
        # Draw vertical line following the cursor
        # painter.drawLine(widget.cursorPos.x() - 174, 0, widget.cursorPos.x() - 174, widget.height())
        painter.drawLine(0, y, widget.width(), y)
        painter.drawLine(x, 0, x, widget.height())

    painter.end()
    widget.image.setPixmap(temp_pixmap)


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