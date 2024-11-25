#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLabel, QComboBox, QPushButton, QShortcut, QInputDialog, QMenu, QAction
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

from utils.annotation_manager import AnnotationManager
from utils.image_manager import ImageManager
from utils.file_manager import FileManager
from utils.index_manager import IndexManager
from utils.utils import get_dark_palette, get_filenames
from utils.io_utils import load_image_and_set_name, save_2d, directory_check
from utils.dir_utils import move_file, open_annotation_dir
from utils.sing_types import eu_sign_types, us_sign_types


class AnnotationTool(QtWidgets.QWidget):
    def __init__(self, us, use_batch_idx):
        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(10)
        self.setPalette(get_dark_palette())  # set dark theme
        self.sign_types = us_sign_types if args.us else eu_sign_types

        self.us = us
        self.use_batch_idx = use_batch_idx
        num_of_columns = 3

        self.annotation_manager = AnnotationManager()
        self.file_manager = FileManager(self, self.annotation_manager)
        self.image_manager = ImageManager(self, self.file_manager)
        self.layout.addWidget(self.image_manager.image, 0, 0, 1, 3)

        self.index_manager = IndexManager(self.file_manager, self.image_manager, self.annotation_manager)
        self.image_manager.image.setAlignment(QtCore.Qt.AlignCenter)

        self.coords_label = QLabel(self)
        self.coords_label.setText("Coordinates: (N/A, N/A)")
        self.coords_label.setStyleSheet("color: red")
        self.coords_label.setFixedSize(500, 60)
        self.layout.addWidget(self.coords_label, 2, 0, 1, num_of_columns)

        self.info_label = QLabel(self)
        self.info_label.setText("Welcome!")
        self.layout.addWidget(self.info_label, 2, 2, 1, num_of_columns)
        # self.info_label.setAlignment(Qt.AlignRight)

        self.label_label = QLabel(self)
        self.label_label.setText("----------")
        self.label_label.setStyleSheet("font-size: 18px; color: red;")
        self.layout.addWidget(self.label_label, 2, 0, 2, num_of_columns)

        self.index_label = QLabel(self)
        self.index_label.setText("----------")
        self.index_label.setStyleSheet("font-size: 18px; color: white;")
        self.layout.addWidget(self.index_label, 2, 2, 2, num_of_columns)
        # self.index_label.setAlignment(Qt.AlignRight)

        # self.move_func_dict = {
        #     "something_wrong": self.get_move_func("something_wrong"),
        #     "to_delete": self.get_move_func("to_delete"),
        #     "new_ok": self.get_move_func("new_ok"),
        #     "new_not_a_sign": self.get_move_func("new_not_a_sign"),
        #     "new_unknown_sign": self.get_move_func("new_unknown_sign"),
        # }

        button_row_offset = 3
        button_size = 40
        self.add_button("Change Input Folder", button_size, (button_row_offset, 0), self.file_manager.set_input_dir)
        self.add_button("Change Output Folder", button_size, (button_row_offset, 1), self.file_manager.set_output_dir)
        self.add_button("Save coords (s)", button_size, (button_row_offset, 2), self.index_manager.save_annotation, "S")
        # self.add_button("Jump to", button_size, (button_row_offset + 1, 0), self.jump_to)
        self.add_button("Previous image (<-)", button_size, (button_row_offset + 1, 1),
                        self.index_manager.previous_file, "Left")
        self.add_button("Next image (->)", button_size, (button_row_offset + 1, 2), self.index_manager.next_file,
                        "Right")
        # self.add_button("To delete (d)", button_size, (button_row_offset + 2, 0), self.file_manager.set_input_dir, "D")
        self.add_button("Not a sign (n)", button_size, (button_row_offset + 1, 0), self.index_manager.set_not_a_sign, "N")
        # self.add_button("Open annotation directory", button_size, (button_row_offset + 2, 2), open_annotation_dir)

        self.button = QPushButton("No input file", self)

        self.menu = QMenu(self)
        for i in self.sign_types:
            action = QAction(i, self)
            action.triggered.connect(self.menu_item_selected)  # Connect to selection handler
            self.menu.addAction(action)
        self.button.setMenu(self.menu)
        self.button.setFixedHeight(button_size)
        self.layout.addWidget(self.button, button_row_offset + 2, 0, 1, 3)

    def add_button(self, name: str, size: int, layout: tuple, func, shortcut: str = None):
        button = QtWidgets.QPushButton(name)
        button.setFixedHeight(size)
        self.layout.addWidget(button, *layout)
        button.clicked.connect(func)

        q_shortcut = None
        if shortcut is not None:
            q_shortcut = QShortcut(QKeySequence(shortcut), self)
            q_shortcut.activated.connect(func)
        return button, q_shortcut

    def set_coords_label(self, tl_x, tl_y, br_x, br_y, color="white", added_test=""):
        self.coords_label.setText("Coordinates: ({}, {}), ({}, {}){}".format(tl_x, tl_y, br_x, br_y, added_test))
        self.coords_label.setStyleSheet("color: {}".format(color))

    def set_label_label(self, label, color="white", added_test=""):
        self.label_label.setText("Label: {}{}".format(label, added_test))
        self.label_label.setStyleSheet("color: {}".format(color))

    def set_info_label(self, text, color="white"):
        self.info_label.setText(text)
        self.info_label.setStyleSheet("color: {}".format(color))

    def set_index_label(self, idx, color="white"):
        self.index_label.setText("idx: {}".format(idx))
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

    def jump_to(self):
        print("out of order")
        return
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
        print("out of order")
        return
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
        if selected_text == "not_a_sign":
            self.index_manager.set_not_a_sign()
        else:
            self.index_manager.set_current_label(selected_text)
        # Set the button text to the selected label
        self.button.setText(selected_text)
        self.set_label_label(selected_text)

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
    args = parser.parse_args()

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
