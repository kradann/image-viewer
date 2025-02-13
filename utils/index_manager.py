import math
import os
import json
from pprint import pprint

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QInputDialog

from utils.annotation_manager import AnnotationManager
from utils.image_manager import ImageManager
from utils.io_utils import directory_check , load_image_and_set_name
from utils.file_manager import FileManager
from utils.box_manager import BoxManager
from utils.box import Box

class IndexManager(object):
    def __init__(self,
                 file_manager: FileManager,
                 image_manager: ImageManager,
                 annotation_manager: AnnotationManager,
                 box_manager: BoxManager):
        self.file_manager = file_manager
        self.image_manager = image_manager
        self.annotation_manager = annotation_manager
        self.box_manager = box_manager
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
        self.image_manager.box_changed_update()
        self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")

    def previous_file(self):
        # self.image_manager.clear_coords()
        self.file_index -= 1
        self.update()
        self.image_manager.box_changed_update()
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
        self.current_image_name = os.path.basename(file_path)
        self.box_manager.coord_list = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)

        self.image_manager.load_image(file_path)

        if self.box_manager.coord_list:
            self.image_manager.get_coords_from_annotation()
            self.box_manager.idx= 0
            self.box_manager_setup()

            for annotation in self.box_manager.coord_list:
                set_old_label(annotation.label)
                set_new_label(annotation.label, "based on annotation", "yellow")
                self.image_manager.draw_rect_from_box_list(self.box_manager.coord_list,
                                                           set_to_current=not self.image_manager.widget.use_batch_idx or self.image_manager.widget.fast_check,
                                                           copy=False,
                                                           text=self.old_label if self.image_manager.widget.fast_check else None)
            # self.image_manager.widget.button.setText(self.old_label)
        else:
            if self.image_manager.widget.use_batch_idx:
                label = self.label_by_filename()
                set_old_label(label)
                set_new_label(label, "based on file name", "yellow")
            else:
                self.image_manager.widget.set_info_label("no annotation", "red")

        print("loaded annotation dict:")
        """for box in self.box_manager.coord_list:
            print(box)"""
        print(self.box_manager.coord_list)



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
        self.box_manager.coord_list[self.box_manager.idx].label = label
        self.image_manager.widget.set_new_label_label(self.new_label, "yellow")

    def set_not_a_sign(self):
        self.not_a_sign = True
        self.new_label = "not_a_sign"
        self.image_manager.widget.set_coords_label(-1, -1, -1, -1, "yellow")
        self.image_manager.widget.set_new_label_label(self.new_label, "yellow")

    def save_annotation(self):
        if self.box_manager.coord_list is None:
            annotation_dict = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)
            self.image_manager.draw_rect_from_box_list(annotation_dict, set_to_current=True)
        annotation_list = []  # Initialize an empty list for the current image's annotations

        self.batch_label_dict[self.current_batch_index] = self.new_label

        for annotation in self.box_manager.coord_list:
            print(len(self.box_manager.coord_list))
            if not annotation.label == "not_a_sign":
                if all([self.current_image_name is not None,
                        annotation.label is not None,
                        annotation.x_1 is not None,
                        annotation.y_1 is not None,
                        annotation.x_2 is not None,
                        annotation.y_2 is not None,
                        self.image_manager.y_back_scale is not None]):
                    print("------------------------------------------")
                    x1, y1, x2, y2 = self.image_manager.get_back_scaled_coords(annotation.x_1, annotation.y_1, annotation.x_2, annotation.y_2)
                    annotation_dict = {
                        "label": annotation.label,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "electric": annotation.electric
                    }
                    # Set widget labels and update the UI
                    self.image_manager.widget.set_coords_label(int(x1), int(y1), int(x2), int(y2), "green")
                    self.image_manager.widget.set_new_label_label(self.new_label, "green")
                    self.image_manager.widget.set_info_label("Saved", "green")
                    print("asdasdsad")
                    self.image_manager.widget.set_electric_label(annotation=True, color="green")
                    self.image_manager.set_last_coords()
                else:
                    print("annotation can't be saved {}".format((self.current_image_name,
                                                                 annotation.label,
                                                                 annotation.x_1,
                                                                 annotation.y_1,
                                                                 annotation.x_2,
                                                                 annotation.y_2,
                                                                 self.image_manager.y_back_scale)))
            else:
                annotation_dict = {
                    "label": "not_a_sign",
                    "x1": None,
                    "y1": None,
                    "x2": None,
                    "y2": None,
                    "electric": False
                }
                self.image_manager.widget.set_coords_label(-1, -1, -1, -1, "green")
                self.image_manager.widget.set_new_label_label(self.new_label, "green")
                self.image_manager.widget.set_info_label("Saved", "green")
                self.image_manager.widget.set_electric_label(annotation=True, color="green")
                self.image_manager.set_last_coords_to_none()

            print(annotation_dict)
            # Append the annotation to the list for the current image
            annotation_list.append(annotation_dict)

        # Now add the annotations to the manager for the current image
        if self.current_image_name in self.annotation_manager.annotation_list:
            self.annotation_manager.annotation_list = dict()
        for annotation_dict in annotation_list:
            self.annotation_manager.add_annotation(annotation_dict, self.current_image_name)

        # Save the annotations list to the specified output directory
        self.annotation_manager.save_annotation_list(self.file_manager.output_dir)


    def save_last_idx(self):
        if len(self.file_manager.file_list) > 0:
            index_data = {"last_image_index": self.file_index % len(self.file_manager.file_list)}
            # Write the updated data back to the JSON file
            with open(self.file_manager.last_index_file, "w") as f:
                json.dump(index_data, f, indent=4)

            print("last_image_index is saved: {}".format(index_data["last_image_index"]))
        else:
            print("last_image_index can not be saved")

    def jump_to(self):
        directory_check(self.file_manager)
        # check if input number correct
        num, ok = QInputDialog.getInt( None,"Jump to index", "Enter image number:")
        if ok:
            # Create the image file path based on the entered number
            if 0 <= num < len(self.file_manager.file_list):
                self.file_index = int(num)
                self.update(draw_previous=False)
                self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")
                self.image_manager.clear_coords()

    def box_manager_setup(self):
        # give coords to be able to edit active box
        self.image_manager.start_x = self.box_manager.coord_list[0].x_1
        self.image_manager.top_left_x = self.box_manager.coord_list[0].x_1
        self.image_manager.start_y = self.box_manager.coord_list[0].y_1
        self.image_manager.top_left_y = self.box_manager.coord_list[0].y_1
        self.image_manager.end_x = self.box_manager.coord_list[0].x_2
        self.image_manager.bottom_right_x = self.box_manager.coord_list[0].x_2
        self.image_manager.end_y = self.box_manager.coord_list[0].y_2
        self.image_manager.bottom_right_y = self.box_manager.coord_list[0].y_2

        self.box_manager.coord_list[0].activate()
        self.box_manager.coord_list[0].color = Qt.cyan

        self.box_manager.set_electric()