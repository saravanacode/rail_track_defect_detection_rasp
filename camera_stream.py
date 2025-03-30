import time
import cv2
import numpy as np
import socket
import pickle
import struct
from picamera2 import Picamera2

def main():
    # Get the Raspberry Pi's IP address (you'll need this for the client)
    hostname = socket.gethostname()
    server_ip = socket.gethostbyname(hostname)
    print(f"Server IP address: {server_ip}")
    
    # Resolution - using a low resolution for better network performance
    resW, resH = 320, 240
    
    # Set up picamera
    cap = Picamera2()
    cap.configure(cap.create_video_configuration(main={"format": 'XRGB8888', "size": (resW, resH)}))
    cap.start()
    
    # Initialize variables for FPS calculation
    fps_avg_len = 30
    frame_rate_buffer = []
    avg_frame_rate = 0
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 8485
    socket_address = ('0.0.0.0', port)  # Listen on all available interfaces
    
    # Socket settings
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(socket_address)
    server_socket.listen(5)
    print(f"Listening on port {port}...")
    
    # Accept client connection
    client_socket, addr = server_socket.accept()
    print(f"Connection from: {addr}")
    
    try:
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
            
            # Optional: Display frame locally on Raspberry Pi
            # cv2.imshow('Server Feed', frame)
            
            # Compress the frame to save bandwidth (JPEG encoding)
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            
            # Serialize frame
            data = pickle.dumps(buffer)
            
            # Send message length first
            message_size = struct.pack("L", len(data))
            
            # Send data
            try:
                client_socket.sendall(message_size + data)
            except:
                print("Connection lost")
                break
            
            # Calculate FPS
            t_stop = time.perf_counter()
            frame_rate_calc = 1.0 / (t_stop - t_start)
            
            # Update FPS buffer and calculate average
            if len(frame_rate_buffer) >= fps_avg_len:
                frame_rate_buffer.pop(0)
            frame_rate_buffer.append(frame_rate_calc)
            avg_frame_rate = np.mean(frame_rate_buffer)
            
            # Optional: Handle local key presses if showing locally
            # key = cv2.waitKey(1) & 0xFF
            # if key == ord('q'):
            #     break
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    
    finally:
        # Clean up
        print(f'Average FPS: {avg_frame_rate:.2f}')
        cap.stop()
        # cv2.destroyAllWindows()
        client_socket.close()
        server_socket.close()
        print("Server shut down")

if __name__ == "__main__":
    main()
