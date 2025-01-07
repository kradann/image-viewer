import math

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush

# from qt_annotation_tool import AnnotationTool
from utils.file_manager import FileManager
from utils.utils import valid_coordinates, out_of_bounds
from utils.box_manager import BoxManager
from utils.box import Box

class ImageManager(object):
    def __init__(self, widget, file_manager: FileManager, box_manager: BoxManager):
        self.widget = widget
        self.file_manager = file_manager
        self.box_manager = box_manager
        self.image = QtWidgets.QLabel()
        self.pixmap = QtGui.QPixmap(320, 320)
        self.pixmap.fill(Qt.white)  # Fill with white color
        self.image.setPixmap(self.pixmap)

        # draw rectangle
        self.start_x, self.start_y = None, None
        self.end_x, self.end_y = None, None

        self.start_dx, self.start_dy = 0, 0
        self.end_dx, self.end_dy = 0, 0

        self.x_back_scale, self.y_back_scale = None, None
        self.x_offset, self.y_offset = 0, 0

        self.corner_to_grab_x, self.corner_to_grab_y = None, None

        self.top_left_x, self.top_left_y = None, None
        self.bottom_right_x, self.bottom_right_y = None, None
        self.last_left_x, self.last_left_y = None, None
        self.last_right_x, self.last_right_y = None, None
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
            tl_x = min(self.start_x, self.end_x)
            tl_y = min(self.start_y, self.end_y)

            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            painter.drawRect(QRect(tl_x, tl_y, width, height))

        painter.end()
        self.image.setPixmap(temp_pixmap)

    # draw rectangle
    def mouse_press_event(self, event):
        def get_corner(x, y):
            center_x = (self.top_left_x + self.bottom_right_x) / 2
            center_y = (self.top_left_y + self.bottom_right_y) / 2

            if x <= center_x:
                self.start_x = x
                self.end_x = self.bottom_right_x
            else:
                self.end_x = x
                self.start_x = self.top_left_x

            if y <= center_y:
                self.start_y = y
                self.end_y = self.bottom_right_y
            else:
                self.end_y = y
                self.start_y = self.top_left_y

            corner_x = "sx" if x <= center_x else "ex"
            corner_y = "sy" if y <= center_y else "ey"
            return corner_x, corner_y

        if event.button() == Qt.LeftButton:
            if self.top_left_x is None:
                self.start_x, self.start_y = self.get_image_coordinates(event.pos())
                self.end_x = self.start_x
                self.end_y = self.start_y

                self.start_dx = self.start_x - event.x()
                self.start_dy = self.start_y - event.y()
                self.end_dx = 0
                self.end_dy = 0

                self.widget.update()
                self.update_image()
            else:
                start_x, start_y = self.get_image_coordinates(event.pos())
                self.corner_to_grab_x, self.corner_to_grab_y = get_corner(start_x, start_y)
                self.widget.update()
                self.update_image()

        if event.button() == Qt.RightButton:
            self.cross_pos = self.get_image_coordinates(event.pos())  # Store the position of the right-click
            self.right_button_pressed = True
            self.widget.update()  # Trigger a repaint to draw the cross

    def mouse_move_event(self, event):
        if event.buttons() & Qt.LeftButton and not self.right_button_pressed:
            if self.top_left_x is None:
                self.end_x, self.end_y = self.get_image_coordinates(event.pos())
                self.end_dx = self.end_x - event.x()
                self.end_dy = self.end_y - event.y()
                self.widget.update()
                self.update_image()
            else:
                x, y = self.get_image_coordinates(event.pos())

                if self.corner_to_grab_x == "sx":
                    self.start_x = x
                else:
                    self.end_x = x

                if self.corner_to_grab_y == "sy":
                    self.start_y = y
                else:
                    self.end_y = y

                self.widget.update()
                self.update_image()

        if self.right_button_pressed:
            self.cross_pos = self.get_image_coordinates(event.pos())
            self.draw_cross(self.cross_pos[0], self.cross_pos[1])
            self.widget.update()

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton:
            if self.top_left_x is None:
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
                    self.clear_coords()
                elif self.top_left_x == self.bottom_right_x or self.top_left_y == self.bottom_right_y:  # check if shape is rectangle
                    self.clear_coords()
                else:
                    self.widget.set_coords_label(self.top_left_x,
                                                 self.top_left_y,
                                                 self.bottom_right_x,
                                                 self.bottom_right_y, "yellow")
                    self.widget.set_info_label("Not saved yet", "yellow")
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

    def get_coords_from_annotation(self, annotation_dict, set_to_current):
        if annotation_dict is None:
            x1 = self.last_left_x
            y1 = self.last_left_y
            x2 = self.last_right_x
            y2 = self.last_right_y
            if set_to_current:
                self.top_left_x = x1
                self.top_left_y = y1
                self.bottom_right_x = x2
                self.bottom_right_y = y2
            return x1, y1, x2, y2

        if all([annotation_dict.x_1 is not None,
                annotation_dict.y_1 is not None,
                annotation_dict.x_2 is not None,
                annotation_dict.y_2 is not None]):
            x1 = math.floor(annotation_dict.x_1 / self.x_back_scale)
            y1 = math.floor(annotation_dict.y_1 / self.y_back_scale)
            x2 = math.floor(annotation_dict.x_2 / self.x_back_scale)
            y2 = math.floor(annotation_dict.y_2 / self.y_back_scale)

            if set_to_current:
                self.top_left_x = x1
                self.top_left_y = y1
                self.bottom_right_x = x2
                self.bottom_right_y = y2
            return x1, y1, x2, y2
        else:
            return None, None, None, None

    def draw_rect_from_box_list(self, box_list=None , set_to_current=False, copy=True, text=None):
        for box in box_list:
            x1, y1, x2, y2 = box.x_1, box.y_1, box.x_2, box.y_2
            color = box.color
            print(color)
            if x1 is not None:
                if copy:
                    temp_pixmap = self.pixmap.copy()
                else:
                    temp_pixmap = self.pixmap
                painter = QPainter(temp_pixmap)
                painter.setPen(QPen(color, 2, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                if text is not None:
                    painter.drawText(x1, y2 + 11, text)
                painter.end()
                self.image.setPixmap(temp_pixmap)
            self.widget.set_coords_label(x1, y1, x2, y2, "cyan")

    def set_last_coords(self):
        self.last_left_x = self.top_left_x
        self.last_left_y = self.top_left_y
        self.last_right_x = self.bottom_right_x
        self.last_right_y = self.bottom_right_y

    def set_last_coords_to_none(self):
        self.last_left_x = None
        self.last_left_y = None
        self.last_right_x = None
        self.last_right_y = None

    def get_back_scaled_coords(self):
        x1 = self.top_left_x * self.x_back_scale
        y1 = self.top_left_y * self.y_back_scale
        x2 = self.bottom_right_x * self.x_back_scale
        y2 = self.bottom_right_y * self.y_back_scale
        return x1, y1, x2, y2

    def clear_coords(self):
        self.widget.set_coords_label(-1, -1, -1, -1, "red")
        self.widget.set_info_label("Wrong coordinates", "red")
        self.top_left_x = None
        self.top_left_y = None
        self.bottom_right_x = None
        self.bottom_right_y = None

    def previous_box(self):
        self.box_manager.previous()
        self.draw_rect_from_box_list(self.box_manager.coord_list, False,True, None)

    def next_box(self):
        self.box_manager.next()
        for box in self.box_manager.coord_list:
            print(box)
        self.update_rectangles()

    def add_box(self):
        self.start_x = 100
        self.start_y = 100
        self.end_x = 200
        self.end_y= 200
        temp_box = Box(self.start_x,self.start_y,self.end_x,self.end_y, False, "unknown_sign" , True)
        self.box_manager.coord_list.append(temp_box)
        self.update_image()

    def update_rectangles(self):
        # Clear only the transparent pixmap, not the background image
        self.rectangles_pixmap.fill(Qt.transparent)

        # Combine the background image with the transparent pixmap for rectangles
        combined_pixmap = self.image_pixmap.copy()  # Keep the original background
        painter = QPainter(combined_pixmap)
        painter.drawPixmap(0, 0, self.rectangles_pixmap)  # Overlay the transparent layer
        painter.end()

        # Update the QLabel to display the combined pixmap
        self.image.setPixmap(combined_pixmap)
