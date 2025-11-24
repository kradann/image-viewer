import os
from pathlib import Path
from tqdm import tqdm
import time

import os
from pathlib import Path
from tqdm import tqdm

import os
from pathlib import Path
from tqdm import tqdm


def collect_image_paths(source):
    """Collect with consistent ordering - sort folders and directories"""
    image_paths = []

    if isinstance(source, set):
        # Sort folders first for consistent order
        for folder in sorted(source):
            if folder.is_dir():
                # Collect all paths from this folder first
                folder_paths = []
                for dirpath, dirnames, filenames in os.walk(folder):
                    # Sort subdirectories for consistent traversal order
                    dirnames.sort()

                    # Sort filenames and filter
                    for fname in sorted(filenames):
                        if fname.lower().endswith('.png'):
                            folder_paths.append(Path(dirpath) / fname)

                image_paths.extend(folder_paths)

    return image_paths


class ImageBatchLoader(object):
    def __init__(self, source, batch_size=1000, start_batch_idx=0, is_json=False):
        self.batch_size = batch_size
        if is_json:
            self.image_paths = list(source)
        else:
            self.image_paths = collect_image_paths(source)


        self.current_batch_idx = start_batch_idx
        self.label = None
        self.number_of_batches = len(self.image_paths)

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
        
