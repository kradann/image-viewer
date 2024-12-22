import os
import numpy as np
from glob import glob
import cv2
from tqdm import tqdm

image_dict = dict()

"""def get_image(img_path):
	if img_path not in image_dict:
		image_dict[img_path] = cv2.imread(img_path)
	return image_dict[img_path]"""

image_path_list = sorted(glob("/home/krezsnely/PycharmProjects/all_images/*.jpg"))
for index in tqdm(range(len(image_path_list)-1)):
	image1 = cv2.imread(image_path_list[index])
	for index2 in range(index+1, len(image_path_list)):
		image2 = cv2.imread(image_path_list[index2])
		if image1.shape == image2.shape and (image1 == image2).all():
			print(image_path_list[index])
			print(image_path_list[index2])
			print()

