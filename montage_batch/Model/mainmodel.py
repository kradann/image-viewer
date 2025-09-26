from PyQt5 import QtWidgets


class Mainmodel(QtWidgets.QMainWindow):
    def __init__(self):
        super(Mainmodel, self).__init__()
        self.loader = None
        self.folder_path = None
        self.main_folder = None  # Folder that stores the subfolders
        self.first_check = True
        self.is_all_region = False  # user load multiple regions
        self.image_paths = None  # used when multiple regions
        self.regions = None  # list regions in folder
        self.base_folder = None  # Only use for JSON
        self.thread = None
        self.isAllSelected = False
        self.subfolders = None  # list of subfolders
        self.labels = list()
        self.selected_images = set()
        self.dropped_selected = set()
        self.batch_info_label = QtWidgets.QLabel("Batch Info")
        self.json = None
        self.json_data = None
        self.is_JSON_active = False
