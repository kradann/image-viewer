#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QShortcut, QInputDialog, QMenu, QAction
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush

from utils.image_manager import get_image_coordinates, mouse_press_event, mouse_move_event, mouse_release_event, \
    ImageManager
from utils.file_manager import FileManager
from utils.utils import close_event, get_dark_palette, search_annotation_by_image_name, get_filenames, \
    valid_coordinates, out_of_bounds
from utils.io_utils import load_image_and_set_name, select_input_dir, select_output_dir, save_2d, directory_check
from utils.dir_utils import move_file, open_annotation_dir
from utils.sing_types import eu_sign_types, us_sign_types

sign_types = None


class AnnotationTool(QtWidgets.QWidget):
    def __init__(self, us, use_batch_idx):
        QtWidgets.QWidget.__init__(self)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(10)
        self.setPalette(get_dark_palette())  # set dark theme

        self.us = us
        self.use_batch_idx = use_batch_idx
        num_of_columns = 3

        self.file_manager = FileManager(self)
        self.image_manager = ImageManager(self, self.file_manager)
        layout.addWidget(self.image_manager.image, 0, 0, 1, 3)

        # the label alignment property is always maintained even when the contents
        # change, so there is no need to set it each time
        self.image_manager.image.setAlignment(QtCore.Qt.AlignCenter)

        # # draw rectangle
        # self.start_x = None
        # self.start_y = None
        # self.end_x = None
        # self.end_y = None

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
        self.saved_check_label.setStyleSheet(
            "font-size: 18px; color: white;")  # Set font size to 18px and color to white
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
        layout.addWidget(self.nextImageButton, 4, 2, 4, 1)

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
        self.nextImageButton.setFixedHeight(button_size * 4)
        layout.addWidget(self.checker, 8, 2, 1, 1)

        self.inputFolderButton.clicked.connect(partial(select_input_dir, self))
        self.outputFolderButton.clicked.connect(select_output_dir)
        self.prevImageButton.clicked.connect(self.prev_image)
        self.nextImageButton.clicked.connect(self.next_image)
        self.save2dButton.clicked.connect(save_2d)
        self.AnnotdirButton.clicked.connect(open_annotation_dir)
        self.JumpTo.clicked.connect(self.jump_to)
        self.checker.clicked.connect(self.checking)

        self.moveImageButton.clicked.connect(self.move_func_dict["something_wrong"])
        self.NasButton.clicked.connect(self.not_a_sign)
        self.UsButton.clicked.connect(self.move_func_dict["new_unknown_sign"])
        self.TdButton.clicked.connect(self.move_func_dict["to_delete"])
        self.OkButton.clicked.connect(self.move_func_dict["new_ok"])

        # Dropdown button and combobox
        """self.combobox = QComboBox(self)
        self.combobox.addItems(sign_types)"""

        self.button = QPushButton("No input file", self)

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

        # self.AnnotdirButton.clicked.connect(partial(self.get_joker_move_funk, self.combobox))
        # self.Joker2Button.clicked.connect(partial(self.get_joker_move_funk, self.combobox2))

        # into file manager
        # self.dirIterator = None
        # self.file_index = 0
        # self.file_list = list()
        # self.current_file_name = None
        # self.input_dir = None
        # self.base_output_dir = None

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
        self.annotation_filename = "annotation.json"

        self.shortcut_save = QShortcut(QKeySequence("S"), self)
        self.shortcut_save.activated.connect(save_2d)

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


    def next_image(self):
        # ensure that the file list has not been cleared due to missing files
        if self.file_list:
            self.first = True
            self.file_index += 1
            self.last_batch_index = self.full_current_file_name.split('_')[0]
            self.last_image = search_annotation_by_image_name(self.annotation_2d_dict, self.full_current_file_name)
            if self.last_image is not None:
                self.last_label = self.last_image["label"]

            load_image_and_set_name(self)
        else:
            self.info_label.setText("No directory loaded!")

    def prev_image(self):
        # ensure that the file list has not been cleared due to missing files
        if self.file_list:
            self.first = True
            self.file_index -= 1
            self.last_batch_index = self.full_current_file_name.split('_')[0]
            load_image_and_set_name(self)
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
                select_output_dir(self)

            if self.base_output_dir is not None:
                move_file(self, file_name)
            else:
                print("first select output dir")
        return move_func

    def get_joker_move_funk(self, combobox):
        joker_move_funk = self.get_move_func("new_" + combobox.currentText())
        joker_move_funk()


    def not_a_sign(self):
        directory_check(self)
        if os.path.isfile(os.path.join(self.base_output_dir, self.annotation_filename)):
            with open(os.path.join(self.base_output_dir, self.annotation_filename), "r") as f:
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

            with open(os.path.join(self.base_output_dir, self.annotation_filename), "w") as f:
                json.dump(self.annotation_2d_dict, f, indent=4)

            self.info_label.setText("Not a sign saved")
            self.coords_label.setText("Null/Null, Null/Null")
        else:
            self.annotation_2d_dict = list()
            self.info_label.setText("annotation_2d.json not found!")


    def jump_to(self):
        directory_check(self)
        # check if input number correct
        num, ok = QInputDialog.getInt(self, "Input Image Number", "Enter image number:")
        if ok:
            # Create the image file path based on the entered number
            if 0 < num < len(self.file_list) + 1:
                self.file_index = int(num) - 1
                load_image_and_set_name(self)
                self.clear_coords()
            else:
                self.info_label.setText("Incorrect image number!")


    def checking(self):
        if directory_check(self):
            first = True
            set_index = 0
            first_index = 0
            filenames = get_filenames(self)
            not_found_text = ""
            print(len(filenames))
            for filename in filenames:
                current_file = search_annotation_by_image_name(self.annotation_2d_dict, filename)
                if current_file is None:  # if true that means no annotation saved
                    not_found_text += f"File name: {filename}, Index:{set_index + 1}\n"
                    if first:  # to jump to first found image
                        load_image_and_set_name(self)
                        first = False
                        first_index = self.file_index  # save first found image index
                set_index += 1
            self.file_index = first_index  # to be able to use next image correctly

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
                msg.setText("List of files:\n" + "\n".join(
                    not_found_text.strip().split("\n")[:30]) + f"\n... and {list_len - 30} more")
            else:
                msg.setText("List of files:\n" + "\n".join(not_found_text.strip().split("\n")[:30]))

            msg.exec_()
        else:
            self.info_label.setText("Directory not opened!")


    def menu_item_selected(self):
        # Get the action that was triggered
        selected_action = self.sender()
        selected_text = selected_action.text()
        self.current_label = selected_text
        # Set the button text to the selected label
        self.button.setText(selected_text)


    def mousePressEvent(self, event):
        mouse_press_event(self, event)


    def mouseMoveEvent(self, event):
        mouse_move_event(self, event)


    def mouseReleaseEvent(self, event):
        mouse_release_event(self, event)


    def closeEvent(self, event):
        # Optionally call the default close event behavior
        super().closeEvent(event)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--us", default=False, action="store_true", help="Use US signs instead of EU")
    parser.add_argument("--use_batch_idx", default=False, action="store_true", help="Use batch index to speed up annotation")
    args = parser.parse_args()
    sign_types = us_sign_types if args.us else eu_sign_types

    app = QtWidgets.QApplication(sys.argv)
    annotation_tool = AnnotationTool(args.us, args.use_batch_idx)
    # width = imageLoader.frameGeometry().width()
    # height = imageLoader.frameGeometry().height()

    annotation_tool.setFixedSize(600, 800)
    annotation_tool.show()
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
