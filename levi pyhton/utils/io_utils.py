import os
import json
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush


def select_input_dir(widget):
    widget.input_dir = str(QtWidgets.QFileDialog.getExistingDirectory(widget, "Select Input Directory"))

    widget.file_list = list()
    try:
        for f in os.listdir(widget.input_dir):
            fpath = os.path.join(widget.input_dir, f)
            if os.path.isfile(fpath) and f.endswith(('.png', '.jpg', '.jpeg')):
                widget.file_list.append(fpath)
        widget.info_label.setText("Input folder loaded!")
    except FileNotFoundError:
        print("Input folder not found ({})".format(widget.input_dir))
        return

    widget.file_list.sort()
    widget.file_index = 0
    widget.load_image_and_set_name()
    widget.first = False


def select_output_dir(widget):
    widget.base_output_dir = str(QtWidgets.QFileDialog.getExistingDirectory(widget, "Select Output Directory"))

    if widget.directory_check():
        last_index_file = os.path.join(widget.base_output_dir, "last_index.json")

        if os.path.isfile(last_index_file):
            with open(last_index_file, "r") as stream:
                try:
                    widget.state = json.load(stream)
                    # Ensure widget.state is a dictionary, not a list or string
                    if isinstance(widget.state, dict):
                        # Check if "last_image_index" exists and load it
                        if "last_image_index" in widget.state:
                            widget.file_index = widget.state["last_image_index"]
                        else:
                            widget.info_label.setText("last_image_index key not found in the JSON file.")
                    else:
                        widget.info_label.setText("Unexpected data structure in the last_index.json file.")
                except json.JSONDecodeError:
                    widget.info_label.setText("Error loading last_index.json, possibly corrupt.")
        else:
            widget.info_label.setText("No last_index.json file found.")
        widget.load_image_and_set_name()
    else:
        widget.info_label.setText("No input or output directory")


def load_2d_annot(widget):
    if widget.directory_check():
        if os.path.isfile(os.path.join(widget.base_output_dir, widget.annotation_filename)):
            with (open(os.path.join(widget.base_output_dir, widget.annotation_filename), "r")) as stream:
                widget.annotation_2d_dict = json.load(stream)
                entry = widget.search_annotation_by_image_name(widget.annotation_2d_dict, widget.full_current_file_name)

                if entry is not None:
                    if all([entry["x1"] is not None, entry["y1"] is not None, entry["x2"] is not None,
                            entry["y2"] is not None]):
                        widget.saved_check_label.setText("Saved")
                        x1 = math.floor(entry["x1"] / widget.x_back_scale)
                        y1 = math.floor(entry["y1"] / widget.y_back_scale)
                        x2 = math.floor(entry["x2"] / widget.x_back_scale)
                        y2 = math.floor(entry["y2"] / widget.y_back_scale)
                        widget.last_left_x = x1
                        widget.last_left_y = y1
                        widget.last_right_x = x2
                        widget.last_right_y = y2

                        widget.top_left_x = x1
                        widget.top_left_y = y1
                        widget.bottom_right_x = x2
                        widget.bottom_right_y = y2
                        if entry["label"] == "unknown":
                            widget.current_label = "unknown_sign"
                            widget.button.setText("unknown_sign")
                        else:
                            for action in widget.menu.actions():
                                if action.text() == entry["label"]:
                                    widget.current_label = entry["label"]
                                    widget.button.setText(entry["label"])

                        temp_pixmap = widget.pixmap.copy()
                        painter = QPainter(temp_pixmap)
                        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                        painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                        painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                        painter.end()
                        widget.image.setPixmap(temp_pixmap)
                        widget.info_label.setText("Box loaded!")

                    else:
                        widget.info_label.setText("save as Not a sign")
                        widget.saved_check_label.setText("Saved")
                else:
                    widget.saved_check_label.setText("Not saved")
                    if widget.last_left_x is not None and widget.last_left_y is not None and widget.last_right_x is not None and widget.last_right_y is not None:
                        # draw previous box
                        temp_pixmap = widget.pixmap.copy()
                        painter = QPainter(temp_pixmap)
                        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                        painter.setBrush(QBrush(Qt.blue, Qt.NoBrush))

                        painter.drawRect(
                            QRect(widget.last_left_x, widget.last_left_y, widget.last_right_x - widget.last_left_x,
                                  widget.last_right_y - widget.last_left_y))
                        painter.end()
                        widget.image.setPixmap(temp_pixmap)

                        widget.top_left_x = widget.last_left_x
                        widget.top_left_y = widget.last_left_y
                        widget.bottom_right_x = widget.last_right_x
                        widget.bottom_right_y = widget.last_right_y
                widget.coords_label.setText(
                    "Coordinates: ({}, {}), ({}, {})".format(widget.last_left_x, widget.last_left_y,
                                                             widget.last_right_x, widget.last_right_y))

        else:
            widget.info_label.setText("No annotation_2d.json found or no output directory!")
            widget.annotation_2d_dict = dict()
    else:
        widget.info_label.setText("In or output directory not found!")


