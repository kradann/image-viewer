import logging
import geopandas
import os
import pandas as pd

from enum import Enum
from glob import glob
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QPixmap

# from src.traffic_light import Subject, SubType, MaskType

LOGGER = logging.getLogger(__name__)


class MaskType(str, Enum):
    FORWARD_ARROW = "forward_arrow"
    LEFT_ARROW = "left_arrow"
    RIGHT_ARROW = "right_arrow"
    FORWARD_LEFT_ARROW = "forward_left_arrow"
    FORWARD_RIGHT_ARROW = "forward_right_arrow"
    SLIGHT_LEFT_ARROW = "slight_left_arrow"
    SLIGHT_RIGHT_ARROW = "slight_right_arrow"
    SLIGHT_LEFT_HARD_LEFT_ARROW = "slight_left_hard_left_arrow"
    SLIGHT_RIGHT_HARD_RIGHT_ARROW = "slight_right_hard_right_arrow"
    LEFT_RIGHT_ARROW = "left_right_arrow"
    FORWARD_LEFT_RIGHT_ARROW = "forward_left_right_arrow"
    U_TURN = "u_turn"
    PEDESTRIAN = "pedestrian"
    HAND = "hand"
    FULL = "full"
    BUS = "bus"
    TRAM_LIGHTS_3_DOTS = "tram_lights_3_dots"
    TRAM_LIGHTS_2_DOTS = "tram_lights_2_dots"
    TRAM_LIGHTS_1_DOTS = "tram_lights_1_dots"
    UNKNOWN = "unknown"

class ColorType(str, Enum):
    RED = "RED"
    RED_YELLOW = "RED+YELLOW"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    UNKNOWN = "UNKNOWN"

class SubType(str, Enum):
    V_3LINE = "v-3line"
    H_3LINE = "h-3line"
    V_2LINE = "v-2line"
    V_4LINE = "v-4line"
    V_5LINE = "v-5line"
    H_5LINE = "h-5line"
    H_2LINE = "h-2line"
    DOGHOUSE = "doghouse"
    SINGLE = "single"
    PEDESTRIAN_HYBRID_BEACON = "pedestrian_hybrid_beacon"
    RAILWAY = "railway"
    UNKNOWN = "unknown"

class Subject(str, Enum):
    VEHICLES = "vehicles"
    PEDESTRIAN = "pedestrian"
    BUS = "bus"
    BICYCLE = "bicycle"
    TRAIN = "train"
    TRAM = "tram"
    UNKNOWN = "unknown"


name_attribute_type_dict = {
    "subject": Subject,
    "subtype": SubType,
    "masktype": MaskType
}

