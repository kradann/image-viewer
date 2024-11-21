import os
import json


class Annotation(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.annotation_filename = "annotation.json"
        self.annotation_list = list()

        self.search_for_annotation()

    def search_for_annotation(self):
        annotation_path = os.path.join(self.output_dir, self.annotation_filename)
        if os.path.isfile(annotation_path):
            with open(annotation_path, "r") as stream:
                self.annotation_list = json.load(stream)
            print("existed annotation.json is loaded with path {}".format(annotation_path))
        else:
            print("new annotation.json is created with path {}".format(annotation_path))

    def get_annotation_by_image_name(self, image_name):
        for annotation_dict in self.annotation_list:
            if annotation_dict["image_name"] == image_name:
                return annotation_dict