def save_2d(widget):
    if widget.directory_check():
        if widget.annotation_2d_dict is None:
            widget.load_2d_annot()

        if widget.valid_coordinates(widget.top_left_x, widget.top_left_y, widget.bottom_right_x, widget.bottom_right_y):
            annotation_entry = {
                "image_name": os.path.basename(widget.full_current_file_name),
                "label": widget.current_label,
                "x1": widget.top_left_x * widget.x_back_scale,
                "y1": widget.top_left_y * widget.y_back_scale,
                "x2": widget.bottom_right_x * widget.x_back_scale,
                "y2": widget.bottom_right_y * widget.y_back_scale
            }

            widget.last_left_x = widget.top_left_x
            widget.last_left_y = widget.top_left_y
            widget.last_right_x = widget.bottom_right_x
            widget.last_right_y = widget.bottom_right_y

            widget.saved_check_label.setText("Saved")
            # Load existing annotations if any
            annotation_file_path = os.path.join(widget.base_output_dir, widget.annotation_filename)

            if os.path.exists(annotation_file_path):
                with open(annotation_file_path, "r") as f:
                    widget.annotation_2d_dict = json.load(f)
            else:
                widget.annotation_2d_dict = list()

            # Find if the image annotation already exists
            found = False

            for entry in widget.annotation_2d_dict:
                if entry["image_name"] == annotation_entry["image_name"]:
                    # Update existing entry
                    entry.update(annotation_entry)
                    found = True
                    break

            if not found:
                # If the entry doesn't exist, append the new annotation entry
                widget.annotation_2d_dict.append(annotation_entry)

            # Save back the updated annotations
            with open(annotation_file_path, "w") as f:
                json.dump(widget.annotation_2d_dict, f, indent=4)

            widget.info_label.setText("Coordinates have been saved!")
        else:
            widget.info_label.setText("2d annotation can not be saved!")
    else:
        widget.info_label.setText("In or output directory not found!")


def load_image_and_set_name(widget):
    if widget.file_list:
        filename = widget.file_list[widget.file_index % len(widget.file_list)]
        widget.pixmap = QtGui.QPixmap(filename)
        ori_width, ori_height = widget.pixmap.width(), widget.pixmap.height()
        if widget.pixmap.isNull():
            # the file is not a valid image, remove it from the list
            # and try to load the next one
            print("file is removed from the list because it is not valid ({})".format(filename))
            widget.file_list.remove(filename)
            widget.load_image_and_set_name()
        else:
            widget.pixmap = widget.pixmap.scaled(widget.image.size(), QtCore.Qt.KeepAspectRatio)
            current_width, current_height = widget.pixmap.width(), widget.pixmap.height()
            widget.x_back_scale = ori_width / current_width
            widget.y_back_scale = ori_height / current_height
            widget.image.setPixmap(widget.pixmap)
            widget.full_current_file_name = os.path.basename(filename)
            widget.current_file_name = filename.split('_')[-1]

            widget.setWindowTitle(os.path.basename(widget.full_current_file_name))

            widget.current_batch_index = widget.full_current_file_name.split('_')[0]

            # Index of the first underscore
            first_underscore_idx = os.path.basename(widget.full_current_file_name).find('_')
            # Index of the last underscore
            last_underscore_idx = os.path.basename(widget.full_current_file_name).rfind('_')

            if widget.current_batch_index != widget.last_batch_index:
                if first_underscore_idx != -1 and last_underscore_idx != -1 and first_underscore_idx < last_underscore_idx:
                    # Predicted label is between the first and last underscore
                    predicted_label = os.path.basename(widget.full_current_file_name)[
                                      first_underscore_idx + 1:last_underscore_idx]
                    found_label = False
                    for action in widget.menu.actions():
                        if predicted_label == action.text():
                            widget.current_label = predicted_label
                            widget.button.setText(predicted_label)
                            found_label = True
                    if not found_label:
                        widget.current_label = "unknown_sign"
                        widget.button.setText("unknown_sign")
            else:
                widget.current_label = widget.last_label

            widget.load_2d_annot()
            widget.update_image_info_label()
            # widget.pred_annot.setText(widget.get_label(os.path.basename(widget.current_file_name)))