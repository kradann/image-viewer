eu_sign_types = [
    "back_of_sign",
    "not_a_sign",
    "unknown_sign",
    "eu_additional_panel",
    "eu_blue_ground_circle_unknown",
    "eu_blue_ground_rectangle_unknown",
    "eu_blue_border_rectangle_unknown",
    "eu_city_limit_entry",
    "eu_city_limit_exit",
    "eu_direction_position_indication_unknown",
    "eu_end_of_overtaking_by_trucks_restriction",
    "eu_end_of_overtaking_restriction",
    "eu_end_of_restrictions",
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
    "eu_end_of_zone_of_speedlimit_20",
    "eu_end_of_zone_of_speedlimit_30",
    "eu_end_of_zone_of_speedlimit_40",
    "eu_giveway",
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
    "eu_noentry",
    "eu_noparking",
    "eu_nostop_nopark",
    "eu_overtaking_not_allowed",
    "eu_overtaking_not_allowed_by_trucks",
    "eu_pedestrian_crossing",
    "eu_priority_for_oncoming_traffic",
    "eu_priority_over_oncoming_traffic",
    "eu_priorityroad_ahead",
    "eu_priorityroad_ends",
    "eu_red_border_circle_unknown",
    "eu_red_border_up_triangle_unknown",
    "eu_road_closed",
    "eu_roadworks",
    "eu_roundabout",
    "eu_speedlimit_100",
    "eu_speedlimit_110",
    "eu_speedlimit_120",
    "eu_speedlimit_130",
    "eu_speedlimit_5",
    "eu_speedlimit_10",
    "eu_speedlimit_20",
    "eu_speedlimit_30",
    "eu_speedlimit_40",
    "eu_speedlimit_50",
    "eu_speedlimit_60",
    "eu_speedlimit_70",
    "eu_speedlimit_80",
    "eu_speedlimit_90",
    "eu_stop",
    "eu_white_ground_rectangle",
    "eu_zone_of_speedlimit_20",
    "eu_zone_of_speedlimit_30",
    "eu_zone_of_speedlimit_40",
]

us_sign_types = [
    "back_of_sign",
    "not_a_sign",
    "unknown_sign",
    "us_hov",
    "us_hov_end",
    "us_yield",
    "us_yield_to_pedestrians",
    "us_stop",
    "us_stop_for_pedestrians",
    "us_no_entry",
    "us_no_passing",
    "us_roadworks",
    "us_roadworks_end",
    "us_roundabout",
    "us_white_ground_rectangle_unknown",
    "us_yellow_ground_rectangle_unknown",
    "us_orange_ground_rectangle_unknown",
    "us_yellow_ground_diamond_unknown",
    "us_orange_ground_diamond_unknown",
]

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_{}".format(speed_limit))

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_minimum_speed_{}".format(speed_limit))

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_trucks_{}".format(speed_limit))

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_night_{}".format(speed_limit))

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_advisory_{}".format(speed_limit))

for speed_limit in range(5, 125, 5):
    us_sign_types.append("us_speedlimit_temporary_{}".format(speed_limit))


if "__main__" == __name__:
    from pprint import pprint
    us_signs_dict = {idx: us_sign for idx, us_sign in enumerate(us_sign_types)}

    for idx, us_sign in enumerate(eu_sign_types + us_sign_types):
        print("\"{}\": \"{}\",".format(idx, us_sign))

