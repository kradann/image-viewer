from PyQt5 import QtWidgets, QtCore, QtGui
import os
from PyQt5.QtWidgets import QPushButton

sign_types = ["eu_speedlimit_100",
              "eu_speedlimit_110",
              "eu_speedlimit_120",
              "eu_speedlimit_130",
              "eu_speedlimit_30",
              "eu_speedlimit_40",
              "eu_speedlimit_50",
              "eu_speedlimit_60",
              "eu_speedlimit_70",
              "eu_speedlimit_80",
              "eu_speedlimit_90",
              "eu_overtaking_not_allowed",
              "eu_overtaking_not_allowed_by_trucks",
              "eu_end_of_restrictions",
              "eu_end_of_overtaking_restriction",
              "eu_end_of_overtaking_by_trucks_restriction",
              "eu_end_of_speedlimit_100",
              "eu_end_of_speedlimit_110",
              "eu_end_of_speedlimit_120",
              "eu_end_of_speedlimit_130",
              "eu_end_of_speedlimit_30",
              "eu_end_of_speedlimit_40",
              "eu_end_of_speedlimit_50",
              "eu_end_of_speedlimit_60",
              "eu_end_of_speedlimit_70",
              "eu_end_of_speedlimit_80",
              "eu_end_of_speedlimit_90",
              "eu_zone_of_speedlimit_20",
              "eu_zone_of_speedlimit_30",
              "eu_zone_of_speedlimit_40",
              "eu_end_of_zone_of_speedlimit_20",
              "eu_end_of_zone_of_speedlimit_30",
              "eu_end_of_zone_of_speedlimit_40",
              "eu_minimum_speed_100",
              "eu_minimum_speed_110",
              "eu_minimum_speed_120",
              "eu_minimum_speed_130",
              "eu_minimum_speed_30",
              "eu_minimum_speed_40",
              "eu_minimum_speed_50",
              "eu_minimum_speed_60",
              "eu_minimum_speed_70",
              "eu_minimum_speed_80",
              "eu_minimum_speed_90",
              "eu_end_of_eu_minimum_speed_100",
              "eu_end_of_eu_minimum_speed_110",
              "eu_end_of_eu_minimum_speed_120",
              "eu_end_of_eu_minimum_speed_130",
              "eu_end_of_eu_minimum_speed_30",
              "eu_end_of_eu_minimum_speed_40",
              "eu_end_of_eu_minimum_speed_50",
              "eu_end_of_eu_minimum_speed_60",
              "eu_end_of_eu_minimum_speed_70",
              "eu_end_of_eu_minimum_speed_80",
              "eu_end_of_eu_minimum_speed_90",
              "eu_city_limit_entry",
              "eu_city_limit_exit",
              "eu_residential_area",
              "eu_end_of_residential_area",
              "eu_no_entry",
              "eu_road_closed",
              "eu_axle_weight_restriction",
              "eu_weight_restriction",
              "eu_height_restriction",
              "eu_length_restriction",
              "eu_width_restriction",
              "eu_minimal_distance",
              "eu_minimal_distance_trucks",
              "eu_no_hazardous_material",
              "eu_hazardous_material_allowed",
              "eu_no_water_pollutants",
              "eu_water_pollutants_allowed",
              "eu_giveway",
              "eu_stop",
              "eu_priority_crossing_ahead",
              "eu_yield_to_right",
              "eu_priorityroad_ahead",
              "eu_priorityroad_ends",
              "eu_motorway",
              "eu_end_of_motorway",
              "eu_highway",
              "eu_end_of_highway",
              "eu_dangerous_situation",
              "eu_warning_of_curve",
              "eu_warning_of_double_curve",
              "eu_warning_of_cattle",
              "eu_warning_of_animals",
              "eu_road_constriction",
              "eu_road_bump",
              "eu_warning_of_wind",
              "eu_roadworks",
              "eu_warning_of_skidding",
              "eu_warning_of_bikes",
              "eu_warning_of_trains",
              "eu_warning_of_pedestrian_crossing",
              "eu_warning_of_pedestrians",
              "eu_warning_of_children",
              "eu_pedestrian_crossing",
              "eu_warning_of_slope",
              "eu_warning_of_traffic_jam",
              "eu_warning_of_roundabouts",
              "eu_warning_of_crossing",
              "eu_warning_of_ice",
              "eu_height_restriction",
              "eu_warning_of_tunnel",
              "eu_warning_of_two_way",
              "eu_warning_of_traffic_lights",
              "eu_warning_of_draw_bridge",
              "eu_warning_of_frogs",
              "eu_warning_of_planes",
              "eu_warning_of_gravel",
              "eu_warning_of_trees",
              "eu_rock_slides",
              "eu_merging_lane",
              "eu_warning_of_pier",
              "eu_warning_of_accidents",
              "eu_dir_sign_diagonal",
              "eu_roundabout",
              "eu_dir_sign_side",
              "eu_dir_sign_curve",
              "eu_dir_sign_up",
              "eu_one_way_street",
              "eu_oncoming_precedence",
              "eu_precedence_over_oncoming",
              "eu_no_turning",
              "eu_additional_vehicle_a",
              "eu_additional_vehicle_b",
              "eu_additional_hazardous",
              "eu_additional_rain",
              "eu_additional_snow",
              "eu_additional_rainsnow",
              "eu_additional_wet_road",
              "eu_additional_day_night",
              "eu_additional_arrow_to_exit",
              "eu_additiona_validity_ends_a",
              "eu_additiona_validity_ends_b",
              "eu_additiona_validity_ends_c",
              "eu_additiona_validity_ends_d",
              "eu_additional_stop_in_dist",
              "eu_additional_dist",
              "eu_additional_timeframe",
              "eu_additional_weight",
              "eu_additional_school",
              "eu_additional_zone",
              "eu_additional_tree",
              "eu_additional_trucks",
              "eu_additional_other",
              "eu_direction_position_indication_unknown",
              "eu_blue_ground_circle_unknown",
              "eu_blue_ground_rectangle_unknown",
              "eu_blue_border_rectangle_unknown",
              "eu_red_border_circle_unknown",
              "eu_red_border_up_triangle_unknown",
              "eu_white_ground_rectangle"]

sign_types.sort()

class FolderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, preffered=None):
        super().__init__(parent)
        self.setWindowTitle("Select Subfolder")
        self.setMinimumSize(400, 500)

        layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(sign_types)
        layout.addWidget(self.list_widget)
        items = self.list_widget.findItems(preffered, QtCore.Qt.MatchExactly)
        if items:
            item = items[0]
            row = self.list_widget.row(item)
            take = self.list_widget.takeItem(row)
            self.list_widget.insertItem(0,take)
            take.setBackground(QtGui.QColor(0, 120, 215, 180))


        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.selected_folder = None
        self.list_widget.itemDoubleClicked.connect(self.accept)

    def accept(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.selected_folder = selected_item.text()
        super().accept()
