import time
import cv2
import numpy as np
from picamera2 import Picamera2

def main():
    # Resolution - using a low resolution for better performance
    resW, resH = 320, 240
    
    # Set up picamera
    cap = Picamera2()
    cap.configure(cap.create_video_configuration(main={"format": 'XRGB8888', "size": (resW, resH)}))
    cap.start()
    
    # Initialize variables for FPS calculation
    fps_avg_len = 30  # Number of frames to average for FPS calculation
    frame_rate_buffer = []
    avg_frame_rate = 0
    
    print("Camera opened. Press 'q' to quit.")
    
    # Main loop
    while True:
        # Start timing for FPS calculation
        t_start = time.perf_counter()
        
        # Capture frame from picamera
        frame_bgra = cap.capture_array()
        frame = cv2.cvtColor(np.copy(frame_bgra), cv2.COLOR_BGRA2BGR)
        
        if frame is None:
            print("Unable to read frames from the Picamera. Camera might be disconnected.")
            break
        
        # Draw FPS on frame
        cv2.putText(frame, f'FPS: {avg_frame_rate:.2f}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Display the frame
        cv2.imshow('Camera Feed', frame)
        
        # Wait for a key press (1ms) - this keeps the window responsive
        key = cv2.waitKey(1)
        if key == ord('q') or key == ord('Q'):
            break
            
        # Calculate FPS
        t_stop = time.perf_counter()
        frame_rate_calc = 1.0 / (t_stop - t_start)
        
        # Update FPS buffer and calculate average
        if len(frame_rate_buffer) >= fps_avg_len:
            frame_rate_buffer.pop(0)
        frame_rate_buffer.append(frame_rate_calc)
        avg_frame_rate = np.mean(frame_rate_buffer)

    # Clean up
    print(f'Average FPS: {avg_frame_rate:.2f}')
    cap.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
