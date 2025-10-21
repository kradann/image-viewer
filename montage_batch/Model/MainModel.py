import copy
import shutil
import subprocess
import sys
from enum import Enum
from pathlib import Path

import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

from Model.sign_types import SIGN_TYPES


APP_VERSION = "0.1.0"
GITHUB_RELEASE_LINK = "https://api.github.com/repos/kradann/image-viewer/releases/latest"

class Mode(Enum):
    SINGLE = 1
    MULTIPLE = 2
    JSON = 3


def check_image_name(img_path, output_folder):
    dst_path = output_folder / img_path.name
    base, ext = Path(img_path.name).stem, Path(img_path.name).suffix

    counter = 1
    while dst_path.exists():
        dst_path = dst_path.parent / f"{base}_{counter}{ext}"
        counter += 1

    return dst_path


class MainModel(QtWidgets.QMainWindow):
    load_subfolders = pyqtSignal(list)
    load_folder_single= pyqtSignal(Mode, dict,int)
    load_folder_multiple = pyqtSignal(Mode, list,int)
    clear_images =  pyqtSignal()
    load_selected_images = pyqtSignal(set)
    change_info_label = pyqtSignal(str)
    update_folder_list_label = pyqtSignal()
    highlight_current_folder_name = pyqtSignal(str)
    load_folder_with_click = pyqtSignal(str)
    show_wrong_folder_names = pyqtSignal(list)

    def __init__(self, loader=None):
        super().__init__()
        self.loader = loader
        self.folder_path = None #when single contains all path, when multiple only the folder name
        self.main_folder = None  # Folder that stores the subfolders / Folder that stored the folders of the regions
        self.mode = None #possible modes: single_region, multiple_region, json
        self.first_check = True
        self.wrong_folder_names = list()
        self.image_paths = None  # used when multiple regions
        self.all_sign_types = None # used to store sign type when multiple regions
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

    # === Setters ===

    def set_loader(self, new_loader):
        self.loader = new_loader

    def set_num_of_col(self, number):
        self.num_of_col = number

    # === Getters ===

    def get_current_batch(self):
        return self.loader.get_batch()

    def get_position(self, idx):
        return idx // self.num_of_col, idx % self.num_of_col

    def get_batch(self):
        return self.loader.get_batch() if self.loader else []

    def get_num_of_columns(self):
        return self.num_of_col

    def get_mode(self):
        return self.mode

    def get_folder_path(self):
        return self.folder_path

    def get_subfolders(self):
        return self.subfolders

    def get_regions(self):
        return self.regions

    def get_all_sign_type(self):
        return self.all_sign_types

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

        self.collect_subfolders()

        if any(sub in SIGN_TYPES for sub in self.subfolders):
            if self.wrong_folder_names:
                self.show_wrong_folder_names.emit(self.wrong_folder_names)
            self.folder_path = self.main_folder / list(self.subfolders.keys())[0]
            self.mode = Mode.SINGLE
            return self.mode, self.subfolders
        else:
            self.all_sign_types = self.collect_sign_types()
            self.subfolders = {sign_type : 0 for sign_type in self.all_sign_types}
            self.mode = Mode.MULTIPLE
            self.image_paths = [Path(region, self.all_sign_types[0]) for region in self.regions] #load first TS type
            return self.mode, self.image_paths

    def load_folder(self, folder_name : str):

        if self.mode == Mode.SINGLE:
            self.folder_path = self.main_folder / folder_name
            self.load_folder_single.emit(self.mode, self.subfolders,0)
        elif self.mode == Mode.MULTIPLE:
            self.folder_path = folder_name
            self.image_paths = [Path(region, folder_name) for region in self.regions]
            self.load_folder_multiple.emit(self.mode, self.image_paths,0)


    def collect_sign_types(self):
        main_path = Path(self.main_folder)
        if not main_path.exists() or not main_path.is_dir():
            return []

        self.regions = sorted([d for d in self.main_folder.iterdir() if d.is_dir()])
        all_sign_types = {
            st.name
            for region in self.regions
            for st in region.iterdir()
            if st.is_dir()
        }
        return sorted(all_sign_types)

    def collect_subfolders(self):
        self.subfolders = {f.name: len(list(f.iterdir())) for f in self.main_folder.iterdir() if f.is_dir()}
        self.subfolders = {k: self.subfolders[k] for k in sorted(self.subfolders.keys())}

        wrong_folders_names = []
        if self.first_check:
            self.wrong_folder_names = self.check_for_invalid_folder_names()

        return self.subfolders


    def check_for_invalid_folder_names(self):
        wrong_subfolder_name = []
        for name in self.subfolders.keys():
            if name not in SIGN_TYPES:
                wrong_subfolder_name.append(name)
        return wrong_subfolder_name

    def current_folder_name(self):
        if self.mode == Mode.SINGLE:
            return Path(self.folder_path).name


    def clear_selected_images(self):
        self.selected_images = set()

    def is_selected(self, path):
        for img in self.selected_images:
            if img == path:
                return True
        return False

    def add_image_to_selected(self, img_path):
        self.selected_images.add(img_path)

    def discard_image_from_selected(self, img_path):
        self.selected_images.discard(img_path)

    def toggle_selection(self, path):
        if path in self.selected_images:
            self.selected_images.remove(path)
        else:
            self.selected_images.add(path)



    def batch_info(self):
        if not self.loader:
            return "No Batch"
        return f"Batch: {self.loader.current_batch_idx + 1} / {self.loader.number_of_batches // 1000 + 1}"


    #TODO: Test these 2 function below
    def load_prev_folder(self):
        if self.main_folder is None:
            return
        subfolders = list(self.subfolders.keys())

        prev_folder_idx = subfolders.index(str(self.folder_path).split('/')[-1])-1
        print(prev_folder_idx)
        if self.mode == Mode.SINGLE:
            if prev_folder_idx > 0:
                while not any(f.is_file() for f in Path(self.main_folder / subfolders[prev_folder_idx]).iterdir()):
                    if prev_folder_idx == len(subfolders) - 1:
                        break
                    prev_folder_idx -= 1
        elif self.mode == Mode.MULTIPLE:
            print(prev_folder_idx)
            if prev_folder_idx == -1:
                prev_folder_idx += 1
            print(prev_folder_idx)

        self.folder_path = self.main_folder / subfolders[prev_folder_idx]

        if self.mode == Mode.SINGLE:
            self.load_folder_single.emit(self.mode, self.subfolders,0)
        elif self.mode == Mode.MULTIPLE:
            self.load_folder_with_click.emit(self.folder_path.name)
        #TODO: Move blue highlight when changing folder

    def load_next_folder(self):
        if self.main_folder is None:
            return

        #subfolders = sorted([f for f in Path(self.folder_path).parent.iterdir() if f.is_dir()])

        subfolders = list(self.subfolders.keys())
        print(subfolders)

        next_folder_idx = subfolders.index(str(self.folder_path).split('/')[-1])+1
        print(next_folder_idx)
        print(len(subfolders))
        if self.mode == Mode.SINGLE:
            if next_folder_idx <= len(subfolders) - 1:
                while not any(f.is_file() for f in Path(self.main_folder / subfolders[next_folder_idx]).iterdir()):
                    if next_folder_idx == len(subfolders) - 1:
                        break
                    next_folder_idx += 1
        elif self.mode == Mode.MULTIPLE:
            if next_folder_idx == len(subfolders)-1:
                next_folder_idx -= 1

        self.folder_path = self.main_folder / subfolders[next_folder_idx]
        print(self.folder_path)
        if self.mode == Mode.SINGLE:
            self.load_folder_single.emit(self.mode, self.subfolders,0)
        elif self.mode == Mode.MULTIPLE:
            self.load_folder_with_click.emit(self.folder_path.name)
        #TODO: Move blue highlight when changing folder

    def load_prev_batch(self):
        if self.loader:
            self.loader.previous_batch()

    def load_next_batch(self):
        if self.loader:
            self.loader.next_batch()

    def move_selected(self, selected_folder):
        if self.mode == Mode.SINGLE:
            output_folder = Path(self.main_folder) / selected_folder
            output_folder.mkdir(parents=True, exist_ok=True)
            folder_where_image_moved_from = ''

            if self.selected_images:
                for img_path in self.selected_images:
                    self.dropped_selected.discard(img_path)
                    img_path = Path(img_path)
                    folder_where_image_moved_from = img_path.parent.name
                    # check if destination folder contains file that has same name
                    dst_path = check_image_name(img_path, output_folder)
                    shutil.move(img_path, str(dst_path))
                self.change_info_label.emit(f"Selected images move successfully to {selected_folder}")
                self.update_folder_list_label.emit()
                self.highlight_current_folder_name.emit(str(self.folder_path.name))

            else:
                self.change_info_label.emit("No selected image found!")

        elif self.mode == Mode.MULTIPLE:
            if self.selected_images:
                for img_path in self.selected_images:
                    self.dropped_selected.discard(img_path)
                    img_path = Path(img_path)

                    output_folder = Path(img_path.parent.parent) / selected_folder

                    output_folder.mkdir(exist_ok=True)
                    # check if destination folder contains file that has same name
                    dst_path = check_image_name(img_path, output_folder)

                    shutil.move(img_path, str(dst_path))
            else:
                self.change_info_label.emit("No selected image found!")

        # Check if any selected images left
        if len(self.dropped_selected) > 0:
            self.selected_images = copy.deepcopy(self.dropped_selected)
            self.show_only_selected()
        else:
            self.selected_images = set()
            if self.mode == Mode.SINGLE:
                self.load_folder_single.emit(self.mode, self.subfolders, self.loader.current_batch_idx)
            elif self.mode == Mode.MULTIPLE:
                self.load_folder_multiple.emit(self.mode, self.image_paths, self.loader.current_batch_idx)

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images.emit()
        self.dropped_selected = {img for img in self.selected_images}
        self.load_selected_images.emit(self.dropped_selected)

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






