import copy
import shutil
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

from Model.sign_types import SIGN_TYPES
from Model.BatchLoaderModel import ImageBatchLoader
from Model.FolderListModel import FolderListModel
from Model.ImageThreadLoaderModel import ImageLoaderThread
from Model.ClickableModel import Clickable


APP_VERSION = "0.1.0"
GITHUB_RELEASE_LINK = "https://api.github.com/repos/kradann/image-viewer/releases/latest"


class MainModel(QtWidgets.QMainWindow):
    LoadSubfolders = pyqtSignal(list)
    LoadFolder= pyqtSignal(str, dict)
    ClearImages =  pyqtSignal()
    LoadSelectedImages = pyqtSignal(set)

    def __init__(self, loader=None):
        super().__init__()
        self.loader = loader
        self.folder_path = None
        self.main_folder = None  # Folder that stores the subfolders / Folder that stored the folders of the regions
        self.mode = None #possible modes: single_region, multiple_region, json
        self.first_check = True
        self.image_paths = None  # used when multiple regions
        self.regions = None  # list regions in folder
        self.base_folder = None  # Only use for JSON
        self.thread = None
        self.isAllSelected = False
        self.subfolders = dict()  # list of subfolders
        self.selected_images = set()
        self.dropped_selected = set()
        self.json = None
        self.json_data = None
        self.num_of_col = 6
        self.batch_size = 1000
        self.thumbnail_size = 150, 150

    def set_loader(self, new_loader):
        self.loader = new_loader


    '''def load_folder(self):
        #self.folderListView.clear()
        #self.clear_images()
        self.main_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.main_folder:
            self.is_JSON_active = False
            self.subfolders = [f.name for f in Path(self.main_folder).iterdir() if f.is_dir()]
            self.subfolders.sort()

            if any(sub in SIGN_TYPES for sub in self.subfolders):
                self.is_all_region = False
                self.folder_path = Path(self.main_folder) / self.subfolders[0]
                self.load_subfolders(self.main_folder)
                self.loader = ImageBatchLoader(self.folder_path, batch_size=self.batch_size)
                self.show_batch()
                self.change_info_label("Folder loaded!")
            else:
                sign_types_in_all_region = self.collect_sign_types()
                sign_types_in_all_region.sort()
                #pprint.pprint(sign_types_in_all_region)
                self.folderListView.clear()
                self.subfolders = sign_types_in_all_region
                for sign_type in self.subfolders:
                    self.folderListView.addItem(sign_type)
                self.is_all_region = True'''

    def load_main_folder(self, path : str):
        if not path:
            return None, []
        self.main_folder = Path(path)
        self.subfolders = {f.name: len(list(f.iterdir())) for f in self.main_folder.iterdir() if f.is_dir()}
        self.subfolders = {k: self.subfolders[k] for k in sorted(self.subfolders.keys())}

        if any(sub in SIGN_TYPES for sub in self.subfolders):
            self.folder_path = self.main_folder / list(self.subfolders.keys())[0]
            self.mode = "single_region"
            print(1)
            return self.mode, self.subfolders
        else:
            sign_types_in_all_region = self.collect_sign_types()
            self.subfolders = sorted(sign_types_in_all_region)
            self.mode = "multi_region"
            return self.mode, self.subfolders

    def load_folder(self, folder_name : str):
        if self.mode == "single_region":
            self.folder_path = self.main_folder / folder_name
            self.LoadFolder.emit(self.mode, self.subfolders)

    def collect_sign_types(self):
        regions = [d for d in Path(self.main_folder).iterdir() if d.is_dir()]
        all_sign_types = {}
        for region in regions:
            for sign_type in region.iterdir():
                if sign_type.is_dir():
                    # Count items in the sign_type folder
                    all_sign_types[sign_type.name] = len(list(sign_type.iterdir()))
        return all_sign_types


    def load_subfolders(self, path=None):
        self.folderListView.clear()
        if not self.is_JSON_active and not self.is_all_region:
            folder_infos = []
            wrong_subfolder_name = []

            for name in self.subfolders.keys():
                if name in SIGN_TYPES:
                    full_path = Path(path) / name
                    if full_path.is_dir():
                        num_images = len(list(Path(full_path).iterdir()))
                        folder_infos.append((name, num_images))
                else:
                        wrong_subfolder_name.append(name)

            if wrong_subfolder_name and self.first_check:
                self.first_check = False
                msg = "These are not valid subfolder names:\n" + "\n".join(wrong_subfolder_name)
                QMessageBox.information(self, "Subfolder name error", msg)

            folder_infos.sort()  # order list names to abc
            self.subfolders = dict()
            for name, count in folder_infos:
                self.subfolders.append(name)
                display_text = f"{name:<40} {count:>6}"  # left-align name, right-align number
                self.folderListView.addItem(display_text)

            # Set monospaced font for alignment
            font = QFont("Courier New", 10)
            self.folderListView.setFont(font)
        elif not self.is_JSON_active and self.is_all_region:
            print(15)
            for sign_type in self.subfolders.keys():
                self.folderListView.addItem(sign_type)

    def get_current_batch(self):
        return self.loader.get_batch()

    def current_folder_name(self):
        return Path(self.folder_path).name

    def clear_selected_images(self):
        self.selected_images = set()

    def is_selected(self, path):
        return path in self.selected_images

    def add_image_to_selected(self, img_path):
        self.selected_images.add(img_path)

    def discard_image_from_selected(self, img_path):
        self.selected_images.discard(img_path)

    def toggle_selection(self, path):
        if path in self.selected_images:
            self.selected_images.remove(path)
        else:
            self.selected_images.add(path)

    def get_position(self, idx):
        return idx // self.num_of_col, idx % self.num_of_col

    def get_batch(self):
        return self.loader.get_batch() if self.loader else []

    def batch_info(self):
        if not self.loader:
            return "No Batch"
        return f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}"

    def load_prev_folder(self):
        if self.main_folder is None:
            return
        subfolders = sorted([f for f in Path(self.folder_path).parent.iterdir() if f.is_dir()])

        prev_folder_idx = subfolders.index(self.folder_path)-1
        if prev_folder_idx > 0:
            while not any(f.is_file() for f in Path(subfolders[prev_folder_idx]).iterdir()):
                if prev_folder_idx == len(subfolders) - 1:
                    break
                prev_folder_idx -= 1

            self.folder_path = subfolders[prev_folder_idx]
            self.LoadFolder.emit(self.mode, self.subfolders)
            #TODO: Move blue highlight when changing folder

    def load_next_folder(self):
        if self.main_folder is None:
            return
        subfolders = sorted([f for f in Path(self.folder_path).parent.iterdir() if f.is_dir()])

        next_folder_idx = subfolders.index(self.folder_path)+1
        if next_folder_idx <= len(subfolders) - 1:
            while not any(f.is_file() for f in Path(subfolders[next_folder_idx]).iterdir()):
                if next_folder_idx == len(subfolders) - 1:
                    break
                next_folder_idx += 1

            self.folder_path = subfolders[next_folder_idx]
            self.LoadFolder.emit(self.mode, self.subfolders)
            #TODO: Move blue highlight when changing folder

    def load_prev_batch(self):
        if self.loader:
            self.loader.previous_batch()

    def load_next_batch(self):
        if self.loader:
            self.loader.next_batch()

    def move_selected(self, selected_folder):
        if self.mode == "single_region":
            output_folder = Path(self.main_folder) / selected_folder
            output_folder.mkdir(parents=True, exist_ok=True)

            if self.selected_images:
                for img_path in self.selected_images:
                    self.dropped_selected.discard(img_path)
                    img_path = Path(img_path.img_path)
                    dst_path = self.check_image_name(img_path, output_folder)
                    #TODO: Check self.check_image_name modified version
                    #TODO: change info label

                    shutil.move(img_path, str(dst_path))
            else:
                pass
                #TODO: change info label

            if len(self.dropped_selected) > 0:
                self.selected_images = copy.deepcopy(self.dropped_selected)
                #TODO: show only selected
            else:
                self.selected_images = set()
                #TODO: refresh

    def check_image_name(self, img_path, output_folder):
        dst_path = output_folder / img_path.name
        base, ext = Path(img_path.name).stem, Path(img_path.name).suffix

        counter = 1
        while dst_path.exists():
            dst_path = dst_path.parent / f"{base}{counter}{ext}"
            counter += 1

        return dst_path

    def show_only_selected(self):
        if not self.loader:
            return

        self.ClearImages.emit()
        self.dropped_selected = {img.img_path for img in self.selected_images}
        self.LoadSelectedImages.emit(self.dropped_selected)

    #TODO: check if function works
    def check_for_update(self):
        try:
            response = requests.get(GITHUB_RELEASE_LINK, timeout=10)

            if response.status_code == 404:
                QMessageBox.information(self, "Update", "No releases found")
                return

            data = response.json()
            latest_release = data["tag_name"]

            if latest_release != APP_VERSION:
                QMessageBox.information(self, "Update", f"New version {latest_release} available!")

                assets = data.get("assets", [])
                if not assets:
                    QMessageBox.information(self, "Update", "No release asset found!")
                    return

                download_url = assets[0]["browser_download_url"]
                file_name = assets[0]["name"]

                r = requests.get(download_url, stream=True)
                with open(file_name, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                QMessageBox.information(self, "Update", f"Downloaded {file_name} successfully!")

                new_path = Path(file_name).resolve()
                subprocess.Popen([new_path])
                sys.exit(0)
            else:
                QMessageBox.information(self, "Update", "Already up to date!")
        except Exception as e:
            QMessageBox.information(self, "Update", f"An error occurred: {e}")






