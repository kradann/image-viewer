#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
from typing import Union

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QShortcut, QInputDialog, QMenu, QAction
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

from utils.annotation_manager import AnnotationManager
from utils.image_manager import ImageManager
from utils.file_manager import FileManager
from utils.index_manager import IndexManager
from utils.utils import get_dark_palette, get_filenames
from utils.box_manager import BoxManager
from utils.io_utils import load_image_and_set_name, save_2d, directory_check
from utils.dir_utils import move_file, open_annotation_dir
from utils.sing_types import eu_sign_types, us_sign_types


class AnnotationTool(QtWidgets.QWidget):
    def __init__(self, us, use_batch_idx, fast_check):
        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(10)
        self.setPalette(get_dark_palette())  # set dark theme
        self.sign_types = us_sign_types if args.us else eu_sign_types

        self.us = us
        self.use_batch_idx = use_batch_idx
        self.fast_check = fast_check
        num_of_columns = 3

        self.box_manager = BoxManager(self)

        self.annotation_manager = AnnotationManager()
        self.file_manager = FileManager(self, self.annotation_manager)
        self.image_manager = ImageManager(self, self.file_manager, self.box_manager)
        self.layout.addWidget(self.image_manager.image, 0, 1, 1, 3)



        self.index_manager = IndexManager(self.file_manager, self.image_manager, self.annotation_manager, self.box_manager)
        self.image_manager.image.setAlignment(QtCore.Qt.AlignCenter)

        self.new_label_label = QLabel(self)
        self.new_label_label.setText("new label: ----------")
        self.new_label_label.setStyleSheet("font-size: 18px; color: red;")
        self.new_label_label.setFixedSize(500, 30)
        # self.new_label_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.new_label_label, 2, 0, 1, num_of_columns)

        self.info_label = QLabel(self)
        self.info_label.setText("Welcome!")
        # self.info_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.info_label, 2, 4, 1, num_of_columns)

        self.old_label_label = QLabel(self)
        self.old_label_label.setText("old label: ----------")
        self.old_label_label.setStyleSheet("font-size: 18px; color: red;")
        self.old_label_label.setFixedSize(500, 30)
        # self.old_label_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.old_label_label, 3, 0, 1, num_of_columns)

        self.coords_label = QLabel(self)
        self.coords_label.setText("Coordinates: (N/A, N/A)")
        self.coords_label.setStyleSheet("color: red")
        self.coords_label.setFixedSize(500, 30)
        # self.coords_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.coords_label, 4, 0, 1, num_of_columns)

        self.is_electric_label = QLabel(self)
        self.is_electric_label.setText("----------")
        self.is_electric_label.setStyleSheet("font-size: 18px; color: white;")
        self.layout.addWidget(self.is_electric_label, 3, 4, 1, num_of_columns)

        self.index_label = QLabel(self)
        self.index_label.setText("----------")
        self.index_label.setStyleSheet("font-size: 18px; color: white;")
        # self.index_label.setFixedSize(500, 60)
        # self.index_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.index_label, 4, 4, 1, num_of_columns)

        button_row_offset = 5
        button_size = 40
        self.add_button("Change Input Folder", button_size, (button_row_offset, 0), self.file_manager.set_input_dir)
        self.add_button("Change Output Folder", button_size, (button_row_offset, 1), self.file_manager.set_output_dir)
        self.add_button("Save (s)", button_size, (button_row_offset, 2), self.index_manager.save_annotation, "S")
        # self.add_button("Jump to", button_size, (button_row_offset + 1, 0), self.jump_to)
        self.add_button("Previous image (<-, a)", button_size, (button_row_offset + 1, 1),
                        self.index_manager.previous_file, ("Left", "A"))
        self.add_button("Next image (->, d)", button_size, (button_row_offset + 1, 2), self.index_manager.next_file,
                        ("Right", "D"))
        # self.add_button("To delete (d)", button_size, (button_row_offset + 2, 0), self.file_manager.set_input_dir, "D")
        self.add_button("Not a sign (n)", button_size, (button_row_offset + 1, 0), self.index_manager.set_not_a_sign,
                        "N")
        # self.add_button("Open annotation directory", button_size, (button_row_offset + 2, 2), open_annotation_dir)
        self.add_button("Previous label (w)", button_size, (button_row_offset + 2, 2), self.set_previous_label_to_new,
                        "W")

        self.add_button("Annotation check", button_size, ((button_row_offset + 2),3), self.file_manager.checking)

        self.add_button("Jump to", button_size, (button_row_offset + 2,4), self.index_manager.jump_to)

        self.add_button("<", button_size , (button_row_offset + 1,3), self.image_manager.previous_box)

        self.add_button(">", button_size , (button_row_offset + 1,4), self.image_manager.next_box)

        self.add_box = QPushButton(self)
        self.add_box.setText("Add box")
        self.add_box.setFixedHeight(button_size)
        self.layout.addWidget(self.add_box, button_row_offset, 3, 1, 2)
        self.add_box.clicked.connect(self.image_manager.add_box)

        self.button = QPushButton("No input file", self)
        self.button_text = "No input file"
        self.previous_label = "not_a_sign"

        self.menu = QMenu(self)
        for i in self.sign_types:
            action = QAction(i, self)
            action.triggered.connect(self.menu_item_selected)  # Connect to selection handler
            self.menu.addAction(action)
        self.button.setMenu(self.menu)
        self.button.setFixedHeight(button_size)
        self.layout.addWidget(self.button, button_row_offset + 2, 0, 1, 2)

    def set_previous_label(self, label):
        self.previous_label = label

    def set_previous_label_to_new(self):
        if self.previous_label == "not_a_sign":
            self.index_manager.set_not_a_sign()
        else:
            self.index_manager.set_new_label(self.previous_label)
        # Set the button text to the selected label
        self.set_new_label_label(self.previous_label, "yellow")

    def add_button(self, name: str, size: int, layout: tuple, func, shortcut: Union[str, tuple] = None):
        button = QtWidgets.QPushButton(name)
        button.setFixedHeight(size)
        self.layout.addWidget(button, *layout)
        button.clicked.connect(func)

        q_shortcut = None
        if shortcut is not None:
            if isinstance(shortcut, tuple):
                for s in shortcut:
                    q_shortcut = QShortcut(QKeySequence(s), self)
                    q_shortcut.activated.connect(func)
            else:
                q_shortcut = QShortcut(QKeySequence(shortcut), self)
                q_shortcut.activated.connect(func)
        return button, q_shortcut

    def set_coords_label(self, tl_x, tl_y, br_x, br_y, color="white", added_test=""):
        self.coords_label.setText("Coordinates: ({}, {}), ({}, {}){}".format(tl_x, tl_y, br_x, br_y, added_test))
        self.coords_label.setStyleSheet("color: {}".format(color))

    def set_old_label_label(self, label, color="white", added_test=""):
        self.old_label_label.setText("old label: {}{}".format(label, added_test))
        self.old_label_label.setStyleSheet("color: {}".format(color))

    def set_new_label_label(self, label, color="white", added_test=""):
        self.new_label_label.setText("new label: {}{}".format(label, added_test))
        self.new_label_label.setStyleSheet("color: {}".format(color))

    def set_info_label(self, text, color="white"):
        self.info_label.setText(text)
        self.info_label.setStyleSheet("color: {}".format(color))

    def set_index_label(self, idx, color="white"):
        self.index_label.setText("idx: {}/{}".format(idx, len(self.file_manager.file_list)))
        self.index_label.setStyleSheet("color: {}".format(color))

    # def get_move_func(self, file_name: str):
    #     def move_func():
    #         if self.base_output_dir is None:
    #             select_output_dir(self)
    #
    #         if self.base_output_dir is not None:
    #             move_file(self, file_name)
    #         else:
    #             print("first select output dir")
    #
    #     return move_func
    #
    # def get_joker_move_funk(self, combobox):
    #     joker_move_funk = self.get_move_func("new_" + combobox.currentText())
    #     joker_move_funk()
    #
    # def not_a_sign(self):
    #     directory_check(self)
    #     if os.path.isfile(os.path.join(self.base_output_dir, self.annotation_filename)):
    #         with open(os.path.join(self.base_output_dir, self.annotation_filename), "r") as f:
    #             self.annotation_2d_dict = json.load(f)
    #
    #         annotation_entry = {
    #             "image_name": os.path.basename(self.full_current_file_name),
    #             "label": None,
    #             "x1": None,
    #             "y1": None,
    #             "x2": None,
    #             "y2": None
    #         }
    #         self.saved_check_label.setText("Saved")
    #         # Find if the image annotation already exists
    #         found = False
    #         for entry in self.annotation_2d_dict:
    #             if entry["image_name"] == annotation_entry["image_name"]:
    #                 # Update existing entry
    #                 entry.update(annotation_entry)
    #                 found = True
    #                 break
    #
    #         if not found:
    #             # If the entry doesn't exist, append the new annotation entry
    #             self.annotation_2d_dict.append(annotation_entry)
    #
    #         with open(os.path.join(self.base_output_dir, self.annotation_filename), "w") as f:
    #             json.dump(self.annotation_2d_dict, f, indent=4)
    #
    #         self.info_label.setText("Not a sign saved")
    #         self.coords_label.setText("Null/Null, Null/Null")
    #     else:
    #         self.annotation_2d_dict = list()
    #         self.info_label.setText("annotation_2d.json not found!")


    def menu_item_selected(self):
        # Get the action that was triggered
        selected_action = self.sender()
        self.button_text = selected_action.text()

        if self.button_text == "not_a_sign":
            self.index_manager.set_not_a_sign()
        else:
            self.index_manager.set_new_label(self.button_text)
        # Set the button text to the selected label
        self.button.setText(self.button_text)
        self.set_new_label_label(self.button_text, "yellow")

    def mousePressEvent(self, event):
        self.image_manager.mouse_press_event(event)

    def mouseMoveEvent(self, event):
        self.image_manager.mouse_move_event(event)

    def mouseReleaseEvent(self, event):
        self.image_manager.mouse_release_event(event)

    def closeEvent(self, event):
        self.index_manager.save_last_idx()
        # Optionally call the default close event behavior
        super().closeEvent(event)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--us", default=False, action="store_true", help="Use US signs instead of EU")
    parser.add_argument("--use_batch_idx", default=False, action="store_true",
                        help="Use batch index to speed up annotation")
    parser.add_argument("--fast_check", default=False, action="store_true",
                        help="Print label on image")
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    annotation_tool = AnnotationTool(args.us, args.use_batch_idx, args.fast_check)
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
