from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout

eu_sign_types = [
    "delete",
    "canceled",
    "unknown_sign",
    "eu_speedlimit_5",
    "eu_speedlimit_10",
    "eu_speedlimit_15",
    "eu_speedlimit_20",
    "eu_speedlimit_25",
    "eu_speedlimit_30",
    "eu_speedlimit_40",
    "eu_speedlimit_50",
    "eu_speedlimit_60",
    "eu_speedlimit_70",
    "eu_speedlimit_80",
    "eu_speedlimit_90",
    "eu_speedlimit_100",
    "eu_speedlimit_110",
    "eu_speedlimit_120",
    "eu_speedlimit_130",
    "eu_end_of_speedlimit_5",
    "eu_end_of_speedlimit_10",
    "eu_end_of_speedlimit_20",
    "eu_end_of_speedlimit_30",
    "eu_end_of_speedlimit_40",
    "eu_end_of_speedlimit_50",
    "eu_end_of_speedlimit_60",
    "eu_end_of_speedlimit_70",
    "eu_end_of_speedlimit_80",
    "eu_end_of_speedlimit_90",
    "eu_end_of_speedlimit_100",
    "eu_end_of_speedlimit_110",
    "eu_end_of_speedlimit_120",
    "eu_end_of_speedlimit_130",
    "eu_zone_of_speedlimit_10",
    "eu_zone_of_speedlimit_20",
    "eu_zone_of_speedlimit_30",
    "eu_zone_of_speedlimit_40",
    "eu_zone_of_speedlimit_50",
    "eu_zone_of_speedlimit_60",
    "eu_end_of_zone_of_speedlimit_10",
    "eu_end_of_zone_of_speedlimit_20",
    "eu_end_of_zone_of_speedlimit_30",
    "eu_end_of_zone_of_speedlimit_40",
    "eu_end_of_zone_of_speedlimit_50",
    "eu_end_of_zone_of_speedlimit_60",
    "eu_minimum_speed_30",
    "eu_minimum_speed_40",
    "eu_minimum_speed_50",
    "eu_minimum_speed_60",
    "eu_minimum_speed_70",
    "eu_minimum_speed_80",
    "eu_minimum_speed_90",
    "eu_minimum_speed_100",
    "eu_minimum_speed_110",
    "eu_minimum_speed_120",
    "eu_minimum_speed_130",
    "eu_end_of_eu_minimum_speed_30",
    "eu_end_of_eu_minimum_speed_40",
    "eu_end_of_eu_minimum_speed_50",
    "eu_end_of_eu_minimum_speed_60",
    "eu_end_of_eu_minimum_speed_70",
    "eu_end_of_eu_minimum_speed_80",
    "eu_end_of_eu_minimum_speed_90",
    "eu_end_of_eu_minimum_speed_100",
    "eu_end_of_eu_minimum_speed_110",
    "eu_end_of_eu_minimum_speed_120",
    "eu_end_of_eu_minimum_speed_130",

    "eu_overtaking_not_allowed",
    "eu_overtaking_not_allowed_by_trucks",
    "eu_end_of_restrictions",
    "eu_end_of_overtaking_restriction",
    "eu_end_of_overtaking_by_trucks_restriction",
    "eu_city_limit_entry",
    "eu_city_limit_exit",
    "eu_residential_area",
    "eu_end_of_residential_area",
    "eu_motorway",
    "eu_end_of_motorway",
    "eu_highway",
    "eu_end_of_highway",

    "eu_additional_vehicle_car",
    "eu_additional_vehicle_truck",
    "eu_additional_vehicle_other",
    "eu_additional_hazardous",
    "eu_additional_rain",
    "eu_additional_snow",
    "eu_additional_rainsnow",
    "eu_additional_wet_road",
    "eu_additional_day_night",
    "eu_additional_arrow_to_exit",
    "eu_additional_validity_ends_a",
    "eu_additional_validity_ends_b",
    "eu_additional_validity_ends_c",
    "eu_additional_validity_ends_d",
    "eu_additional_stop_in_dist",
    "eu_additional_dist",
    "eu_additional_timeframe",
    "eu_additional_weight",
    "eu_additional_school",
    "eu_additional_zone",
    "eu_additional_zone_end",
    "eu_additional_tree",
    "eu_additional_except_cars",
    "eu_additional_except_trucks",
    "eu_additional_except_others",
    "eu_additional_other",

    "eu_warning_of_curve",
    "eu_warning_of_double_curve",
    "eu_warning_of_cattle",
    "eu_warning_of_animals",
    "eu_warning_of_wind",
    "eu_warning_of_skidding",
    "eu_warning_of_bikes",
    "eu_warning_of_trains",
    "eu_warning_of_pedestrian_crossing",
    "eu_warning_of_pedestrians",
    "eu_warning_of_children",
    "eu_warning_of_slope",
    "eu_warning_of_traffic_jam",
    "eu_warning_of_roundabouts",
    "eu_warning_of_crossing",
    "eu_warning_of_ice",
    "eu_warning_of_tunnel",
    "eu_warning_of_two_way",
    "eu_warning_of_traffic_lights",
    "eu_warning_of_draw_bridge",
    "eu_warning_of_frogs",
    "eu_warning_of_planes",
    "eu_warning_of_gravel",
    "eu_warning_of_trees",
    "eu_warning_of_pier",
    "eu_warning_of_accidents",

    "eu_no_entry",
    "eu_no_hazardous_material",
    "eu_no_water_pollutants",
    "eu_no_turning",
    "eu_no_stop_no_park",
    "eu_no_parking",

    "eu_dir_sign_diagonal",
    "eu_dir_sign_side",
    "eu_dir_sign_curve",
    "eu_dir_sign_up",

    "eu_axle_weight_restriction",
    "eu_weight_restriction",
    "eu_height_restriction",
    "eu_length_restriction",
    "eu_width_restriction",

    "eu_roadworks",
    "eu_pedestrian_crossing",
    "eu_rock_slides",
    "eu_merging_lane",
    "eu_road_constriction",
    "eu_road_bump",
    "eu_road_closed",

    "eu_minimal_distance",
    "eu_minimal_distance_trucks",

    "eu_hazardous_material_allowed",
    "eu_water_pollutants_allowed",
    "eu_giveway",
    "eu_stop",
    "eu_priority_crossing_ahead",
    "eu_yield_to_right",
    "eu_priorityroad_ahead",
    "eu_priorityroad_ends",

    "eu_dangerous_situation",
    "eu_roundabout",

    "eu_one_way_street",
    "eu_priority_over_oncoming_traffic",
    "eu_priority_for_oncoming_traffic",

    "eu_direction_position_indication_unknown",
    "eu_blue_ground_circle_unknown",
    "eu_blue_ground_rectangle_unknown",
    "eu_blue_border_rectangle_unknown",
    "eu_red_border_circle_unknown",
    "eu_red_border_up_triangle_unknown",
    "eu_white_ground_rectangle",
]

