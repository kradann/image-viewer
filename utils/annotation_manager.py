import os
import json
from pprint import pprint
from utils.box import Box
from PyQt5.QtCore import Qt
#from modify_json import annotation


#from PyQt5 import QtWidgets



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
        if image_name in self.annotation_list:
            return_list = []
            for annotation in self.annotation_list[image_name]:
                #pprint(annotation)
                box = Box(annotation["x1"], annotation["y1"], annotation["x2"], annotation["y2"],annotation["electric"], annotation["label"], False)
                #pprint(box)
                return_list.append(box)
            return return_list
        return []

    def add_annotation(self, annotation_dict_to_add, image_name):
        print("saved annotation:")
        pprint(annotation_dict_to_add)
        modified = False
        """for annotation_idx in range(len(self.annotation_list)):
            if self.annotation_list[annotation_idx]["image_name"] == annotation_dict_to_add["image_name"]:
                self.annotation_list[annotation_idx] = annotation_dict_to_add
                modified = True

        if not modified:
            self.annotation_list.append(annotation_dict_to_add)"""
        if image_name in self.annotation_list:
            # If it does, append the new annotation to the list
            self.annotation_list[image_name].append(annotation_dict_to_add)
        else:
            # If no annotations exist for this image, create a new list with the first annotation
            self.annotation_list[image_name] = [annotation_dict_to_add]

    def save_annotation_list(self, output_dir):
        annotation_path = os.path.join(output_dir, self.annotation_filename)
        with open(annotation_path, "w") as f:
            json.dump(self.annotation_list, f, indent=4)



