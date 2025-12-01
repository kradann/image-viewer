import copy, shutil, subprocess, sys, json, requests
import logging
import pprint
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
from Model.FolderScanThread import FolderScanThread




APP_VERSION = "0.1.0"
GITHUB_RELEASE_LINK = "https://api.github.com/repos/kradann/image-viewer/releases/latest"


def check_image_name(img_path, output_folder):
    dst_path = output_folder / img_path.name
    base, ext = Path(img_path.name).stem, Path(img_path.name).suffix

    counter = 1
    while dst_path.exists():
        dst_path = dst_path.parent / f"{base}_{counter}{ext}"
        counter += 1

    return dst_path


class MainModel(QObject):
    #Signals for grid view model
    # notifies grid view model to load images from folder (subfolders, start batch index, is the input json)
    load_folder= pyqtSignal(dict, int, bool)
    clear_images =  pyqtSignal() #clears images from grid
    load_selected_images = pyqtSignal(set) # #notifies grid view model to load only selected images
    update_folder_list = pyqtSignal() # updates folder list
    show_wrong_folder_names = pyqtSignal(list) #shows wrong folder dialog
    set_base_folder_signal = pyqtSignal() #shows base folder dialog
    change_info_label = pyqtSignal(str)  # updates info label

    #Signals for folder list view model
    highlight_current_folder_name = pyqtSignal(str)  # highlight current folder in folder list by name
    load_folder_with_click = pyqtSignal(str)  # loads folder by click

    def __init__(self, loader=None):
        super().__init__()
        self.scan_thread = None
        self.loader = loader

        self.current_label_folder_paths = None
        self.current_label = None
        self.main_folder = None  # Folder that stores the subfolders / Folder that stored the folders of the regions

        self.labels = dict()

        self.is_input_from_json = False

        self.current_label_list = set()
        self.load_labels_from_json(str(Path(__file__).parent.parent / 'resources/sign_types/EU_sign_types.json'))

        self.current_log_file_path = None

        self.dir_tree_data = None

        self.last_move = dict()

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

    def set_base_folder(self, base_folder_path):
        self.base_folder = Path(base_folder_path)

    def set_subfolders(self, count):
        self.subfolders = count
        self.subfolders = dict(sorted(self.subfolders.items()))

    # === Getters ===
    @property
    def get_current_batch(self):
        return self.loader.get_batch()

    @property
    def get_batch(self):
        return self.loader.get_batch() if self.loader else []

    @property
    def get_num_of_columns(self):
        return self.num_of_col

    @property
    def get_mode(self):
        return self.mode

    @property
    def get_folder_paths(self):
        return self.current_label_folder_paths

    @property
    def get_subfolders(self):
        return self.subfolders

    @property
    def get_regions(self):
        return self.regions

    @property
    def get_all_sign_type(self):
        return self.all_sign_types

    @property
    def get_current_label(self):
        return self.current_label

    @property
    def get_is_json(self):
        return self.is_input_from_json

    @property
    def get_current_label_list(self):
        return self.current_label_list

    @property
    def get_loader(self):
        return self.loader

    @property
    def get_batch_size(self):
        return self.batch_size

    @property
    def get_log_file_path(self):
        return self.current_log_file_path

    @property
    def get_dir_tree_data(self):
        return self.dir_tree_data

    @property
    def get_last_move(self):
        return self.last_move

    @property
    def get_main_folder(self):
        return self.main_folder

    def get_base_folder(self):
        return self.base_folder

    def get_position(self, idx):
        return idx // self.num_of_col, idx % self.num_of_col

    def find_label_folders(self):

        label_paths = {label: set() for label in self.current_label_list}

        wrong_folder_names = []
        base = Path(self.main_folder)
        if self.main_folder:
            for path in base.rglob('*'):
                if path.is_dir():
                    folder_name = path.name
                    if folder_name in self.current_label_list:
                        label_paths[folder_name].add(path)
                    else:
                        wrong_folder_names.append(folder_name)

            return label_paths
        return None


    def load_main_folder(self, path : str):
        if not path:
            return None, []
        self.is_input_from_json = False
        self.main_folder = Path(path)
        logging.info(f"{path} loadded as main folder")
        self.collect_subfolders_async()



    def load_folder_by_folder_name(self, folder_name : str, batch=0):
        self.current_label_folder_paths = self.labels[folder_name]
        self.current_label = folder_name
        self.load_folder.emit(self.subfolders, batch, self.is_input_from_json)


    '''def collect_subfolders(self):
        self.labels = self.find_label_folders()
        from tqdm import tqdm
        self.labels = {k: self.labels[k] for k in sorted(self.labels.keys()) if self.labels[k]}
        print(self.labels)
        for label, paths in self.labels.items():
            if paths:
                count = 0
                for path in tqdm(paths):
                    count += sum(1 for file in path.iterdir() if file.suffix.lower() == '.png')

                self.subfolders[label] = count
        self.subfolders = {k: self.subfolders[k] for k in sorted(self.subfolders.keys())}'''

    def collect_subfolders_async(self):
        self.scan_thread = FolderScanThread(self.main_folder, self.current_label_list)
        self.scan_thread.scanned.connect(self._on_scan_done)
        self.scan_thread.start()

    def _on_scan_done(self, labels, counts):
        self.labels = {k: labels[k] for k in sorted(labels.keys()) if labels[k]}
        self.subfolders = {k: counts.get(k,0) for k in sorted(counts.keys())}

        if self.labels:
            self.current_label = list(self.labels.keys())[0]
            self.current_label_folder_paths = self.labels[self.current_label]

        self.update_folder_list.emit()
        self.load_folder.emit(self.subfolders, 0, self.is_input_from_json)

    def collect_labels_from_json(self):
        self.is_input_from_json = True
        for path, label in self.json_data.items():
            image_path = self.base_folder / path
            if image_path.exists():
                if self.current_label is None:
                    self.current_label = label
                if label not in self.subfolders.keys():
                    self.subfolders[label] = 0
                self.subfolders[label] += 1
                self.labels[label].add(image_path)


    def load_json(self, json_data):

        with open(json_data[0], 'r', encoding='utf-8') as json_file:
            self.json_data = json.load(json_file)
            logging.info(f"{json_data[0]} loaded")
        if not isinstance(self.json_data, dict):
            raise ValueError("Invalid json format")
        self.set_base_folder_signal.emit()

        self.labels = {label : set() for label in self.current_label_list}

        if self.base_folder:
            self.collect_labels_from_json()
            if self.current_label:
                self.current_label_folder_paths = self.labels[self.current_label]
                self.load_folder.emit(self.subfolders, 0, self.is_input_from_json)


    def clear_selected_images(self):
        self.selected_images = set()

    def is_selected(self, path):
        for img in self.selected_images:
            if str(img) == str(path):
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


    def load_prev_folder(self):
        if self.main_folder is None and self.base_folder is None:
            return

        subfolders = list(self.subfolders.keys())
        prev_folder_idx = subfolders.index(str(self.current_label))-1

        # get label name because subfolder does not contain every label name
        current_prev_label = list(self.subfolders.keys())[prev_folder_idx+1]

        if prev_folder_idx >= 0:
            current_prev_label = list(self.subfolders.keys())[prev_folder_idx]
            while list(self.subfolders.values())[prev_folder_idx] == 0:
                if prev_folder_idx == 0:
                    break
                prev_folder_idx -= 1
                current_prev_label = list(self.subfolders.keys())[prev_folder_idx]


        if self.current_label != current_prev_label:
            self.current_label_folder_paths = self.labels[current_prev_label]
            self.current_label = current_prev_label

            self.load_folder.emit(self.subfolders, 0, self.is_input_from_json)

    def load_next_folder(self):
        if self.main_folder is None and self.base_folder is None:
            return
        subfolders = list(self.subfolders.keys())
        next_folder_idx = subfolders.index(str(self.current_label))+1

        # get label name because subfolder does not contain every label name
        current_next_label = list(self.subfolders.keys())[next_folder_idx-1]

        if next_folder_idx <= len(subfolders) - 1:
            current_next_label = list(self.subfolders.keys())[next_folder_idx]
            while list(self.subfolders.values())[next_folder_idx] == 0:
                if next_folder_idx == len(subfolders) - 1:
                    break
                next_folder_idx += 1
                current_next_label = list(self.subfolders.keys())[next_folder_idx]

        if self.current_label != current_next_label:
            self.current_label_folder_paths = self.labels[current_next_label]
            self.current_label = current_next_label

            self.load_folder.emit(self.subfolders, 0, self.is_input_from_json)

    def load_prev_batch(self):
        if self.loader:
            self.loader.previous_batch()

    def load_next_batch(self):
        if self.loader:
            self.loader.next_batch()

    def move_selected(self, selected_folder):
        if self.selected_images:
            new_folder_created = False
            self.last_move = dict()
            for img_path in self.selected_images:
                self.dropped_selected.discard(img_path)
                img_path = Path(img_path)

                # image path main_folder/data_type/region/label/image.jpg
                output_folder = img_path.parent.parent / selected_folder # cut path to region and add new label

                folder_existed = output_folder.exists()
                output_folder.mkdir(parents=True, exist_ok=True)

                if not folder_existed:
                    new_folder_created = True
                    if output_folder.name not in self.labels:
                        self.labels[output_folder.name] = set()
                    if output_folder not in self.labels[output_folder.name]:
                        self.labels[output_folder.name].add(output_folder)
                # check if destination folder contains file that has same name
                dst_path = check_image_name(img_path, output_folder)
                self.last_move[str(img_path)] = str(dst_path)
                shutil.move(img_path, str(dst_path))
                logging.info(f"{img_path} moved to {dst_path}")

            self.change_info_label.emit(f"Selected images move successfully to {selected_folder}")

            self.update_folder_list.emit()

        else:
            self.change_info_label.emit("No selected image found!")

        # Check if any selected images left
        if len(self.dropped_selected) > 0:
            self.selected_images = copy.deepcopy(self.dropped_selected)
            self.show_only_selected()
        else:
            self.selected_images = set()
            #self.load_folder.emit(self.subfolders, self.loader.current_batch_idx, self.is_input_from_json)

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images.emit()
        self.dropped_selected = {img for img in self.selected_images}
        self.load_selected_images.emit(self.dropped_selected)


    def undo_last_move(self):
        if self.last_move:
            for key, value in self.last_move.items():
                shutil.move(value, key)
            self.change_info_label.emit("Last move undid")

    #TODO: check if function works
    #TODO: Dont use messageBox
    def check_for_update(self):
        try:
            response = requests.get(GITHUB_RELEASE_LINK, timeout=10)

            if response.status_code == 404:
                QMessageBox.information(self, 'Update', "No releases found")
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

    @staticmethod
    def create_log_folder():
        log_folder_path = Path(__file__).parent.parent / '.logs'
        log_folder_path.mkdir(parents=True, exist_ok=True)


    def create_log_file(self):
        log_dir = Path(__file__).resolve().parent.parent / '.logs'
        log_filename = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.current_log_file_path = str(log_filename)
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        logging.info("Annotation tool started!")


    def load_labels_from_json(self, json_path):
        with open(json_path, 'r') as label_json:
            labels_from_json = json.load(label_json)
        self.current_label_list = labels_from_json
        self.current_label_list.sort()
        if not self.is_input_from_json:
            self.load_main_folder(self.main_folder)

    def load_dir_tree(self, dir_tree_path):
        with open(dir_tree_path[0], 'r') as dir_tree:
            #content = dir_tree.read()
            #print(repr(content))
            self.dir_tree_data = json.load(dir_tree)

    def move_file_dir_tree(self, base_folder):
        try:
            not_found_images = []
            if base_folder.exists():
                if not isinstance(self.dir_tree_data, dict):
                    raise ValueError("Wrong JSON file format. Should be dict")
                self.main_folder = base_folder
                labels_folder = self.find_label_folders()
                for key, value in self.dir_tree_data.items(): #(image name, where to move (relative path)
                    image_found = False
                    for label_folders_list in labels_folder.values(): # (label, folder path to that label)
                        for label_path in label_folders_list:  # list of folder path
                            for image in label_path.iterdir(): # folder path
                                if image.name == key:
                                    image_found = True
                                    print(image,'\n',base_folder / value / image.name)
                                    #shutil.move(image, value)
                    if not image_found:
                        not_found_images.append(key)

                return not_found_images

            else:
                raise ValueError("No Folder Loaded")
        except Exception as e:
            logging.info(e)

    def make_directory_tree(self, folder_path):
        if not Path(folder_path).exists():
            raise ValueError("Folder not exists")

        if not self.main_folder or self.base_folder:
            raise ValueError("Load folder to make directory tree")

        folder_path = Path(folder_path)
        main = Path(self.main_folder)
        text = dict()
        if self.main_folder:
            for folder in main.rglob('*'):
                if folder.is_dir():
                    for image in folder.iterdir():
                        if str(image).endswith('.png'):
                            rel_path = image.relative_to(main)
                            text[image.name] = str(rel_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = folder_path / f"dir_tree_{timestamp}.json"

        with open(json_path, 'w') as f:
            json.dump(text, f, indent=4)

        self.change_info_label.emit("Directory tree export file created")





