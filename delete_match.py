import json
import os.path
import pprint

try:
	with open("/home/krezsnely/PycharmProjects/image-viewer/data/match.json", 'r') as file:
		data = json.load(file)
	folder_path = "/home/krezsnely/PycharmProjects/all_images"
	folder = set(os.listdir(folder_path))
	match_list = data.get("match_list", [])
	for match in match_list:
		file1 = os.path.basename(match[0])
		file2 = os.path.basename(match[1])

		if file1 in folder and file2 in folder:
			file_to_delete = os.path.join(folder_path, file2)
			pprint.pprint(file_to_delete)
			try:
				#os.remove(file_to_delete)

				if os.path.exists(file_to_delete):
					print(1)
			except Exception as e:
				print(e)


except Exception as e:
	print(e)

