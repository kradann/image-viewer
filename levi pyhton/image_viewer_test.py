#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
import shutil
import math
import subprocess
import platform
"""from curses.textpad import rectangle
from functools import partial
from operator import truediv
from traceback import print_tb"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QShortcut, QInputDialog
#QApplication, QWidget, QVBoxLayout, QMainWindow, QGraphicsView, QGraphicsLineItem
from PyQt5.QtGui import QPainter, QPen, QBrush, QPalette, QColor, QKeySequence
#QPixmap, QColor
from PyQt5.QtCore import Qt, QRect
#from markdown_it.rules_inline import image

#QPoint, QLineF

#from qt_utils.sing_types import eu_sign_types, us_sign_types
from sing_types import eu_sign_types, us_sign_types
sign_types = None


class ImageLoader(QtWidgets.QWidget):
    def __init__(self, us):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(10)
        self.set_dark_theme()

        self.us = us
        num_of_columns = 3
        self.image = QtWidgets.QLabel()
        self.pixmap = QtGui.QPixmap(320, 320)
        self.pixmap.fill(Qt.white)  # Fill with white color
        self.image.setPixmap(self.pixmap)
        layout.addWidget(self.image, 0, 0, 1, 3)
        # self.image.setMinimumSize(500, 500)
        # the label alignment property is always maintained even when the contents
        # change, so there is no need to set it each time
        self.image.setAlignment(QtCore.Qt.AlignCenter)

        self.pred_annot = QLabel(self.get_label(), self)
        self.pred_annot.setFixedSize(500, 50)
        layout.addWidget(self.pred_annot, 1, 0, 1, num_of_columns)

        # draw rectangle
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        self.coords_label = QLabel(self)
        self.coords_label.setText("Coordinates: (N/A, N/A)")
        self.coords_label.setFixedSize(500, 50)
        layout.addWidget(self.coords_label, 2, 0, 1, num_of_columns)

        self.info_label = QLabel(self)
        self.info_label.setText("Welcome!")
        layout.addWidget(self.info_label, 2, 0, 1, num_of_columns)
        self.info_label.setAlignment(Qt.AlignRight)

        self.move_func_dict = {
            "something_wrong": self.get_move_func("something_wrong"),
            "to_delete": self.get_move_func("to_delete"),
            "new_ok": self.get_move_func("new_ok"),
            "new_not_a_sign": self.get_move_func("new_not_a_sign"),
            "new_unknown_sign": self.get_move_func("new_unknown_sign"),
        }

        button_size = 40
        self.inputFolderButton = QPushButton('Change Input Folder', self)
        self.inputFolderButton.setFixedHeight(button_size)
        layout.addWidget(self.inputFolderButton, 3, 0)

        self.outputFolderButton = QtWidgets.QPushButton('Change Output Folder')
        self.outputFolderButton.setFixedHeight(button_size)
        layout.addWidget(self.outputFolderButton, 3, 1)

        self.save2dButton = QtWidgets.QPushButton('Save coords')
        self.save2dButton.setFixedHeight(button_size)
        layout.addWidget(self.save2dButton, 3, 2)

        self.prevImageButton = QtWidgets.QPushButton('Previous image')
        self.prevImageButton.setFixedHeight(button_size)
        layout.addWidget(self.prevImageButton, 4, 0)

        self.OkButton = QtWidgets.QPushButton('OK')
        self.OkButton.setFixedHeight(button_size)
        layout.addWidget(self.OkButton, 4, 1)

        self.nextImageButton = QtWidgets.QPushButton('Next image')
        self.nextImageButton.setFixedHeight(button_size * 5)
        layout.addWidget(self.nextImageButton, 4, 2, 5, 1)

        self.moveImageButton = QtWidgets.QPushButton('Move image')
        self.moveImageButton.setFixedHeight(button_size)
        layout.addWidget(self.moveImageButton, 5, 0)

        self.TdButton = QtWidgets.QPushButton('To delete')
        self.TdButton.setFixedHeight(button_size)
        layout.addWidget(self.TdButton, 5, 1)

        self.NasButton = QtWidgets.QPushButton('Not a sign')
        self.NasButton.setFixedHeight(button_size)
        layout.addWidget(self.NasButton, 6, 0)

        self.UsButton = QtWidgets.QPushButton('Unknown sign')
        self.UsButton.setFixedHeight(button_size)
        layout.addWidget(self.UsButton, 6, 1)

        self.AnnotdirButton = QtWidgets.QPushButton('Open annotation directory')
        layout.addWidget(self.AnnotdirButton, 7, 0)

        self.JumpTo = QtWidgets.QPushButton('Jump to')
        layout.addWidget(self.JumpTo, 8, 0)

        self.inputFolderButton.clicked.connect(self.select_input_dir)
        self.outputFolderButton.clicked.connect(self.select_output_dir)
        self.prevImageButton.clicked.connect(self.prev_image)
        self.nextImageButton.clicked.connect(self.next_image)
        self.save2dButton.clicked.connect(self.save_2d)
        self.AnnotdirButton.clicked.connect(self.open_annotation_dir)
        self.JumpTo.clicked.connect(self.jumpto)

        self.moveImageButton.clicked.connect(self.move_func_dict["something_wrong"])
        self.NasButton.clicked.connect(self.not_a_sign)
        self.UsButton.clicked.connect(self.move_func_dict["new_unknown_sign"])
        self.TdButton.clicked.connect(self.move_func_dict["to_delete"])
        self.OkButton.clicked.connect(self.move_func_dict["new_ok"])

        # Dropdown button and combobox
        self.combobox = QComboBox(self)
        self.combobox.addItems(sign_types)
        layout.addWidget(self.combobox, 7, 1)

        self.combobox2 = QComboBox(self)
        self.combobox2.addItems(sign_types)
        layout.addWidget(self.combobox2, 8, 1)

        #self.AnnotdirButton.clicked.connect(partial(self.get_joker_move_funk, self.combobox))
        #self.Joker2Button.clicked.connect(partial(self.get_joker_move_funk, self.combobox2))

        # self.dirIterator = None
        self.file_index = 0
        self.file_list = list()
        self.current_file_name = None
        self.input_dir = None
        self.base_output_dir = None

        self.start_dx = 0
        self.start_dy = 0
        self.end_dx = 0
        self.end_dy = 0

        self.x_back_scale = None
        self.y_back_scale = None

        self.top_left_x = None
        self.top_left_y = None
        self.bottom_right_x = None
        self.bottom_right_y = None
        self.annotation_2d_dict = None

        self.cursorPos = self.rect().center()  # Initialize cursor position
        self.crossPos = None, None  # To store the cross position
        self.right_button_pressed = False
        self.x_off = 0
        self.y_off = 0
        self.coordinates = None
        self.annotation_filename = "annotation_2d.json"

        self.shortcut_save = QShortcut(QKeySequence("S"), self)
        self.shortcut_save.activated.connect(self.save_2d)
        self.shortcut_next1 = QShortcut(QKeySequence("N"), self)
        self.shortcut_next1.activated.connect(self.next_image)
        self.shortcut_next2 = QShortcut(QKeySequence("Right"), self)
        self.shortcut_next2.activated.connect(self.next_image)
        self.shortcut_prev = QShortcut(QKeySequence("P"), self)
        self.shortcut_prev.activated.connect(self.prev_image)

        self.x_offset = 0
        self.y_offset = 0

        self.first = False
        self.select_input_dir()

    def select_input_dir(self):
        self.input_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Input Directory"))

        self.file_list = list()
        try:
            for f in os.listdir(self.input_dir):
                fpath = os.path.join(self.input_dir, f)
                if os.path.isfile(fpath) and f.endswith(('.png', '.jpg', '.jpeg')):
                    self.file_list.append(fpath)
            self.info_label.setText("Input folder loaded!")
        except FileNotFoundError:
            print("Input folder not found ({})".format(self.input_dir))
            return

        self.file_list.sort()
        self.file_index = 0
        self.load_image_and_set_name()
        self.first = False

    def select_output_dir(self):
        self.base_output_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        if self.base_output_dir == "":
            self.base_output_dir = None
        elif self.input_dir is None:
            self.select_input_dir()
            filepath = os.path.join(self.base_output_dir, self.annotation_filename)
            if os.path.isfile(filepath):
                self.load_2d_annot()
        else:
            filepath = os.path.join(self.base_output_dir, self.annotation_filename)
            if os.path.isfile(filepath):
                self.load_2d_annot()

    def load_2d_annot(self):
        if self.directory_check():
            if os.path.isfile(os.path.join(self.base_output_dir, "annotation_2d.json")):
                with (open(os.path.join(self.base_output_dir, "annotation_2d.json"), "r") as stream):
                    self.annotation_2d_dict = json.load(stream)
                    #filename = self.current_file_name.split('/')[-1]
                    if os.path.basename(self.current_file_name) in self.annotation_2d_dict:
                        self.coordinates = self.annotation_2d_dict[os.path.basename(self.current_file_name)]
                        #print(self.coordinates)
                        if len(self.coordinates) == 4 and self.coordinates[0] is not None and self.coordinates[1] is not None and self.coordinates[2] is not None and self.coordinates[3] is not None:
                            x1,y1,x2,y2 = self.coordinates
                            x1 = int(math.floor(x1/self.x_back_scale))
                            y1 = int(math.floor(y1/self.y_back_scale))
                            x2 = int(math.ceil(x2/self.x_back_scale))
                            y2 = int(math.ceil(y2/self.y_back_scale))
                            temp_pixmap = self.pixmap.copy()
                            painter = QPainter(temp_pixmap)
                            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                            painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                            painter.drawRect(QRect(x1,y1,x2-x1,y2-y1))
                            painter.end()
                            self.image.setPixmap(temp_pixmap)
                            self.info_label.setText("Box loaded!")
                    else:
                        self.info_label.setText("File name not found!")
            else:
                self.info_label.setText("No annotation_2d.json found or no output directory!")
                self.annotation_2d_dict = dict()
        else:
            self.info_label.setText("In or output directory not found!")

    def save_2d(self):
        if self.directory_check():
            if self.annotation_2d_dict is None:
                self.load_2d_annot()

            if (self.top_left_x is not None and
                    self.top_left_y is not None and
                    self.bottom_right_x is not None and
                    self.bottom_right_y is not None):
                self.annotation_2d_dict[os.path.basename(self.current_file_name)] = [self.top_left_x * self.x_back_scale,
                                                                                     self.top_left_y * self.y_back_scale,
                                                                                     self.bottom_right_x * self.x_back_scale,
                                                                                     self.bottom_right_y * self.y_back_scale]
                with open(os.path.join(self.base_output_dir, "annotation_2d.json"), "w") as f:
                    json.dump(self.annotation_2d_dict, f, indent=4)
                self.info_label.setText("Coordinates have been saved!")
            else:
                self.info_label.setText("2d annotation can not be saved!")
        else:
            self.info_label.setText("In or output directory not found!")

    def load_image_and_set_name(self):
        if self.file_list:
            filename = self.file_list[self.file_index % len(self.file_list)]
            self.pixmap = QtGui.QPixmap(filename)
            ori_width, ori_height = self.pixmap.width(), self.pixmap.height()
            if self.pixmap.isNull():
                # the file is not a valid image, remove it from the list
                # and try to load the next one
                print("file is removed from the list because it is not valid ({})".format(filename))
                self.file_list.remove(filename)
                self.load_image_and_set_name()
            else:
                self.pixmap = self.pixmap.scaled(self.image.size(), QtCore.Qt.KeepAspectRatio)
                current_width, current_height = self.pixmap.width(), self.pixmap.height()
                self.x_back_scale = ori_width / current_width
                self.y_back_scale = ori_height / current_height
                self.image.setPixmap(self.pixmap)
                self.current_file_name = filename
                self.load_2d_annot()
                self.setWindowTitle(os.path.basename(self.current_file_name))
                if (self.file_index % len(self.file_list) == 0) and self.first is False:
                    self.info_label.setText("{} Images loaded!".format(len(self.file_list)))

                elif self.file_index % len(self.file_list) == 0 and self.first :
                    self.info_label.setText("Image (1/{}) loaded!".format(len(self.file_list)))
                else:
                    self.info_label.setText("Image ({}/{}) loaded!".format( self.file_index % len(self.file_list)+1,len(self.file_list)))
                self.pred_annot.setText(self.get_label(os.path.basename(self.current_file_name)))

    def next_image(self):
        # ensure that the file list has not been cleared due to missing files
        if self.file_list:
            self.first = True
            self.file_index += 1
            self.load_image_and_set_name()
            self.clear_coords()
        else:
            self.info_label.setText("No directory loaded!")


    def prev_image(self):
        # ensure that the file list has not been cleared due to missing files
        if self.file_list:
            self.first = True
            self.file_index -= 1
            self.load_image_and_set_name()
            self.clear_coords()
        else:
            self.info_label.setText("No directory loaded!")

    def clear_coords(self):
        self.coords_label.setText("Coordinates: (N/A, N/A)")
        self.top_left_x = None
        self.top_left_y = None
        self.bottom_right_x = None
        self.bottom_right_y = None

    def get_move_func(self, file_name: str):
        def move_func():
            if self.base_output_dir is None:
                self.select_output_dir()

            if self.base_output_dir is not None:
                self.move_file(file_name)
            else:
                print("first select output dir")
        return move_func

    def get_joker_move_funk(self, combobox):
        joker_move_funk = self.get_move_func("new_" + combobox.currentText())
        joker_move_funk()

    def move_file(self, file_name: str):
        dst_dir = os.path.join(self.base_output_dir, file_name)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(self.current_file_name))
        try:
            print("dst path: {}".format(dst))
            shutil.move(self.current_file_name, dst)
        except FileNotFoundError:
            print("Error during moving file: {}".format(dst))

    # draw rectangle
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_x, self.start_y= self.get_image_coordinates(event.pos())
            self.end_x = self.start_x
            self.end_y = self.start_y
            
            self.start_dx = self.start_x - event.x()
            self.start_dy = self.start_y - event.y()
            self.end_dx = 0
            self.end_dy = 0

            self.update()
            self.update_image()
        if event.button() == Qt.RightButton:
            self.crossPos = self.get_image_coordinates(event.pos()) # Store the position of the right-click
            self.right_button_pressed = True
            self.update()  # Trigger a repaint to draw the cross

    def mouseMoveEvent(self, event):
        if self.right_button_pressed:
            self.cursorPos = self.get_image_coordinates(event.pos())
            self.drawCross(self.cursorPos[0], self.cursorPos[1])
            self.update()
        if event.buttons() & Qt.LeftButton:
            self.end_x, self.end_y= self.get_image_coordinates(event.pos())
            self.end_dx = self.end_x - event.x()
            self.end_dy = self.end_y - event.y()
            self.update()
            self.update_image()


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_x, self.end_y= self.get_image_coordinates(event.pos())
            self.end_dx = self.end_x - event.x()
            self.end_dy = self.end_y - event.y()

            self.update()
            self.update_image()

            if self.start_x is not None and self.start_y is not None and self.end_x is not None and self.end_y is not None:
                self.top_left_x = min(self.start_x, self.end_x)
                self.top_left_y = min(self.start_y, self.end_y)
                self.bottom_right_x = max(self.start_x, self.end_x)
                self.bottom_right_y = max(self.start_y, self.end_y)

                image_width = self.image.width()-self.x_off
                image_height = self.image.height()-self.y_off


                if (self.top_left_x < 0 or self.top_left_x > image_width or self.top_left_y < 0 or self.top_left_y > image_height or # check if top left point is in the pixmap
                      self.bottom_right_x < 0 or self.bottom_right_x > image_width or self.bottom_right_y < 0 or self.bottom_right_y > image_height): # check if bottom right point is in the pixmap
                    self.coords_label.setText("Coordinates: Invalid coordinates!")
                    self.clear_coords()
                elif self.top_left_x == self.bottom_right_x or self.top_left_y == self.bottom_right_y: # check if shape is rectangle
                    self.coords_label.setText("Coordinates: Invalid values, shape is not rectangle")
                    self.clear_coords()
                else:
                    self.coords_label.setText("Coordinates: ({}, {}), ({}, {})".format(self.top_left_x, self.top_left_y, self.bottom_right_x, self.bottom_right_y))
            else:
                print("(at least) One of the coordinates is None")

        if event.button() == Qt.RightButton:
            self.right_button_pressed = False
            self.cursorPos = event.pos()
            x,y = self.get_image_coordinates(event.pos())
            self.drawCross(x,y)
            self.update()


    """def paintEvent(self, event):
        painter = QPainter(self)
        if self.start_x is not None and self.start_y is not None and self.end_x is not None and self.end_y is not None:

            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
            painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

            top_left_x = min(self.start_x - self.start_dx, self.end_x - self.end_dx)
            top_left_y = min(self.start_y - self.start_dy, self.end_y - self.end_dy)

            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            painter.drawRect(QRect(top_left_x, top_left_y, width, height))

        painter.end()"""

    def update_image(self):
        temp_pixmap = self.pixmap.copy()
        painter = QPainter(temp_pixmap)
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

        if self.start_x is not None and self.start_y is not None and self.end_x is not None and self.end_y is not None:
            top_left_x = min(self.start_x, self.end_x)
            top_left_y = min(self.start_y, self.end_y)

            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)

            painter.drawRect(QRect(top_left_x, top_left_y, width, height))

        painter.end()
        self.image.setPixmap(temp_pixmap)

    def drawCross(self,x,y):
        temp_pixmap = self.pixmap.copy()
        painter = QPainter(temp_pixmap)
        if self.crossPos and self.right_button_pressed:
            #self.drawCross(painter, self.crossPos)
            painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))

            # Draw horizontal line following the cursor
            #painter.drawLine(0, self.cursorPos.y() - 13, self.width(), self.cursorPos.y() - 13)
            # Draw vertical line following the cursor
            #painter.drawLine(self.cursorPos.x() - 174, 0, self.cursorPos.x() - 174, self.height())
            painter.drawLine(0,y, self.width(),y)
            painter.drawLine(x, 0,x, self.height())

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

    def get_label(self, file_name: str = None):
        if self.us:
            pred, annot = "-", "-"
            return "prediction: {}\nannotation: {}".format(pred, annot)
        else:
            if file_name is None:
                return "prediction:\nannotation:"
            else:
                # eu_additional_panel_(eu_additional_panel)_2185.jpg
                try:
                    pred, annot = file_name.split("_(")
                    annot, _ = annot.split(")_")
                except ValueError:
                    print("file name convention error ({})".format(file_name))
                    pred, annot = "-", "-"
                return "prediction: {}\nannotation: {}".format(pred, annot)

    def set_dark_theme(self):
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(45,45,48)) #Background color
        palette.setColor(QPalette.WindowText, Qt.white) #Text color

        #palette.setColor(QPalette.Button, QColor(60,70,80)) #Button color
        palette.setColor(QPalette.ButtonText, Qt.black) #Buttontext color

        self.setPalette(palette)

    def open_annotation_dir(self):
        self.directory_check()
        if os.path.isfile(os.path.join(self.base_output_dir, "annotation_2d.json")):
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{self.base_output_dir}"')
            else:  # Linux
                subprocess.Popen(["xdg-open", self.base_output_dir])
            self.info_label.setText("Folder opened!")
        else:
             self.info_label.setText("annotation_2d.json not found!")


    def not_a_sign(self):
        self.directory_check()
        if os.path.isfile(os.path.join(self.base_output_dir, "annotation_2d.json")):
            self.annotation_2d_dict[os.path.basename(self.current_file_name)] = [None,None,None,None]
            with open(os.path.join(self.base_output_dir, "annotation_2d.json"), "w") as f:
                json.dump(self.annotation_2d_dict, f, indent=4)
        else:
            self.info_label.setText("annotation_2d.json not found!")

    def directory_check(self):
        if self.input_dir is None:
            self.select_input_dir()
        if self.base_output_dir is None:
            self.select_output_dir()
        if self.input_dir is not None and self.base_output_dir is not None:
            return True
        else:
            return False

    def jumpto(self):
        self.directory_check()
        num, ok = QInputDialog.getInt(self, "Input Image Number", "Enter image number:")

        if ok:
            # Create the image file path based on the entered number
            if 0 < num < len(self.file_list)+1:
                self.file_index = int(num)-1
                self.load_image_and_set_name()
                self.clear_coords()
            else:
                self.info_label.setText("Incorrect image number!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--us", default=False, action="store_true", help="Use US signs instead of EU")
    args = parser.parse_args()
    sign_types = us_sign_types if args.us else eu_sign_types

    app = QtWidgets.QApplication(sys.argv)
    imageLoader = ImageLoader(args.us)
    # width = imageLoader.frameGeometry().width()
    # height = imageLoader.frameGeometry().height()

    imageLoader.setFixedSize(600, 800)
    imageLoader.show()
    sys.exit(app.exec_())

    # with open("./annotation_check/check_4/annotation_2d.json", "r") as stream:
    #     annotation_2d_dict = json.load(stream)
    #
    # for image_name, bbox in annotation_2d_dict.items():
    #     top_left_x, top_left_y, bottom_right_x, bottom_right_y = [int(i) for i in bbox]
    #     img = cv2.imread(os.path.join("./annotation_check/check_4/wrong_box", image_name))
    #     cv2.rectangle(img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255, 0, 0), 1)
    #     cv2.imshow(image_name, img)
    #     cv2.waitKey(0)



