import os
import platform
import shutil
import subprocess

from utils import update_image_info_label
from io_utils import select_output_dir, select_input_dir

def open_annotation_dir(widget):
    widget.directory_check()
    if os.path.isfile(os.path.join(widget.base_output_dir, widget.annotation_filename)):
        if platform.system() == "Windows":
            subprocess.Popen("explorer \"{}\"".format(widget.base_output_dir))
        else:  # Linux
            subprocess.Popen(["xdg-open", widget.base_output_dir])
        widget.info_label.setText("Folder opened!")
    else:
        widget.info_label.setText("{} not found!".format(widget.annotation_filename))


def move_file(widget, file_name: str):
    dst_dir = os.path.join(widget.base_output_dir, file_name)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, widget.full_current_file_name)
    try:
        print("dst path: {}".format(dst))
        shutil.copy2(os.path.join(widget.input_dir, widget.full_current_file_name), dst)  # Copy instead of move

        if file_name == "to_delete":
            original_file_path = os.path.join(widget.input_dir, widget.full_current_file_name)
            os.remove(original_file_path)
            print("Original file deleted from source: {}".format(original_file_path))
            widget.info_label.setText("Deleted!")
            update_image_info_label(widget)
        else:
            widget.info_label.setText("Copied!")
    except FileNotFoundError:
        print("Error during moving file: {}".format(dst))


def directory_check(widget):
    if widget.input_dir is None:
        select_input_dir(widget)
    if widget.base_output_dir is None:
        select_output_dir(widget)
    if widget.input_dir is not None and widget.base_output_dir is not None:
        return True
    else:
        return False