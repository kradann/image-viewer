import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush

# from qt_annotation_tool import AnnotationTool
from utils.file_manager import FileManager
from utils.utils import valid_coordinates, out_of_bounds


class ImageManager(object):
    def __init__(self, widget, file_manager: FileManager):
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

        self.start_dx = 0
        self.start_dy = 0
        self.end_dx = 0
        self.end_dy = 0

        self.x_back_scale = None
        self.y_back_scale = None

        self.x_offset = 0
        self.y_offset = 0

        self.top_left_x = None
        self.top_left_y = None
        self.bottom_right_x = None
        self.bottom_right_y = None
        self.annotation_2d_dict = None

        self.cursor_pos = self.widget.rect().center()  # Initialize cursor position
        self.cross_pos = None, None  # To store the cross position
        self.right_button_pressed = False
        self.coordinates = None

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

    def update_image(self):
        temp_pixmap = self.pixmap.copy()
        painter = QPainter(temp_pixmap)
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

        if valid_coordinates(self.start_x, self.start_y, self.end_x, self.end_y):
            top_left_x = min(self.start_x, self.end_x)
            top_left_y = min(self.start_y, self.end_y)

            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            painter.drawRect(QRect(top_left_x, top_left_y, width, height))

        painter.end()
        self.image.setPixmap(temp_pixmap)


    # draw rectangle
    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.start_x, self.start_y = self.get_image_coordinates(event.pos())
            self.end_x = self.start_x
            self.end_y = self.start_y

            self.start_dx = self.start_x - event.x()
            self.start_dy = self.start_y - event.y()
            self.end_dx = 0
            self.end_dy = 0

            self.widget.update()
            self.update_image()
        if event.button() == Qt.RightButton:
            self.cross_pos = self.get_image_coordinates(event.pos())  # Store the position of the right-click
            self.right_button_pressed = True
            self.widget.update()  # Trigger a repaint to draw the cross


    def mouse_move_event(self, event):
        if self.right_button_pressed:
            self.cross_pos = self.get_image_coordinates(event.pos())
            self.draw_cross(self.cross_pos[0], self.cross_pos[1])
            self.widget.update()
        if event.buttons() & Qt.LeftButton:
            self.end_x, self.end_y = self.get_image_coordinates(event.pos())
            self.end_dx = self.end_x - event.x()
            self.end_dy = self.end_y - event.y()
            self.widget.update()
            self.update_image()


    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton:
            self.end_x, self.end_y = self.get_image_coordinates(event.pos())
            self.end_dx = self.end_x - event.x()
            self.end_dy = self.end_y - event.y()

            self.widget.update()
            self.update_image()

            if valid_coordinates(self.start_x, self.start_y, self.end_x, self.end_y):
                self.top_left_x = min(self.start_x, self.end_x)
                self.top_left_y = min(self.start_y, self.end_y)
                self.bottom_right_x = max(self.start_x, self.end_x)
                self.bottom_right_y = max(self.start_y, self.end_y)

                if out_of_bounds(self):
                    self.widget.coords_label.setText("Coordinates: Invalid coordinates!")
                    self.clear_coords()
                elif self.top_left_x == self.bottom_right_x or self.top_left_y == self.bottom_right_y:  # check if shape is rectangle
                    self.widget.coords_label.setText("Coordinates: Invalid values, shape is not rectangle")
                    self.clear_coords()
                else:
                    self.widget.coords_label.setText(
                        "Coordinates: ({}, {}), ({}, {})".format(self.top_left_x, self.top_left_y,
                                                                 self.bottom_right_x,
                                                                 self.bottom_right_y))
            else:
                print("(at least) One of the coordinates is None")

        if event.button() == Qt.RightButton:
            self.right_button_pressed = False
            self.cursor_pos = event.pos()
            x, y = self.get_image_coordinates(event.pos())
            self.draw_cross(x, y)
            self.widget.update()


    def draw_cross(self, x, y):
        temp_pixmap = self.pixmap.copy()
        painter = QPainter(temp_pixmap)
        if self.cross_pos and self.right_button_pressed:
            # widget.drawCross(painter, widget.crossPos)
            painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))

            # Draw horizontal line following the cursor
            # painter.drawLine(0, widget.cursorPos.y() - 13, widget.width(), widget.cursorPos.y() - 13)
            # Draw vertical line following the cursor
            # painter.drawLine(widget.cursorPos.x() - 174, 0, widget.cursorPos.x() - 174, widget.height())
            painter.drawLine(0, y, self.widget.width(), y)
            painter.drawLine(x, 0, x, self.widget.height())

        painter.end()
        self.image.setPixmap(temp_pixmap)


    def get_image_coordinates(self, pos):
        # Get the position of the click relative to the QLabel
        relative_pos = pos - self.image.pos()

        # Get the size of the QLabel and the Pixmap
        label_width = self.image.width()
        label_height = self.image.height()
        pixmap_width = self.pixmap.width()
        pixmap_height = self.pixmap.height()

        # Calculate the position of the Pixmap within the QLabel
        if self.image.hasScaledContents():
            x_ratio = pixmap_width / label_width
            y_ratio = pixmap_height / label_height
            return relative_pos.x() * x_ratio, relative_pos.y() * y_ratio
        else:
            self.x_offset = (label_width - pixmap_width) // 2
            self.y_offset = (label_height - pixmap_height) // 2
            return relative_pos.x() - self.x_offset, relative_pos.y() - self.y_offset

    def clear_coords(self):
        self.widget.coords_label.setText("Coordinates: (N/A, N/A)")
        self.top_left_x = None
        self.top_left_y = None
        self.bottom_right_x = None
        self.bottom_right_y = None