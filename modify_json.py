import os
import json
from pprint import pprint

old_data = list()
old_electric_data = list()
with open("/home/krezsnely/PycharmProjects/eu_ts/electric_traffic_signs/traffic_sign_annotation.json", "r") as json_file:
    old_electric_data.extend(json.load(json_file))

with open("/home/krezsnely/PycharmProjects/eu_ts/traffic_signs_dataset/traffic_sign_annotation.json", "r") as json_file:
    old_data.extend(json.load(json_file))

with open("/home/krezsnely/PycharmProjects/eu_ts/traffic_signs_rikardo/traffic_sign_annotation.json", "r") as json_file:
    old_data.extend(json.load(json_file))

new_data = dict()

for annotation in old_data:
	new_data[annotation["image_name"]] = [annotation]
	new_data[annotation["image_name"]][0]["electric"] = False
	del new_data[annotation["image_name"]][0]["image_name"]

for annotation in old_electric_data:
	new_data[annotation["image_name"]] = [annotation]
	new_data[annotation["image_name"]][0]["electric"] = True
	del new_data[annotation["image_name"]][0]["image_name"]

with open("/home/krezsnely/PycharmProjects/traffic_sign_annotation.json", "w") as json_file:
	json.dump(new_data, json_file, indent=4)
pprint(new_data)