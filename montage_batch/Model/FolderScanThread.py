from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
from tqdm import tqdm
import os


def scan_and_count_labels(root_path, label_set, extensions=('.png')):
    root = Path(root_path) if root_path else None
    labels = {name: set() for name in label_set}
    counts = {}

    if not root or not root.exists():
        return labels, counts

    # Single pass: find label dirs, count images, and prune
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        for d in list(dirnames):
            if d in label_set:
                full = Path(dirpath) / d
                labels[d].add(full)

                # Count image files inside the leaf folder
                try:
                    image_count = sum(
                        1
                        for entry in os.scandir(full)
                        if entry.is_file() and entry.name.lower().endswith(extensions)
                    )
                    counts[d] = counts.get(d, 0) + image_count
                except Exception as e:
                    print(f"Error counting images in {full}: {e}")

                # Prune: do not descend into this label folder
                dirnames.remove(d)

    return labels, counts

class FolderScanThread(QThread):
    scanned = pyqtSignal(dict,dict)

    def __init__(self, root, label_set):
        super().__init__()
        self.root = Path(root) if root else None
        self.label_set = label_set

    def run(self):
        labels, counts = scan_and_count_labels(self.root, self.label_set)
        self.scanned.emit(labels, counts)