class ObjectAnnotator(QWidget):
    def __init__(self, path_to_geojson, path_to_detections, outdir, attribute_name, title='Object Annotator'):
        super().__init__()
        self.pixmap = None
        self.text = None
        self.image = None
        self.layout = None
        self.title = title
        self.path_to_geojson = path_to_geojson
        self.path_to_detections = path_to_detections
        self.outdir = outdir
        self.attribute_name = attribute_name
        self.attribute_type = name_attribute_type_dict[self.attribute_name]
        self.annotated_csv_path = os.path.join(self.outdir, "annotated_df.csv")
        self.annotated_map_path = os.path.join(self.outdir, "annotated_map.geojson")
        self.ecef_crs = "urn:ogc:def:crs:EPSG::4328"
        self.annotation_df = None
        self.image_paths = None
        self.image_index = 0
        self.object_ids = None
        self.objects_map = None
        if os.path.exists(self.annotated_csv_path) and os.path.exists(self.annotated_map_path):
            self.annotation_df = pd.read_csv(self.annotated_csv_path)
            self.image_paths = sorted(glob(os.path.join(self.outdir, "montage", "*jpg")))
            self.objects_map = geopandas.read_file(self.annotated_map_path)
            self.object_ids = self.objects_map["object_id"].values
            if self.attribute_name not in self.objects_map.columns:
                self.objects_map[self.attribute_name] = None
            else:
                self.objects_map.loc[ self.objects_map[self.attribute_name].isna(), self.attribute_name ] = None
            if self.attribute_name not in self.annotation_df.columns:
                self.annotation_df[self.attribute_name] = None
        else:
            NotImplementedError()
            #self.prepare_data_for_annotation()
        self.desktop = QDesktopWidget()
        self.screen = self.desktop.availableGeometry()
        self.init_window()

    '''
    def prepare_data_for_annotation(self):
        from src.training.manual_annotation.json_to_2D_bbox_converter import JsonTo2DBboxConverter
        self.objects_map = geopandas.read_file(self.path_to_geojson)
        self.objects_map[self.attribute_name] = None
        relevant_sequences = set()
        for i, row in self.objects_map.iterrows():
            views = row["views"]
            for key in views.keys():
                seq_frameid = views[key]
                if seq_frameid != "":
                    relevant_sequences.add(seq_frameid.split("_")[0])
        relevant_sequences = sorted(list(relevant_sequences))
        seq_dir_path = os.path.join(self.path_to_geojson.split("/traffic")[0], "daa")
        relevant_sequences = list(map(lambda x: os.path.join(seq_dir_path, x), relevant_sequences))
        jsonTo2DBboxConverter = JsonTo2DBboxConverter(relevant_sequences, self.path_to_detections, self.outdir, True)
        jsonTo2DBboxConverter.run()
        self.image_paths = sorted(glob(os.path.join(jsonTo2DBboxConverter.montage_outdir, "*jpg")))
        self.object_ids = jsonTo2DBboxConverter.object_ids
        self.annotation_df = jsonTo2DBboxConverter.detection_df_all.copy()
        self.annotation_df[self.attribute_name] = None
        self.write_out_annotation()
    '''

    def init_window(self):
        self.setWindowTitle(self.title)
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

        self._render_image()

    def init_class_buttons(self):
        classes_button = QPushButton("Classes", self)
        prev_button = QPushButton("Previous", self)
        prev_button.setShortcut("Left")
        next_button = QPushButton("Next", self)
        next_button.setShortcut("Right")
        prev_button.clicked.connect(self.prev_button_selected)
        next_button.clicked.connect(self.next_button_selected)

        button_size = 40
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
        self.layout.addWidget(prev_button, button_row_offset + 2, 0, 1, 2)
        self.layout.addWidget(next_button, button_row_offset + 3, 0, 1, 2)
        self.layout.addWidget(classes_button, button_row_offset + 4, 0, 1, 2)

    def prev_button_selected(self):
        self.image_index -= 1
        self._render_image()

    def next_button_selected(self):
        self.image_index += 1
        self._render_image()

    def menu_item_selected(self):
        # Get the action that was triggered
        selected_action = self.sender()
        cls = selected_action.text()
        objid = self.object_ids[self.image_index]

        self.annotation_df.loc[ self.annotation_df["object_id"] == objid, self.attribute_name ] = cls

        self.objects_map.loc[ self.objects_map["object_id"] == objid, self.attribute_name ] = cls
        self.write_out_annotation()

        self.image_index += 1
        self._render_image()

    def write_out_annotation(self):
        self.annotation_df.to_csv(self.annotated_csv_path, index=False)
        print("--------------")
        print(self.objects_map.columns)
        print("------------------")
        self.objects_map["relevant_sequences"] = self.objects_map["relevant_sequences"].astype(str)
        self.objects_map["manual_relevance_version"] = self.objects_map["manual_relevance_version"].astype("Int64")
        self.objects_map.set_crs(self.ecef_crs, inplace=True, allow_override=True)
        self.objects_map.to_file(self.annotated_map_path, driver="GeoJSON", mode="w")

    def _render_image(self):
        if not 0 <= self.image_index < len(self.image_paths):
            print("Annotation ready, exiting...")
            exit(0)
        image = QPixmap(self.image_paths[self.image_index])
        #resize_width = min(image.width(), self.screen.width()*0.8)
        objid = self.object_ids[self.image_index]
        attribute_type = self.objects_map.loc[ self.objects_map["object_id"] == objid, self.attribute_name ]
        attribute_type = None if attribute_type.isna().iloc[0] else attribute_type.iloc[0]
        attribute_type_str = "not annotated yet" if attribute_type is None else attribute_type
        attribute_type_color = 'color:red;' if attribute_type is None else 'color:green;'
        self.text.setText(f"<b>Object ID</b>: <p style={attribute_type_color}>{objid}</p> <b>{self.attribute_name}</b>: <p style={attribute_type_color}>{attribute_type_str}</p>")

        resize_width = 1000
        resize_height = int(min(image.height(), self.screen.height()*0.8))
        image = image.scaled(resize_width, resize_height, Qt.KeepAspectRatio)
        self.image.setPixmap(image)
        self.image.resize(resize_width, resize_height)
        self.show()

if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--path-to-geojson', type=str, required=True, help='Path to the geojson')
    parser.add_argument('--path-to-detection', type=str, required=True, help='Relative path to the json files')
    parser.add_argument('--attribute-name', type=str, required=True, help='The name of the attribute that you want to annotate')
    parser.add_argument('--outdir', type=str, required=False, help='Path to the output directory')

    args = parser.parse_args()

    app = QApplication(sys.argv)
    viewer = ObjectAnnotator(args.path_to_geojson, args.path_to_detection, args.outdir, args.attribute_name)
    viewer.show()
    app.exec()