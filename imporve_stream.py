#!/usr/bin/env python3
import io
import logging
import socketserver
import subprocess
import sys
import time
import os
import signal
from threading import Condition
from http import server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Import Picamera2 libraries
try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
except ImportError:
    logging.error("Could not import Picamera2 libraries")
    sys.exit(1)

# Determine the Raspberry Pi's IP address dynamically
import socket
hostname = socket.gethostname()
try:
    ip_address = socket.gethostbyname(hostname)
except:
    ip_address = "localhost"
    logging.warning("Could not determine IP address, using localhost")

# Define HTML page
PAGE = f"""\
<!DOCTYPE html>
<html>
  <head>
    <title>Raspberry Pi Video Streaming</title>
  </head>
  <body>
    <h1>Raspberry Pi Video Stream</h1>
    <img src="stream.mjpg" width="640" height="480" />
  </body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()
    
    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def kill_existing_camera_processes():
    """Kill any processes that might be using the camera"""
    try:
        # Find processes using the camera by searching for libcamera
        result = subprocess.run(
            ['pgrep', '-f', 'libcamera'], 
            capture_output=True, 
            text=True
        )
        
        # Get the current process ID to avoid killing ourselves
        current_pid = os.getpid()
        
        if result.returncode == 0:
            for pid in result.stdout.strip().split('\n'):
                pid = int(pid)
                # Don't kill our own process
                if pid != current_pid:
                    logging.info(f"Killing process {pid} that may be using the camera")
                    try:
                        os.kill(pid, signal.SIGTERM)
                        # Give it a moment to shut down
                        time.sleep(1)
                    except ProcessLookupError:
                        pass
    except Exception as e:
        logging.error(f"Error killing camera processes: {e}")

def init_camera():
    """Initialize the camera with retry mechanism"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Try to initialize the camera
            picam2 = Picamera2()
            video_config = picam2.create_video_configuration(main={"size": (640, 480)})
            picam2.configure(video_config)
            picam2.start()
            return picam2
        except RuntimeError as e:
            logging.warning(f"Failed to initialize camera (attempt {retry_count+1}/{max_retries}): {e}")
            
            # First try to release any existing camera processes
            kill_existing_camera_processes()
            
            # Wait before retrying
            time.sleep(2)
            retry_count += 1
    
    # If we get here, we've failed to initialize after retries
    logging.error("Failed to initialize camera after multiple attempts")
    sys.exit(1)

def main():
    # Initialize camera
    picam2 = init_camera()
    
    # Set up the output
    global output
    output = StreamingOutput()
    encoder = JpegEncoder(q=70)  # Quality set to 70 for better performance
    
    try:
        # Start recording
        picam2.start_encoder(encoder, FileOutput(output))
        
        # Start server
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        logging.info(f"Server started. Access stream at http://{ip_address}:8000")
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    finally:
        # Cleanup
        logging.info("Shutting down camera")
        try:
            picam2.stop_encoder()
            picam2.stop()
        except Exception as e:
            logging.error(f"Error shutting down camera: {e}")

if __name__ == "__main__":
    main()
