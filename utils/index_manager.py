import os
import json

from utils.image_manager import ImageManager
from utils.file_manager import FileManager


class IndexManager(object):
    def __init__(self, file_manager: FileManager, image_manager: ImageManager):
        self.file_manager = file_manager
        self.image_manager = image_manager
        self.file_index = -1

        self.current_batch_index = None
        self.last_batch_index = None

        self.current_label = None
        self.last_label = None

    def next_file(self):
        self.file_index += 1
        file_path, batch_index = self.file_manager.set_current_file(self.file_index)
        self.image_manager.load_image(file_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        index_data = {"last_image_index": self.file_index}

        # Write the updated data back to the JSON file
        with open(self.file_manager.last_index_file, "w") as f:
            json.dump(index_data, f, indent=4)

