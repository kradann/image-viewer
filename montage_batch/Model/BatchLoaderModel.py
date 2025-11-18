from pathlib import Path
from tqdm import tqdm


def collect_image_paths(source):
    image_paths = []
    print("source", source)
    if isinstance(source, set):
        for folder in source:
            print(folder)
            if folder.is_dir():
                for file in folder.rglob("*"):
                    if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                        image_paths.append(file)
    return sorted(image_paths)


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
        
