import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


def valid_coordinates(a, b, c, d):
    return a is not None and b is not None and c is not None and d is not None


def out_of_bounds(widget):
    return (
                widget.top_left_x < 0 or widget.top_left_x > widget.pixmap.width() or  # check if top left point is in the pixmap
                widget.top_left_y < 0 or widget.top_left_y > widget.pixmap.height() or
                widget.bottom_right_x < 0 or widget.bottom_right_x > widget.pixmap.width() or  # check if bottom right point is in the pixmap
                widget.bottom_right_y < 0 or widget.bottom_right_y > widget.pixmap.height())


def update_image_info_label(widget):
    print("uiil")
    if (widget.file_index % len(widget.file_list) == 0) and not widget.first:
        widget.info_label.setText("{} Images loaded!".format(len(widget.file_list)))
    elif widget.file_index % len(widget.file_list) == 0 and widget.first:
        widget.info_label.setText("Image (1/{}) loaded!".format(len(widget.file_list)))
    else:
        widget.info_label.setText(
            "Image ({}/{}) loaded!".format(widget.file_index % len(widget.file_list) + 1, len(widget.file_list)))


def get_filenames(widget):
    return [os.path.basename(file) for file in widget.file_list]  # get only filename not path


def close_event(widget):
    file_path = os.path.join(widget.base_output_dir, "last_index.json")

    # Load the existing JSON file (if it exists)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                index_data = json.load(f)  # Load existing data
                # Ensure the loaded data is a dictionary, not a list
                if not isinstance(index_data, dict):
                    index_data = dict()  # If it's a list or other type, initialize as an empty dictionary
            except json.JSONDecodeError:
                index_data = dict()  # If file is empty or corrupted, initialize as an empty dictionary
    else:
        index_data = dict()  # If file does not exist, start fresh

    # Update or add the 'last_image_index'
    # Assuming widget.file_index holds the current index
    index_data["last_image_index"] = len(widget.annotation_2d_dict)

    # Write the updated data back to the JSON file
    with open(file_path, "w") as f:
        json.dump(index_data, f, indent=4)


def get_dark_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 48))  # Background color
    palette.setColor(QPalette.WindowText, Qt.white)  # Text color

    # palette.setColor(QPalette.Button, QColor(60,70,80)) #Button color
    palette.setColor(QPalette.ButtonText, Qt.black)  # Buttontext color
    return palette
