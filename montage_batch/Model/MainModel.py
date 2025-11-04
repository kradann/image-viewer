import copy, shutil, subprocess, sys, json, requests
import pprint
from pathlib import Path
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox




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
        self.loader = loader

        self.current_label_folder_paths = None
        self.current_label = None
        self.main_folder = None  # Folder that stores the subfolders / Folder that stored the folders of the regions

        self.labels = dict()

        self.is_input_from_json = False

        self.current_label_list = list()
        self.load_labels_from_json(str(Path(__file__).parent.parent / 'resources/EU_sign_types.json'))

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

    def get_base_folder(self):
        return self.base_folder

    def get_position(self, idx):
        return idx // self.num_of_col, idx % self.num_of_col

    def find_label_folders(self):
        label_paths = {label : [] for label in self.current_label_list}
        wrong_folder_name = []
        if self.main_folder:
            for path in Path(self.main_folder).rglob('*'):
                if path.is_dir():
                    if path.name in self.current_label_list:
                        label_paths[path.name].append(path)
                    else:
                        wrong_folder_name.append(path.name)
            return label_paths
        return None


    def load_main_folder(self, path : str):
        if not path:
            return None, []
        self.is_input_from_json = False
        self.main_folder = Path(path)

        self.collect_subfolders()

        #self.collect_subfolders()
        #print("első" , list(labels.values())[0])
        self.current_label_folder_paths = list(self.labels.values())[0]
        self.current_label = list(self.labels.keys())[0]

        '''
        if all(sub in SIGN_TYPES for sub in self.subfolders):
            if self.wrong_folder_names:
                self.show_wrong_folder_names.emit(self.wrong_folder_names)
            self.folder_path = self.main_folder / list(self.subfolders.keys())[0]
            self.mode = Mode.SINGLE
            return self.mode, self.subfolders
        else:
            self.all_sign_types = self.collect_sign_types()
            if all(sign in SIGN_TYPES for sign in self.all_sign_types):
                if self.wrong_folder_names:
                    self.show_wrong_folder_names.emit(self.wrong_folder_names)
                self.subfolders = {sign_type : 0 for sign_type in self.all_sign_types}
                self.mode = Mode.MULTIPLE
                self.image_paths = [Path(region, self.all_sign_types[0]) for region in self.regions] #load first TS type
                return self.mode, self.image_paths
        '''
        return self.subfolders


    def load_folder_by_folder_name(self, folder_name : str):
        self.current_label_folder_paths = self.labels[folder_name]
        self.current_label = folder_name
        self.load_folder.emit(self.subfolders, 0, self.is_input_from_json)


    def collect_subfolders(self):
        self.labels = self.find_label_folders()

        self.labels = {k: self.labels[k] for k in sorted(self.labels.keys())}

        for label, paths in self.labels.items():
            if paths:
                count = 0
                for path in paths:
                    count += sum(1 for file in path.iterdir() if file.suffix.lower() == '.png')

                self.subfolders[label] = count
        self.subfolders = {k: self.subfolders[k] for k in sorted(self.subfolders.keys())}

    def collect_labels_from_json(self):
        self.is_input_from_json = True
        for path, label in self.json_data.items():
            if (self.base_folder / path).exists():
                if self.current_label is None:
                    self.current_label = label
                if label not in self.subfolders.keys():
                    self.subfolders[label] = 0
                self.subfolders[label] += 1

                if (self.base_folder / path) not in self.labels[label]:
                    self.labels[label].append(self.base_folder / path)

    def load_json(self, json_data):
            with open(json_data[0], 'r', encoding='utf-8') as json_file:
                self.json_data = json.load(json_file)
            if not isinstance(self.json_data, dict):
                raise ValueError("Invalid json format")
            self.set_base_folder_signal.emit()

            self.labels = {label : [] for label in self.current_label_list}

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
            for img_path in self.selected_images:
                self.dropped_selected.discard(img_path)
                img_path = Path(img_path)

                # image path main_folder/data_type/region/label/image.jpg
                output_folder = img_path.parent.parent / selected_folder # cut path to region and add new label
                output_folder.mkdir(parents=True, exist_ok=True)

                # check if destination folder contains file that has same name
                dst_path = check_image_name(img_path, output_folder)

                shutil.move(img_path, str(dst_path))

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
            self.load_folder.emit(self.subfolders, self.loader.current_batch_idx, self.is_input_from_json)

    def show_only_selected(self):
        if not self.loader:
            return

        self.clear_images.emit()
        self.dropped_selected = {img for img in self.selected_images}
        self.load_selected_images.emit(self.dropped_selected)

    #TODO: check if function works
    #TODO: Dont use messageBox
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

    def load_labels_from_json(self, json_path):
        with open(json_path, 'r') as label_json:
            labels_from_json = json.load(label_json)
        self.current_label_list = labels_from_json
        self.current_label_list.sort()
        if self.is_input_from_json:
            pass
        else:
            self.load_main_folder(self.main_folder)






