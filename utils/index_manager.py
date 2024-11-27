import math
import os
import json
from pprint import pprint

from PyQt5.QtCore import Qt
from utils.annotation_manager import AnnotationManager
from utils.image_manager import ImageManager
from utils.file_manager import FileManager
from utils.io_utils import load_2d_annot


class IndexManager(object):
    def __init__(self,
                 file_manager: FileManager,
                 image_manager: ImageManager,
                 annotation_manager: AnnotationManager):
        self.file_manager = file_manager
        self.image_manager = image_manager
        self.annotation_manager = annotation_manager
        self.file_index = -1

        self.current_image_name = None
        self.current_batch_index = None
        self.old_label = None
        self.new_label = None
        self.not_a_sign = False
        self.batch_label_dict = dict()

    def next_file(self):
        # self.image_manager.clear_coords()
        self.image_manager.widget.set_previous_label(self.new_label)
        self.file_index += 1
        self.update(draw_previous=True)
        self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")

    def previous_file(self):
        # self.image_manager.clear_coords()
        self.file_index -= 1
        self.update()
        self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")

    def update(self, draw_previous=False):
        def set_old_label(old_label, text="", color="white"):
            self.old_label = old_label
            self.image_manager.widget.set_old_label_label(self.old_label, color if old_label is not None else "red")
            self.image_manager.widget.set_info_label(text, "white")

        def set_new_label(new_label, text="", color="white"):
            self.new_label = new_label
            self.image_manager.widget.set_new_label_label(self.new_label, color)
            self.image_manager.widget.set_info_label(text, "white")

        self.not_a_sign = False
        file_path, reset = self.file_manager.set_current_file(self.file_index)
        self.image_manager.load_image(file_path)
        self.current_image_name = os.path.basename(file_path)
        annotation_dict = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)
        print("loaded annotation dict:")
        pprint(annotation_dict)

        if annotation_dict is not None:
            set_old_label(annotation_dict["label"])
            set_new_label(annotation_dict["label"], "based on annotation", "yellow")
            self.image_manager.draw_rect_from_annotation(annotation_dict,
                                                         set_to_current=not self.image_manager.widget.use_batch_idx or self.image_manager.widget.fast_check,
                                                         color=Qt.cyan,
                                                         copy=False,
                                                         text=self.old_label if self.image_manager.widget.fast_check else None)
            # self.image_manager.widget.button.setText(self.old_label)
        else:
            self.image_manager.widget.set_info_label("no annotation", "red")

        if self.image_manager.widget.use_batch_idx:
            self.current_batch_index = self.batch_idx_by_filename()

            if self.current_batch_index in self.batch_label_dict:
                set_new_label(self.batch_label_dict[self.current_batch_index], "based on batch", "yellow")
                if self.new_label == "not_a_sign":
                    self.not_a_sign = True
                if draw_previous:
                    self.image_manager.draw_rect_from_annotation(None,
                                                                 set_to_current= not self.image_manager.widget.fast_check,
                                                                 color=Qt.yellow)
        if reset:
            self.file_index = 0

    def label_by_filename(self):
        # Index of the first underscore
        first_underscore_idx = os.path.basename(self.current_image_name).find('_')
        # Index of the last underscore
        last_underscore_idx = os.path.basename(self.current_image_name).rfind('_')
        # Predicted label is between the first and last underscore
        label = os.path.basename(self.current_image_name)[first_underscore_idx + 1:last_underscore_idx]
        return label

    def batch_idx_by_filename(self):
        batch_index = self.current_image_name.split('_')[0]
        return batch_index

    def set_new_label(self, label):
        self.not_a_sign = False
        self.new_label = label
        self.image_manager.widget.set_new_label_label(self.new_label, "yellow")

    def set_not_a_sign(self):
        self.not_a_sign = True
        self.new_label = "not_a_sign"
        self.image_manager.widget.set_coords_label(-1, -1, -1, -1, "yellow")
        self.image_manager.widget.set_new_label_label(self.new_label, "yellow")

    def save_annotation(self):
        if self.image_manager.top_left_x is None:
            annotation_dict = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)
            self.image_manager.draw_rect_from_annotation(annotation_dict, set_to_current=True, color=Qt.green)

        self.batch_label_dict[self.current_batch_index] = self.new_label
        if not self.not_a_sign:
            if all([self.current_image_name is not None,
                    self.new_label is not None,
                    self.image_manager.top_left_x is not None,
                    self.image_manager.top_left_y is not None,
                    self.image_manager.bottom_right_x is not None,
                    self.image_manager.bottom_right_y is not None,
                    self.image_manager.bottom_right_y is not None,
                    self.image_manager.y_back_scale is not None]):
                x1, y1, x2, y2 = self.image_manager.get_back_scaled_coords()
                annotation_dict = {
                    "image_name": self.current_image_name,
                    "label": self.new_label,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                }
                self.annotation_manager.add_annotation(annotation_dict)
                self.annotation_manager.save_annotation_list(self.file_manager.output_dir)
                self.image_manager.widget.set_coords_label(int(x1), int(y1), int(x2), int(y2), "green")
                self.image_manager.widget.set_new_label_label(self.new_label, "green")
                self.image_manager.widget.set_info_label("Saved", "green")
                self.image_manager.set_last_coords()
                self.image_manager.draw_rect_from_annotation(None, set_to_current=False, color=Qt.green)
            else:
                print("annotation can't be saved {}".format((self.current_image_name,
                                                             self.new_label,
                                                             self.image_manager.top_left_x,
                                                             self.image_manager.top_left_y,
                                                             self.image_manager.bottom_right_x,
                                                             self.image_manager.bottom_right_y,
                                                             self.image_manager.bottom_right_y,
                                                             self.image_manager.y_back_scale)))
        else:
            annotation_dict = {
                "image_name": self.current_image_name,
                "label": "not_a_sign",
                "x1": None,
                "y1": None,
                "x2": None,
                "y2": None
            }
            self.annotation_manager.add_annotation(annotation_dict)
            self.annotation_manager.save_annotation_list(self.file_manager.output_dir)
            self.image_manager.widget.set_coords_label(-1, -1, -1, -1, "green")
            self.image_manager.widget.set_new_label_label(self.new_label, "green")
            self.image_manager.widget.set_info_label("Saved", "green")
            self.image_manager.set_last_coords_to_none()

    def save_last_idx(self):
        if len(self.file_manager.file_list) > 0:
            index_data = {"last_image_index": self.file_index % len(self.file_manager.file_list)}
            # Write the updated data back to the JSON file
            with open(self.file_manager.last_index_file, "w") as f:
                json.dump(index_data, f, indent=4)

            print("last_image_index is saved: {}".format(index_data["last_image_index"]))
        else:
            print("last_image_index can not be saved")
