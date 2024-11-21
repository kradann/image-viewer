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
        self.last_batch_index = None

        self.current_label = None
        self.last_label = None


    def next_file(self):
        self.file_index += 1
        self.update()


    def previous_file(self):
        self.file_index -= 1
        self.update()


    def update(self):
        file_path, batch_index, reset = self.file_manager.set_current_file(self.file_index)
        self.image_manager.load_image(file_path)
        self.current_image_name = os.path.basename(file_path)
        annotation_dict = self.annotation_manager.get_annotation_by_image_name(self.current_image_name)

        if annotation_dict is not None:
            self.image_manager.draw_rect_from_annotation(annotation_dict)
            self.current_label = annotation_dict["label"]
            self.image_manager.widget.set_label_label(self.current_label, "yellow")

        if reset:
            self.file_index = 0


    def save_annotation(self):
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


    def __exit__(self, exc_type, exc_val, exc_tb):
        index_data = {"last_image_index": self.file_index}

        # Write the updated data back to the JSON file
        with open(self.file_manager.last_index_file, "w") as f:
            json.dump(index_data, f, indent=4)
