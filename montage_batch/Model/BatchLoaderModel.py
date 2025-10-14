import hashlib
import os
from pathlib import Path

from PIL import Image
from PyQt5 import QtCore, QtGui


class ImageBatchLoader(object):
    def __init__(self, source, batch_size=1000, start_batch_idx=0):
        self.batch_size = batch_size
        self.image_paths = self.collect_image_paths(source)
        #pprint.pprint(self.image_paths)
        self.current_batch_idx = start_batch_idx
        self.label = None
        self.number_of_batches = len(self.image_paths)

    def collect_image_paths(self, source):
        image_paths = []
        if isinstance(source, list):
            for region in source:
                print(region)
                region_path = Path(region)
                for file in region_path.rglob("*"):
                    if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                        image_paths.append(file)
        else:
            source_path = Path(source)
            for file in source_path.rglob("*"):
                if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                    image_paths.append(file)
        print(image_paths[:10])
        return sorted(image_paths)

    def get_batch(self):
        start_idx = self.current_batch_idx * self.batch_size
        end_idx = start_idx + self.batch_size
        return self.image_paths[start_idx:end_idx]

    def next_batch(self):
        if (self.current_batch_idx + 1) * self.batch_size < len(self.image_paths):
            self.current_batch_idx += 1
        print("batch idx: {}".format(self.current_batch_idx))

    def previous_batch(self):
        if self.current_batch_idx > 0:
            self.current_batch_idx -= 1
        print("batch idx: {}".format(self.current_batch_idx))
        
