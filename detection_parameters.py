import json
import cv2
import numpy as np

cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)

max_value = 255
max_value_H = 360//2
low_HSV = 0

detection_params_file = "detection_params.json"

"""
rango_detection = {
    "low":{
        "H":low_HSV,
        "S":low_HSV,
        "V":low_HSV
    },
    "high":{
        "H":max_value_H,
        "S":max_value,
        "V":max_value
    }
}
"""
with open(detection_params_file,"r") as f:
    rango_detection = json.loads(f.read())


window_capture_name = 'Video Capture'
window_detection_name = 'Object Detection'
low_H_name = 'Low H'
low_S_name = 'Low S'
low_V_name = 'Low V'
high_H_name = 'High H'
high_S_name = 'High S'
high_V_name = 'High V'

def on_low_H_thresh_trackbar(val):
    global rango_detection
    rango_detection['low']["H"] = val
    rango_detection['low']["H"] = min(rango_detection['high']["H"]-1, rango_detection['low']["H"])
    cv2.setTrackbarPos(low_H_name, window_detection_name, rango_detection['low']["H"])

def on_high_H_thresh_trackbar(val):
    global rango_detection
    rango_detection['high']["H"] = val
    rango_detection['high']["H"] = max(rango_detection['high']["H"], rango_detection['low']["H"]+1)
    cv2.setTrackbarPos(high_H_name, window_detection_name, rango_detection['high']["H"])

def on_low_S_thresh_trackbar(val):
    global rango_detection
    rango_detection['low']["S"] = val
    rango_detection['low']["S"] = min(rango_detection['high']["S"]-1, rango_detection['low']["S"])
    cv2.setTrackbarPos(low_S_name, window_detection_name, rango_detection['low']["S"])

def on_high_S_thresh_trackbar(val):
    global rango_detection
    rango_detection['high']["S"] = val
    rango_detection['high']["S"] = max(rango_detection['high']["S"], rango_detection['low']["S"]+1)
    cv2.setTrackbarPos(high_S_name, window_detection_name, rango_detection['high']["S"])

def on_low_V_thresh_trackbar(val):
    global rango_detection
    rango_detection['low']["V"] = val
    rango_detection['low']["V"] = min(rango_detection['high']["V"]-1, rango_detection['low']["V"])
    cv2.setTrackbarPos(low_V_name, window_detection_name, rango_detection['low']["V"])

def on_high_V_thresh_trackbar(val):
    global rango_detection
    rango_detection['high']["V"] = val
    rango_detection['high']["V"] = max(rango_detection['high']["V"], rango_detection['low']["V"]+1)
    cv2.setTrackbarPos(high_V_name, window_detection_name, rango_detection['high']["V"])

# parser = argparse.ArgumentParser(description='Code for Thresholding Operations using inRange tutorial.')
# parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
# args = parser.parse_args()
# cap = cv2.VideoCapture(args.camera)

cv2.namedWindow(window_capture_name)
cv2.namedWindow(window_detection_name)
cv2.createTrackbar(low_H_name, window_detection_name , rango_detection['low']["H"], max_value_H, on_low_H_thresh_trackbar)
cv2.createTrackbar(high_H_name, window_detection_name , rango_detection['high']["H"], max_value_H, on_high_H_thresh_trackbar)
cv2.createTrackbar(low_S_name, window_detection_name , rango_detection['low']["S"], max_value, on_low_S_thresh_trackbar)
cv2.createTrackbar(high_S_name, window_detection_name , rango_detection['high']["S"], max_value, on_high_S_thresh_trackbar)
cv2.createTrackbar(low_V_name, window_detection_name , rango_detection['low']["V"], max_value, on_low_V_thresh_trackbar)
cv2.createTrackbar(high_V_name, window_detection_name , rango_detection['high']["V"], max_value, on_high_V_thresh_trackbar)
while True:
    
    ret, frame = cap.read()
    if frame is None:
        break
    
    frame = cv2.flip(frame,1)
    frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    frame_threshold = cv2.inRange(frame_HSV, (rango_detection['low']["H"], rango_detection['low']["S"], rango_detection['low']["V"]), (rango_detection['high']["H"], rango_detection['high']["S"], rango_detection['high']["V"]))
    
    
    cv2.imshow(window_capture_name, frame)
    cv2.imshow(window_detection_name, frame_threshold)
    
    key = cv2.waitKey(30)
    if key == ord('q') or key == 27:
        break

    if key == ord('s'):
        # guardar los valores
        with open(detection_params_file,"w") as f:
            json.dump(rango_detection,f)
            print("Values Saved:",rango_detection)