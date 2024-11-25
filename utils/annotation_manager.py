import os
import json
from pprint import pprint


class AnnotationManager(object):
    def __init__(self):
        self.annotation_filename = "annotation.json"
        self.annotation_list = list()

    def search_for_annotation(self, output_dir):
        annotation_path = os.path.join(output_dir, self.annotation_filename)
        if os.path.isfile(annotation_path):
            with open(annotation_path, "r") as stream:
                self.annotation_list = json.load(stream)
            print("already existing annotation.json is loaded with path {}".format(annotation_path))
        else:
            print("new annotation.json is created with path {}".format(annotation_path))

    def get_annotation_by_image_name(self, image_name):
        for annotation_dict in self.annotation_list:
            if annotation_dict["image_name"] == image_name:
                return annotation_dict
        return None

    def add_annotation(self, annotation_dict_to_add):
        pprint(annotation_dict_to_add)
        modified = False
        for annotation_idx in range(len(self.annotation_list)):
            if self.annotation_list[annotation_idx]["image_name"] == annotation_dict_to_add["image_name"]:
                self.annotation_list[annotation_idx] = annotation_dict_to_add
                modified = True

        if not modified:
            self.annotation_list.append(annotation_dict_to_add)

    def save_annotation_list(self, output_dir):
        annotation_path = os.path.join(output_dir, self.annotation_filename)
        with open(annotation_path, "w") as f:
            json.dump(self.annotation_list, f, indent=4)
