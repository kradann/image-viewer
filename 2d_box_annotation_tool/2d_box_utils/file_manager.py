import os
import json

from collections import defaultdict
from PyQt5 import QtWidgets
#from 2d_box_utils.index_manager import IndexManager
from utils.annotation_manager import AnnotationManager





class FileManager(object):
    def __init__(self, widget, annotation_manager: AnnotationManager):
        self.widget = widget
        self.annotation_manager = annotation_manager
        self.input_dir = None
        self.output_dir = None
        self.last_index_file = None
        self.last_image_index = None

        self.file_list = list()
        self.batch_dict = defaultdict(list)

        self.current_label = None
        self.last_label = None

    @property
    def input_dir(self):
        if self.__input_dir is None:
            self.set_input_dir()
        return self.__input_dir

    @input_dir.setter
    def input_dir(self, input_dir):
        self.__input_dir = input_dir

    @property
    def output_dir(self):
        if self.__output_dir is None:
            self.set_output_dir()
        return self.__output_dir

    @output_dir.setter
    def output_dir(self, output_dir):
        self.__output_dir = output_dir

    def set_current_file(self, file_index: int):
        reset = False
        if self.input_dir is None:
            self.set_input_dir()
            reset = True
            file_index = 0

        if self.output_dir is None:
            self.set_output_dir()

        file_path = self.file_list[file_index % len(self.file_list)]
        full_current_file_name = os.path.basename(file_path)
        self.widget.setWindowTitle(os.path.basename(full_current_file_name))
        return file_path, reset

    def remove_file_from_list(self, file_path):
        if file_path in self.file_list:
            self.file_list.remove(file_path)
        else:
            print("file path ({}) is not in the list".format(file_path))

    def set_input_dir(self):
        input_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self.widget, "Select Input Directory"))
        if input_dir == "":
            return
        # input_dir = "/home/ad.adasworks.com/levente.peto/projects/traffic_sign_classification/annotation_check/rikardo_check"
        self.input_dir = input_dir
        self.file_list = list()
        try:
            for f in os.listdir(self.input_dir):
                fpath = os.path.join(self.input_dir, f)
                if os.path.isfile(fpath) and f.endswith(('.png', '.jpg', '.jpeg')):
                    self.file_list.append(fpath)
            # TODO: widget.info_label.setText("Input folder loaded!")
            print("input folder is set: {}".format(self.input_dir))
        except FileNotFoundError:
            print("Input folder not found ({})".format(input_dir))
            return

        self.file_list.sort()

        if self.widget.use_batch_idx:
            # collect batches
            for file_path in self.file_list:
                file_name = os.path.basename(file_path)
                batch_index = file_name.split('_')[0]
                self.batch_dict[batch_index].append(file_name)

    def set_output_dir(self):
        output_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self.widget, "Select Output Directory"))
        if output_dir == "":
            return
        # output_dir = "/home/ad.adasworks.com/levente.peto/projects/traffic_sign_classification/annotation_check/rikardo_check"
        self.annotation_manager.search_for_annotation(output_dir)
        self.output_dir = output_dir
        self.last_index_file = os.path.join(self.output_dir, "last_index.json")

        if os.path.isfile(self.last_index_file):
            try:
                with open(self.last_index_file, "r") as stream:
                    last_index_dict = json.load(stream)
            except json.JSONDecodeError:
                print("Error loading last_index.json, possibly corrupt.")
                # TODO: widget.info_label.setText("Error loading last_index.json, possibly corrupt.")

            # Ensure last_index_dict is a dictionary, not a list or string
            if isinstance(last_index_dict, dict):
                # Check if "last_image_index" exists and load it
                if "last_image_index" in last_index_dict:
                    self.last_image_index = last_index_dict["last_image_index"]
                    self.widget.index_manager.file_index = self.last_image_index - 1
                    print("last_image_index is loaded: {}".format(self.last_image_index))
                else:
                    print("last_image_index key not found in the JSON file.")
                    # TODO: widget.info_label.setText("last_image_index key not found in the JSON file.")
            else:
                print("last_image_index key not found in the JSON file.")
                # TODO: widget.info_label.setText("Unexpected data structure in the last_index.json file.")

        else:
            print("last_index JSON file does not exist yet")
            # TODO: widget.info_label.setText("No last_index.json file found.")

    def checking(self):
        if self.annotation_manager.annotation_dict is not None:
            #print(self.annotation_manager.annotation_list)
            #first = True
            set_index = 0
            #first_index = 0

            not_found_text = ""
            #print(len(self.file_list))
            for filename in self.file_list:
                    filename_in_annotation = self.annotation_manager.get_annotation_by_image_name(filename.split("/")[-1])
                    if not filename_in_annotation:  # if true that means no annotation saved
                        not_found_text += f"File name: {filename}, Index:{set_index + 1}\n"
                    set_index += 1

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
            elif list_len > 20:
                msg.setText("List of files:\n" + "\n".join(
                    not_found_text.strip().split("\n")[:20]) + f"\n... and {list_len - 20} more")
            else:
                msg.setText("List of files:\n" + "\n".join(not_found_text.strip().split("\n")[:20]))

            msg.exec_()