eu_sign_types.sort()

us_sign_types = [
    "delete",
    "canceled",
    "unknown_sign",
    "us_stop",
    "us_stop_for_pedestrians",
    "us_giveway",
    "us_giveway_to_pedestrians",
    "us_roadworks",
    "us_roadworks_end",
    "us_pedestrian_crossing",
    "us_roundabout",
]
for number in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_{}".format(number))
    us_sign_types.append("us_speedlimit_trucks_{}".format(number))
    us_sign_types.append("us_speedlimit_night_{}".format(number))
    us_sign_types.append("us_speedlimit_advisory_{}".format(number))
    us_sign_types.append("us_speedlimit_temporary_{}".format(number))
    us_sign_types.append("us_minimum_speed_{}".format(number))

us_sign_types.sort()

class SignTypeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose sign type")
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.selected_type = None

        # Gombok
        self.eu = QPushButton("Eu sign types")
        self.us = QPushButton("US sign types")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.eu)
        layout.addWidget(self.us)
        self.setLayout(layout)

        # Események
        self.eu.clicked.connect(self.first_clicked)
        self.us.clicked.connect(self.second_clicked)


    def first_clicked(self):
        self.selected_type =  eu_sign_types
        self.accept()

    def second_clicked(self):
        self.selected_type =  us_sign_types
        self.accept()