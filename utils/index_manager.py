import os
import json

from utils.annotation_manager import AnnotationManager
from utils.image_manager import ImageManager
from utils.file_manager import FileManager


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
        self.current_label = None
        self.not_a_sign = False
        self.batch_label_dict = dict()

    def next_file(self):
        self.file_index += 1
        self.update()
        self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")

    def previous_file(self):
        self.file_index -= 1
        self.update()
        self.image_manager.widget.set_index_label(self.file_index % len(self.file_manager.file_list), "white")

    def update(self):
        self.not_a_sign = False
        file_path, reset = self.file_manager.set_current_file(self.file_index)
        self.image_manager.load_image(file_path)
        self.current_image_name = os.path.basename(file_path)
        annotation_dict = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)

        if annotation_dict is not None:
            if self.image_manager.widget.use_batch_idx:
                self.current_batch_index = self.batch_idx_by_filename()
                if self.current_batch_index in self.batch_label_dict:
                    self.current_batch_index = self.batch_idx_by_filename()
                    self.current_label = self.batch_label_dict[self.current_batch_index]
                    self.image_manager.widget.set_label_label(self.current_label, "yellow")
                    self.image_manager.widget.set_info_label("based on batch idx", "yellow")
                else:
                    self.current_label = annotation_dict["label"]
                    self.image_manager.widget.set_label_label(self.current_label, "white")
                    self.image_manager.widget.set_info_label("from annotation", "white")
            else:
                self.current_label = annotation_dict["label"]
                self.image_manager.widget.set_label_label(self.current_label, "white")
                self.image_manager.widget.set_info_label("from annotation", "white")

            self.image_manager.draw_rect_from_annotation(annotation_dict)
            self.image_manager.widget.button.setText(self.current_label)
        elif self.image_manager.widget.use_batch_idx:
            self.current_batch_index = self.batch_idx_by_filename()

            if self.current_batch_index in self.batch_label_dict:
                self.current_label = self.batch_label_dict[self.current_batch_index]
                self.image_manager.widget.set_label_label(self.current_label, "yellow")
                self.image_manager.widget.set_info_label("based on batch idx", "yellow")
            else:
                self.current_label = self.label_by_filename()
                self.image_manager.widget.set_info_label("based on file name", "white")

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

    def set_current_label(self, label):
        self.not_a_sign = True
        self.current_label = label
        self.image_manager.widget.set_label_label(self.current_label, "yellow")
        self.batch_label_dict[self.current_batch_index] = label

    def set_not_a_sign(self):
        self.not_a_sign = True
        self.current_label = "not_a_sign"
        self.image_manager.widget.set_coords_label(-1, -1, -1, -1, "yellow")
        self.image_manager.widget.set_label_label(self.current_label, "yellow")
        self.batch_label_dict[self.current_batch_index] = self.current_label

    def save_annotation(self):
        if not self.not_a_sign:
            if all([self.current_image_name is not None,
                    self.current_label is not None,
                    self.image_manager.top_left_x is not None,
                    self.image_manager.top_left_y is not None,
                    self.image_manager.bottom_right_x is not None,
                    self.image_manager.bottom_right_y is not None,
                    self.image_manager.bottom_right_y is not None,
                    self.image_manager.y_back_scale is not None]):
                x1 = self.image_manager.top_left_x * self.image_manager.x_back_scale
                y1 = self.image_manager.top_left_y * self.image_manager.y_back_scale
                x2 = self.image_manager.bottom_right_x * self.image_manager.x_back_scale
                y2 = self.image_manager.bottom_right_y * self.image_manager.y_back_scale

                annotation_dict = {
                    "image_name": self.current_image_name,
                    "label": self.current_label,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                }
                self.annotation_manager.add_annotation(annotation_dict)
                self.annotation_manager.save_annotation_list(self.file_manager.output_dir)
                self.image_manager.widget.set_coords_label(int(x1), int(y1), int(x2), int(y2), "green")
                self.image_manager.widget.set_label_label(self.current_label, "green")
                self.image_manager.widget.set_info_label("Saved", "green")
            else:
                print("annotation can't be saved {}".format((self.current_image_name,
                                                             self.current_label,
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
            self.image_manager.widget.set_label_label(self.current_label, "green")
            self.image_manager.widget.set_info_label("Saved", "green")

    def save_last_idx(self):
        index_data = {"last_image_index": self.file_index % len(self.file_manager.file_list)}
        # Write the updated data back to the JSON file
        with open(self.file_manager.last_index_file, "w") as f:
            json.dump(index_data, f, indent=4)

        print("last_image_index is saved: {}".format(index_data["last_image_index"]))
