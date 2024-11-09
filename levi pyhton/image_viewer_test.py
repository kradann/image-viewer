#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import json
import math
import os
import platform
import shutil
import subprocess
import sys

#from PIL.ImageMath import imagemath_equal

"""from curses.textpad import rectangle
from functools import partial
from operator import truediv
from traceback import print_tb"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QShortcut, QInputDialog, QMenu, QAction
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

        self.saved_check_label = QLabel(self)
        self.saved_check_label.setText("----------")
        self.saved_check_label.setStyleSheet("font-size: 18px; color: white;")  # Set font size to 18px and color to white
        layout.addWidget(self.saved_check_label, 2, 0, 2, num_of_columns)

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
        self.nextImageButton.setFixedHeight(button_size * 4)
        layout.addWidget(self.nextImageButton, 4, 2,4,1)

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

        self.checker = QtWidgets.QPushButton('Checking')
        self.nextImageButton.setFixedHeight(button_size*4)
        layout.addWidget(self.checker, 8, 2,1,1)

        self.inputFolderButton.clicked.connect(self.select_input_dir)
        self.outputFolderButton.clicked.connect(self.select_output_dir)
        self.prevImageButton.clicked.connect(self.prev_image)
        self.nextImageButton.clicked.connect(self.next_image)
        self.save2dButton.clicked.connect(self.save_2d)
        self.AnnotdirButton.clicked.connect(self.open_annotation_dir)
        self.JumpTo.clicked.connect(self.jumpto)
        self.checker.clicked.connect(self.checking)

        self.moveImageButton.clicked.connect(self.move_func_dict["something_wrong"])
        self.NasButton.clicked.connect(self.not_a_sign)
        self.UsButton.clicked.connect(self.move_func_dict["new_unknown_sign"])
        self.TdButton.clicked.connect(self.move_func_dict["to_delete"])
        self.OkButton.clicked.connect(self.move_func_dict["new_ok"])

        # Dropdown button and combobox
        """self.combobox = QComboBox(self)
        self.combobox.addItems(sign_types)"""

        self.button = QPushButton("No input file",self)

        self.menu = QMenu(self)
        for i in sign_types:
            action = QAction(i, self)
            action.triggered.connect(self.menu_item_selected)  # Connect to selection handler
            self.menu.addAction(action)
        self.button.setMenu(self.menu)

        layout.addWidget(self.button, 7, 1)
        """self.list = QListWidget(self)
        self.list.addItems(sign_types)
        layout.addWidget(self.list, 7, 1)"""

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
        self.coordinates = None
        self.annotation_filename = "eu_2_annotation.json"

        self.shortcut_save = QShortcut(QKeySequence("S"), self)
        self.shortcut_save.activated.connect(self.save_2d)

        self.shortcut_next1 = QShortcut(QKeySequence("N"), self)
        self.shortcut_next1.activated.connect(self.next_image)

        self.shortcut_next2 = QShortcut(QKeySequence("Right"), self)
        self.shortcut_next2.activated.connect(self.next_image)

        self.shortcut_prev = QShortcut(QKeySequence("P"), self)
        self.shortcut_prev.activated.connect(self.prev_image)

        self.shortcut_not_a_sign = QShortcut(QKeySequence("V"), self)
        self.shortcut_not_a_sign.activated.connect(self.not_a_sign)

        self.shortcut_to_delete = QShortcut(QKeySequence("D"), self)
        self.shortcut_to_delete.activated.connect(self.move_func_dict["to_delete"])

        self.x_offset = 0
        self.y_offset = 0

        self.first = False
        self.current_label = ""
        self.full_current_file_name = None
        self.state = None

        self.last_left_x = None
        self.last_left_y = None
        self.last_right_x = None
        self.last_right_y = None

        self.last_label = None
        self.current_batch_index = None
        self.last_batch_index = None
        self.last_image = None

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

        if self.directory_check():
            last_index_file = os.path.join(self.base_output_dir, "last_index.json")

            if os.path.isfile(last_index_file):
                with open(last_index_file, "r") as stream:
                    try:
                        self.state = json.load(stream)
                        # Ensure self.state is a dictionary, not a list or string
                        if isinstance(self.state, dict):
                            # Check if "last_image_index" exists and load it
                            if "last_image_index" in self.state:
                                self.file_index = self.state["last_image_index"]
                            else:
                                self.info_label.setText("last_image_index key not found in the JSON file.")
                        else:
                            self.info_label.setText("Unexpected data structure in the last_index.json file.")
                    except json.JSONDecodeError:
                        self.info_label.setText("Error loading last_index.json, possibly corrupt.")
            else:
                self.info_label.setText("No last_index.json file found.")

            self.load_image_and_set_name()

        else:
            self.info_label.setText("No input or output directory")


    def load_2d_annot(self):
        if self.directory_check():
            if os.path.isfile(os.path.join(self.base_output_dir, "eu_2_annotation.json")):
                with ((open(os.path.join(self.base_output_dir, "eu_2_annotation.json"), "r"))as stream):
                    self.annotation_2d_dict = json.load(stream)
                    #filename = self.current_file_name.split('/')[-1]
                    entry = self.search_annotation_by_image_name(self.annotation_2d_dict,self.full_current_file_name)
                    if entry is not None:
                        #print(self.coordinates)
                        if all([entry["x1"] is not None , entry["y1"] is not None, entry["x2"] is not None, entry["y2"] is not None]) :
                            self.saved_check_label.setText("Saved")
                            x1 = math.floor(entry["x1"]/self.x_back_scale)
                            y1 = math.floor(entry["y1"]/self.y_back_scale)
                            x2 = math.floor(entry["x2"]/self.x_back_scale)
                            y2 = math.floor(entry["y2"]/self.y_back_scale)
                            self.last_left_x = x1
                            self.last_left_y = y1
                            self.last_right_x = x2
                            self.last_right_y = y2
                            if entry["label"] == "unknown":
                                self.current_label = "unknown_sign"
                                self.button.setText("unknown_sign")
                            else:
                                for action in self.menu.actions():
                                    if action.text() == entry["label"]:
                                        self.current_label = entry["label"]
                                        self.button.setText(entry["label"])

                            temp_pixmap = self.pixmap.copy()
                            painter = QPainter(temp_pixmap)
                            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                            painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                            painter.drawRect(QRect(x1,y1,x2-x1,y2-y1))
                            painter.end()
                            self.image.setPixmap(temp_pixmap)
                            self.info_label.setText("Box loaded!")

                        else:
                            self.info_label.setText("save as Not a sign")
                            self.saved_check_label.setText("Saved")
                    else:
                        self.saved_check_label.setText("Not saved")
                        if self.last_left_x is not None and self.last_left_y is not None and self.last_right_x is not None and self.last_right_y is not None:
                            #draw previous box
                            temp_pixmap = self.pixmap.copy()
                            painter = QPainter(temp_pixmap)
                            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                            painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                            painter.drawRect(QRect(self.last_left_x, self.last_left_y, self.last_right_x - self.last_left_x, self.last_right_y - self.last_left_y))
                            painter.end()
                            self.image.setPixmap(temp_pixmap)

                            self.top_left_x = self.last_left_x
                            self.top_left_y = self.last_left_y
                            self.bottom_right_x = self.last_right_x
                            self.bottom_right_y = self.last_right_y
                    self.coords_label.setText(
                        "Coordinates: ({}, {}), ({}, {})".format(self.last_left_x, self.last_left_y,
                                                                 self.last_right_x, self.last_right_y))

            else:
                self.info_label.setText("No annotation_2d.json found or no output directory!")
                self.annotation_2d_dict = dict()
        else:
            self.info_label.setText("In or output directory not found!")

    def save_2d(self):
        if self.directory_check():
            if self.annotation_2d_dict is None:
                self.load_2d_annot()

            if self.valid_coordinates(self.top_left_x, self.top_left_y, self.bottom_right_x, self.bottom_right_y):
                annotation_entry = {
                    "image_name": os.path.basename(self.full_current_file_name),
                    "label": self.current_label,
                    "x1": self.top_left_x * self.x_back_scale,
                    "y1": self.top_left_y * self.y_back_scale,
                    "x2": self.bottom_right_x * self.x_back_scale,
                    "y2": self.bottom_right_y * self.y_back_scale
                }

                self.last_left_x = self.top_left_x
                self.last_left_y = self.top_left_y
                self.last_right_x = self.bottom_right_x
                self.last_right_y = self.bottom_right_y

                self.saved_check_label.setText("Saved")
                # Load existing annotations if any
                annotation_file_path = os.path.join(self.base_output_dir, "eu_2_annotation.json")

                if os.path.exists(annotation_file_path):
                    with open(annotation_file_path, "r") as f:
                        self.annotation_2d_dict = json.load(f)
                else:
                    self.annotation_2d_dict = []

                # Find if the image annotation already exists
                found = False

                for entry in self.annotation_2d_dict:
                    if entry["image_name"] == annotation_entry["image_name"]:
                        # Update existing entry
                        entry.update(annotation_entry)
                        found = True
                        break

                if not found:
                    # If the entry doesn't exist, append the new annotation entry
                    self.annotation_2d_dict.append(annotation_entry)

                # Save back the updated annotations
                with open(annotation_file_path, "w") as f:
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
                self.full_current_file_name = os.path.basename(filename)
                self.current_file_name = filename.split('_')[-1]

                self.setWindowTitle(os.path.basename(self.full_current_file_name))

                self.current_batch_index = self.full_current_file_name.split('_')[0]

                first_underscore_idx = os.path.basename(self.full_current_file_name).find('_')  # Index of the first underscore
                last_underscore_idx = os.path.basename(self.full_current_file_name).rfind('_')  # Index of the last underscore

                if self.current_batch_index != self.last_batch_index:
                    if first_underscore_idx != -1 and last_underscore_idx != -1 and first_underscore_idx < last_underscore_idx:
                        predicted_label = os.path.basename(self.full_current_file_name)[first_underscore_idx + 1:last_underscore_idx]  # Predicted label is between the first and last underscore
                        found_label = False
                        for action in self.menu.actions():
                            if predicted_label == action.text():
                                self.current_label = predicted_label
                                self.button.setText(predicted_label)
                                found_label = True
                        if not found_label:
                            self.current_label = "unknown_sign"
                            self.button.setText("unknown_sign")
                else:
                    self.current_label = self.last_label

                self.load_2d_annot()

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
            self.last_batch_index = self.full_current_file_name.split('_')[0]
            self.last_image = self.search_annotation_by_image_name(self.annotation_2d_dict, self.full_current_file_name)
            if self.last_image is not None:
                self.last_label = self.last_image["label"]

            print(self.last_label)
            print(self.last_batch_index)
            self.load_image_and_set_name()

        else:
            self.info_label.setText("No directory loaded!")

    def prev_image(self):
        # ensure that the file list has not been cleared due to missing files
        if self.file_list:
            self.first = True
            self.file_index -= 1
            self.last_batch_index = self.full_current_file_name.split('_')[0]
            self.load_image_and_set_name()

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
        dst = os.path.join(dst_dir, self.full_current_file_name)
        try:
            print("dst path: {}".format(dst))
            shutil.copy2(os.path.join(self.input_dir, self.full_current_file_name), dst)  # Copy instead of move


            if file_name == "to_delete":
                original_file_path = os.path.join(self.input_dir, self.full_current_file_name)
                os.remove(original_file_path)
                print("Original file deleted from source: {}".format(original_file_path))
                self.info_label.setText("Deleted!")
            else:
                self.info_label.setText("Copied!")
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

            if self.valid_coordinates(self.start_x, self.start_y, self.end_x, self.end_y):
                self.top_left_x = min(self.start_x, self.end_x)
                self.top_left_y = min(self.start_y, self.end_y)
                self.bottom_right_x = max(self.start_x, self.end_x)
                self.bottom_right_y = max(self.start_y, self.end_y)

                if self.out_of_bounds():
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

        if self.valid_coordinates(self.start_x, self.start_y, self.end_x, self.end_y):
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
        if os.path.isfile(os.path.join(self.base_output_dir, "eu_2_annotation.json")):
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{self.base_output_dir}"')
            else:  # Linux
                subprocess.Popen(["xdg-open", self.base_output_dir])
            self.info_label.setText("Folder opened!")
        else:
             self.info_label.setText("annotation_2d.json not found!")


    def not_a_sign(self):
        self.directory_check()
        if os.path.isfile(os.path.join(self.base_output_dir, "eu_2_annotation.json")):
            with open(os.path.join(self.base_output_dir, "eu_2_annotation.json"), "r") as f:
                    self.annotation_2d_dict = json.load(f)

            annotation_entry = {
                "image_name": os.path.basename(self.full_current_file_name),
                "label": None,
                "x1": None,
                "y1": None,
                "x2": None,
                "y2": None
            }
            self.saved_check_label.setText("Saved")
            # Find if the image annotation already exists
            found = False
            for entry in self.annotation_2d_dict:
                if entry["image_name"] == annotation_entry["image_name"]:
                    # Update existing entry
                    entry.update(annotation_entry)
                    found = True
                    break

            if not found:
                # If the entry doesn't exist, append the new annotation entry
                self.annotation_2d_dict.append(annotation_entry)

            with open(os.path.join(self.base_output_dir, "eu_2_annotation.json"), "w") as f:
                json.dump(self.annotation_2d_dict, f, indent=4)

            self.info_label.setText("Not a sign saved")
            self.coords_label.setText("Null/Null, Null/Null")
        else:
            self.annotation_2d_dict = []
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
        num, ok = QInputDialog.getInt(self, "Input Image Number", "Enter image number:") #check if input number correct

        if ok:
            # Create the image file path based on the entered number
            if 0 < num < len(self.file_list)+1:
                self.file_index = int(num)-1
                self.load_image_and_set_name()
                self.clear_coords()
            else:
                self.info_label.setText("Incorrect image number!")

    def get_filenames(self):
        return [os.path.basename(file) for file in self.file_list] #get only filename not path

    def checking(self):
        if self.directory_check():

            first = True
            set_index = 0
            first_index = 0
            filenames = self.get_filenames()
            not_found_text = ""
            print(len(filenames))
            for filename in filenames:
                if not self.image_name_exists(self.annotation_2d_dict, filename): #if true that means no annotation saved
                    not_found_text += f"File name: {filename}, Index:{set_index}\n"
                    if first: #to jump to first found image
                        self.load_image_and_set_name()
                        first = False
                        first_index = self.file_index # save first found image index
                set_index += 1
            self.file_index = first_index # to be able to use next image correctly

            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Checker")
            msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #2e2e2e;  /* Dark background */
                    }
                    QLabel {
                        color: white;  /* White text for labels */
                    }
                    QPushButton {
                        background-color: #555555;  /* Darker buttons */
                        color: white;  /* White text for buttons */
                    }
                """)
            list_len = len(not_found_text.strip().split("\n"))
            if not_found_text == "":
                msg.setText("All files in this directory has annotation")
            elif list_len > 30:
                msg.setText("List of files:\n" + "\n".join(not_found_text.strip().split("\n")[:30]) + f"\n... and {list_len - 30} more")
            else:
                msg.setText("List of files:\n" + "\n".join(not_found_text.strip().split("\n")[:30]))

            msg.exec_()
        else:
            self.info_label.setText("Directory not opened!")

    #def image_name_exists(self, annotation_list, filename):
    #    for annotation in annotation_list:
    #        if annotation["image_name"] == filename:
    #           return True
    #    return False

    @staticmethod
    def valid_coordinates(a, b, c, d):
        return a is not None and b is not None and c is not None and d is not None

    def out_of_bounds(self):
        return (self.top_left_x < 0 or self.top_left_x > self.pixmap.width() or # check if top left point is in the pixmap
                self.top_left_y < 0 or self.top_left_y > self.pixmap.height() or
                self.bottom_right_x < 0 or self.bottom_right_x > self.pixmap.width() or # check if bottom right point is in the pixmap
                self.bottom_right_y < 0 or self.bottom_right_y > self.pixmap.height())

    def menu_item_selected(self):
        # Get the action that was triggered
        selected_action = self.sender()
        selected_text = selected_action.text()
        self.current_label = selected_text
        # Get the text of the selected menu item

        # Set the button text to the selected label
        self.button.setText(selected_text)

    def search_annotation_by_image_name(self, annotations, image_name):
        for entry in annotations:
            if entry["image_name"] == image_name:
                return entry  # Return the matching dictionary
        return None  # Return None if not found

    def closeEvent(self, event):
        # Path to the annotation file
        file_path = os.path.join(self.base_output_dir, "last_index.json")

        # Load the existing JSON file (if it exists)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    index_data = json.load(f)  # Load existing data
                    # Ensure the loaded data is a dictionary, not a list
                    if not isinstance(index_data, dict):
                        index_data = {}  # If it's a list or other type, initialize as an empty dictionary
                except json.JSONDecodeError:
                    index_data = {}  # If file is empty or corrupted, initialize as an empty dictionary
        else:
            index_data = {}  # If file does not exist, start fresh

        # Update or add the 'last_image_index'
        index_data["last_image_index"] = self.file_index  # Assuming self.file_index holds the current index

        # Write the updated data back to the JSON file
        with open(file_path, "w") as f:
            json.dump(index_data, f, indent=4)

        # Optionally call the default close event behavior
        super().closeEvent(event)

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



