import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QInputDialog
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5 import QtWidgets

import geopandas
import os
from glob import glob
from src.traffic_light import Subject, SubType, MaskType
from src.traffic_sign import SignTypeEU, SignTypeUS
import pandas as pd
import json
import numpy as np

LOGGER = logging.getLogger(__name__)

name_attribute_type_dict = {
    "subject": Subject,
    "subtype": SubType,
    "masktype": MaskType,
    "signtype_eu": SignTypeEU,
    "signtype_us": SignTypeUS
}

class ObjectAnnotator(QWidget):
    def __init__(self, attribute_name, title='Object Annotator'):
        super().__init__()
        self.attribute_name = attribute_name if attribute_name is not None else None
        self.attribute_type = name_attribute_type_dict[self.attribute_name]
        self.title = title
        self.outdir = None

        self.pixmap = None
        self.text = None
        self.image = None
        self.layout = None
        self.annotated_csv_path = None
        self.annotated_map_path = None

        self.init_window()

        self.ecef_crs = "urn:ogc:def:crs:EPSG::4328"
        self.annotation_df = None
        self.image_paths = None
        self.image_index = 0
        self.object_ids = None
        self.objects_map = None
        self.last_index_file = None

        self.desktop = QDesktopWidget()
        self.screen = self.desktop.availableGeometry()

    # def prepare_data_for_annotation(self):
    #     from src.training.manual_annotation.json_to_2D_bbox_converter import JsonTo2DBboxConverter
    #     self.objects_map = geopandas.read_file(self.path_to_geojson)
    #
    #     df = pd.read_csv(
    #         "/home/ad.adasworks.com/levente.peto/projects/TL3D_detector/outputs/traffic_signs_qc_results_731979409.txt",
    #         header=None)
    #     df = df[df[7] != "ok"]
    #
    #     self.objects_map = self.objects_map[self.objects_map["GlobalID"].isin(df[0])]
    #
    #     self.objects_map[self.attribute_name] = None
    #     relevant_sequences = set()
    #     for i, row in self.objects_map.iterrows():
    #         views = row["views"]
    #         for key in views.keys():
    #             seq_frameid = views[key]
    #             if seq_frameid != "":
    #                 relevant_sequences.add(seq_frameid.split("_")[0])
    #     relevant_sequences = sorted(list(relevant_sequences))
    #     seq_dir_path = os.path.join(self.path_to_geojson.split("/traffic")[0], "daa")
    #     relevant_sequences = list(map(lambda x: os.path.join(seq_dir_path, x), relevant_sequences))
    #
    #     jsonTo2DBboxConverter = JsonTo2DBboxConverter(relevant_sequences,
    #                                                   self.path_to_detections,
    #                                                   self.outdir,
    #                                                   filter_detections=True,
    #                                                   export_cutouts=True,
    #                                                   objects_ids_to_export=df[0].values.tolist())
    #     jsonTo2DBboxConverter.run()
    #     return
    #     self.image_paths = sorted(glob(os.path.join(jsonTo2DBboxConverter.montage_outdir, "*jpg")))
    #     self.object_ids = jsonTo2DBboxConverter.object_ids
    #     self.annotation_df = jsonTo2DBboxConverter.detection_df_all.copy()
    #     self.annotation_df[self.attribute_name] = None
    #     self.write_out_annotation()

    def init_window(self):
        self.setWindowTitle(self.title)
        self.setPalette(self.dark_palette())
        self.setFixedHeight(700)
        self.init_widgets()

    def init_widgets(self):
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)
        self.image = QLabel()
        self.text = QLabel()
        self.pixmap = QPixmap(1000, 1000)
        self.pixmap.fill(Qt.white)  # Fill with white color
        self.image.setPixmap(self.pixmap)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.text)

        self.init_class_buttons()

        # self._render_image()

    def init_class_buttons(self):
        classes_button = QPushButton("Classes", self)
        next_button = QPushButton("Next", self)
        next_button.setShortcut("Right")
        prev_button = QPushButton("Previous", self)
        prev_button.setShortcut("Left")
        set_output_dir = QPushButton("Set output directory", self)
        jump_to_button = QPushButton("Jump to", self)

        prev_button.clicked.connect(self.prev_button_selected)
        next_button.clicked.connect(self.next_button_selected)
        set_output_dir.clicked.connect(self.set_output_dir)
        jump_to_button.clicked.connect(self.jump_to)

        button_size = 40
        button_width = 1000
        button_row_offset = 5
        menu = QMenu(self)
        for cls in self.attribute_type:
            action = QAction(cls, self)
            action.triggered.connect(self.menu_item_selected)  # Connect to selection handler
            menu.addAction(action)
        classes_button.setMenu(menu)

        classes_button.setFixedHeight(button_size)
        prev_button.setFixedHeight(button_size)
        next_button.setFixedHeight(button_size)
        prev_button.setFixedWidth(button_width)
        next_button.setFixedWidth(button_width)
        set_output_dir.setFixedWidth(button_width)
        set_output_dir.setFixedHeight(button_size)
        classes_button.setFixedWidth(button_width)
        jump_to_button.setFixedWidth(button_width)
        jump_to_button.setFixedHeight(button_size)

        self.layout.addWidget(prev_button, button_row_offset, 0, 1, 1)
        self.layout.addWidget(next_button, button_row_offset + 1, 0, 1, 1)
        self.layout.addWidget(set_output_dir, button_row_offset + 2, 0, 1, 2)
        self.layout.addWidget(classes_button, button_row_offset + 3, 0, 1, 2)
        self.layout.addWidget(jump_to_button, button_row_offset + 4, 0, 1, 2)

    def prev_button_selected(self):
        self.image_index -= 1
        self._render_image()

    def next_button_selected(self):
        self.image_index += 1
        self._render_image()

    def set_output_dir(self):
        output_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory"))
        if output_dir == "":
            return
        self.outdir = output_dir
        self.annotated_csv_path = os.path.join(self.outdir, "annotated_df.csv")
        self.annotated_map_path = os.path.join(self.outdir, "annotated_map.geojson")
        self.setup_data()
        self.open_last_index_file()
        self._render_image()

    def setup_data(self):
        if not os.path.exists(self.annotated_csv_path) or not os.path.exists(self.annotated_map_path):
            print("Annotation csv file or map file is not found.\n"
                  "Please run \'python data_manger.py\' with the proper flags first.\n"
                  "attribute-name must be the same.")
            exit()

        self.annotation_df = pd.read_csv(self.annotated_csv_path)
        self.annotation_df[self.attribute_name] = None
        self.image_paths = np.array(sorted(glob(os.path.join(self.outdir, "montage", "*jpg"))))
        self.objects_map = geopandas.read_file(self.annotated_map_path)
        self.object_ids = np.array([int(os.path.basename(x).split(".jpg")[0]) for x in self.image_paths])
        self.image_paths = self.image_paths[ np.argsort(self.object_ids) ]
        self.object_ids = np.sort(self.object_ids)
        if self.attribute_name in ["signtype_eu", "signtype_us"]:
            self.attribute_name = "subtype"
        if self.attribute_name not in self.objects_map.columns:
            self.objects_map[self.attribute_name] = None
        else:
            self.objects_map.loc[self.objects_map[self.attribute_name].isna(), self.attribute_name] = None
        if self.attribute_name not in self.annotation_df.columns:
            self.annotation_df[self.attribute_name] = None

    def menu_item_selected(self):
        # Get the action that was triggered
        selected_action = self.sender()
        cls = selected_action.text()
        objid = self.object_ids[self.image_index]

        self.annotation_df.loc[self.annotation_df["object_id"] == objid, self.attribute_name] = cls

        self.objects_map.loc[self.objects_map["object_id"] == objid, self.attribute_name] = cls
        self.write_out_annotation()

        self.image_index += 1
        self._render_image()

    def write_out_annotation(self):
        self.annotation_df.to_csv(self.annotated_csv_path, index=False)
        self.objects_map["relevant_sequences"] = self.objects_map["relevant_sequences"].astype(str)
        self.objects_map["manual_relevance_version"] = self.objects_map["manual_relevance_version"].astype("Int64")
        self.objects_map.set_crs(self.ecef_crs, inplace=True, allow_override=True)
        self.objects_map.to_file(self.annotated_map_path, driver="GeoJSON", mode="w")

    def _render_image(self):
        if not 0 <= self.image_index < len(self.image_paths):
            print("Annotation ready, exiting...")
            self.image_index -= 1
            self.save_data()
            exit(0)
        image = QPixmap(self.image_paths[self.image_index])
        # resize_width = min(image.width(), self.screen.width()*0.8)
        objid = self.object_ids[self.image_index]
        attribute_type = self.objects_map.loc[self.objects_map["object_id"] == objid, self.attribute_name]
        attribute_type = None if attribute_type.isna().iloc[0] else attribute_type.iloc[0]
        attribute_type_str = "not annotated yet" if attribute_type is None else attribute_type
        attribute_type_color = 'color:red;' if attribute_type is None else 'color:lime;'
        self.text.setText(
            f"<b>Object ID</b>: <p style={attribute_type_color}>{objid}/{len(self.object_ids)}</p> <b>{self.attribute_name}</b>: <p style={attribute_type_color}>{attribute_type_str}</p>")

        resize_width = 1000
        resize_height = int(min(image.height(), self.screen.height() * 0.8))
        image = image.scaled(resize_width, resize_height, Qt.KeepAspectRatio)
        self.image.setPixmap(image)
        self.image.resize(resize_width, resize_height)
        self.show()

    def open_last_index_file(self):
        self.last_index_file = os.path.join(self.outdir, "last_index.json")
        if os.path.exists(self.last_index_file):
            try:
                with open(self.last_index_file, "r") as stream:
                    last_index_dict = json.load(stream)
            except json.JSONDecodeError:
                print("Error loading last_index.json, possibly corrupt.")

            if isinstance(last_index_dict, dict):
                # Check if "last_image_index" exists and load it
                if "last_image_index" in last_index_dict:
                    self.image_index = last_index_dict["last_image_index"]
                    print("last_image_index is loaded: {}".format(self.image_index))
                else:
                    print("last_image_index key not found in the JSON file.")
            else:
                print("last_image_index key not found in the JSON file.")

        else:
            print("last_index JSON file does not exist yet")

    def jump_to(self):
        if self.object_ids is not None:
            num, ok = QInputDialog.getInt(None, "Jump to index", "Enter image number:")
            if ok:
                # Create the image file path based on the entered number
                if 0 <= num < len(self.object_ids):
                    self.image_index = int(num)
                    self._render_image()

    @staticmethod
    def dark_palette():
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 48))  # Background color
        palette.setColor(QPalette.WindowText, Qt.white)  # Text color

        # palette.setColor(QPalette.Button, QColor(60,70,80)) #Button color
        palette.setColor(QPalette.ButtonText, Qt.black)  # Buttontext color
        return palette

    def closeEvent(self, event):
        self.save_data()
        super().closeEvent(event)

    def save_data(self):
        if self.image_index != 0 and self.attribute_type is not None:
            index_data = {"last_image_index": self.image_index}
            # attribute_type = {"last_attribute_type": str(self.attribute_type)}
            # Write the updated data back to the JSON file
            with open(self.last_index_file, "w") as f:
                json.dump(index_data, f, indent=4)
                # json.dump(attribute_type, f, indent=4)

if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser()

    # parser.add_argument('--path-to-geojson', type=str, required=False, help='Path to the geojson')
    # parser.add_argument('--path-to-detection', type=str, required=False, help='Relative path to the json files')
    parser.add_argument('--attribute-name', type=str, required=True, help='The name of the attribute that you want to annotate')
    # parser.add_argument('--outdir', type=str, required=False, help='Path to the output directory')

    args = parser.parse_args()

    app = QApplication(sys.argv)
    viewer = ObjectAnnotator(args.attribute_name)
    viewer.show()
    app.exec()