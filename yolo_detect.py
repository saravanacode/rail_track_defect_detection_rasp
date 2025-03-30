import os
import sys
import time

import cv2
import numpy as np
from ultralytics import YOLO

# Fixed parameters
model_path = "yolo11n_ncnn_model"
img_source = "picamera0"
min_thresh = 0.5
resW, resH = 320, 240  # Lowest reasonable resolution

# Check if model file exists and is valid
if (not os.path.exists(model_path)):
    print('ERROR: Model path is invalid or model was not found. Make sure the model filename was entered correctly.')
    sys.exit(0)

# Load the model into memory and get labelmap
model = YOLO(model_path, task='detect')
labels = model.names

# Set source type to picamera
source_type = 'picamera'
picam_idx = 0

# Set up picamera
from picamera2 import Picamera2
cap = Picamera2()
cap.configure(cap.create_video_configuration(main={"format": 'XRGB8888', "size": (resW, resH)}))
cap.start()

# Set bounding box colors (using the Tableu 10 color scheme)
bbox_colors = [(164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106), 
              (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)]

# Initialize control and status variables
avg_frame_rate = 0
frame_rate_buffer = []
fps_avg_len = 200

# Begin inference loop
while True:

    t_start = time.perf_counter()

    # Grab frames using picamera interface
    frame_bgra = cap.capture_array()
    frame = cv2.cvtColor(np.copy(frame_bgra), cv2.COLOR_BGRA2BGR)
    if (frame is None):
        print('Unable to read frames from the Picamera. This indicates the camera is disconnected or not working. Exiting program.')
        break

    # Run inference on frame
    results = model(frame, verbose=False)

    # Extract results
    detections = results[0].boxes

    # Initialize variable for basic object counting
    object_count = 0

    # Go through each detection and get bbox coords, confidence, and class
    for i in range(len(detections)):

        # Get bounding box coordinates
        xyxy_tensor = detections[i].xyxy.cpu()
        xyxy = xyxy_tensor.numpy().squeeze()
        xmin, ymin, xmax, ymax = xyxy.astype(int)

        # Get bounding box class ID and name
        classidx = int(detections[i].cls.item())
        classname = labels[classidx]

        # Get bounding box confidence
        conf = detections[i].conf.item()

        # Draw box if confidence threshold is high enough
        if conf > min_thresh:

            color = bbox_colors[classidx % 10]
            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)

            label = f'{classname}: {int(conf*100)}%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_ymin = max(ymin, labelSize[1] + 10)
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), color, cv2.FILLED)
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # Count objects
            object_count = object_count + 1

    # Calculate and draw framerate
    cv2.putText(frame, f'FPS: {avg_frame_rate:0.2f}', (10,20), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)
    
    # Display detection results
    cv2.putText(frame, f'Number of objects: {object_count}', (10,40), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,255,255), 2)
    cv2.imshow('YOLO detection results', frame)

    key = cv2.waitKey(5)
    
    if key == ord('q') or key == ord('Q'):  # Press 'q' to quit
        break
    elif key == ord('s') or key == ord('S'):  # Press 's' to pause inference
        cv2.waitKey()
    elif key == ord('p') or key == ord('P'):  # Press 'p' to save a picture of results on this frame
        cv2.imwrite('capture.png', frame)
    
    # Calculate FPS for this frame
    t_stop = time.perf_counter()
    frame_rate_calc = float(1/(t_stop - t_start))

    # Append FPS result to frame_rate_buffer
    if len(frame_rate_buffer) >= fps_avg_len:
        temp = frame_rate_buffer.pop(0)
        frame_rate_buffer.append(frame_rate_calc)
    else:
        frame_rate_buffer.append(frame_rate_calc)

    # Calculate average FPS for past frames
    avg_frame_rate = np.mean(frame_rate_buffer)

# Clean up
print(f'Average pipeline FPS: {avg_frame_rate:.2f}')
cap.stop()
cv2.destroyAllWindows()
