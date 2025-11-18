from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
from tqdm import tqdm
import os

class FolderScanThread(QThread):
    scanned = pyqtSignal(dict,dict)

    def __init__(self, root, label_set):
        super().__init__()
        self.root = Path(root) if root else None
        self.label_set = label_set

    def run(self):
        labels = {name: set() for name in self.label_set}
        counts = {}

        if not self.root or not self.root.exists():
            self.scanned.emit(labels, counts)
            return

        # Single pass: prune label dirs (leaf) and count PNGs immediately
        for dirpath, dirnames, filenames in os.walk(self.root, topdown=True): # using os instead pathlib because its faster
            # Work on a copy because we modify dirnames in-place
            for d in list(dirnames):
                if d in self.label_set:
                    full = Path(dirpath) / d
                    labels[d].add(full)

                    # Count PNG files inside the leaf folder (no deeper walk needed)
                    try:
                        png_count = sum(
                            1
                            for entry in os.scandir(full)
                            if entry.is_file() and entry.name.lower().endswith('.png')
                        )
                        counts[d] = counts.get(d, 0) + png_count
                    except Exception:
                        pass

                    # Prune: do not descend into this label folder
                    dirnames.remove(d)

        self.scanned.emit(labels, counts)

    '''
    def run(self):
        labels = {l: set() for l in self.label_set}
        counts = {}

        if not self.root or not self.root.exists():
            self.scanned.emit(labels, counts)
            return

        for path in tqdm(self.root.rglob('*'), desc='rglob'):
            if path.is_dir():
                n = path.name
                if n in labels:
                    labels[n].add(path)

        for label, paths in tqdm(labels.items(), desc='labels'):
            if paths:
                c = 0
                for path in paths:
                    try:
                        for f in tqdm(path.iterdir(), desc='path'):
                            if f.suffix.lower() == '.png':
                                c += 1
                    except Exception:
                        pass
                counts[label] = c

        self.scanned.emit(labels, counts)'''