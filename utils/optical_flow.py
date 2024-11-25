import cv2
import numpy as np

def get_image_path(_id):
    return "/home/ad.adasworks.com/levente.peto/projects/traffic_sign_classification/outputs/AID-5081_vol2_cut_images_padded/6_eu_end_of_restrictions_000097{}.jpg".format(_id)

def get_new_corners(_frame1, _frame2):
    corners = cv2.goodFeaturesToTrack(_frame1, maxCorners=100, qualityLevel=0.3, minDistance=7)
    _new_corners, _status, error = cv2.calcOpticalFlowPyrLK(_frame1, _frame2, corners, None)
    return _new_corners, _status


for image_id in range(0, 9):
    frame1 = cv2.imread(get_image_path(image_id), cv2.IMREAD_GRAYSCALE)
    frame2 = cv2.imread(get_image_path(image_id + 1), cv2.IMREAD_GRAYSCALE)


# Megjelenítés
frame1_color = cv2.cvtColor(frame1, cv2.COLOR_GRAY2BGR)
for i, (new, old) in enumerate(zip(corners[status == 1], new_corners[status == 1])):
    a, b = new.ravel()
    c, d = old.ravel()
    print((int(a), int(b)), (int(c), int(d)))
    cv2.line(frame1_color, (int(a), int(b)), (int(c), int(d)), (0, 255, 0), 2)
    cv2.circle(frame1_color, (int(a), int(b)), 2, (0, 0, 255), -1)

cv2.imshow("Lucas-Kanade Optical Flow", frame1_color)
cv2.waitKey(0)
cv2.destroyAllWindows()