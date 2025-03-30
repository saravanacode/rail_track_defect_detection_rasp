#!/usr/bin/env python3
import io
import logging
import socketserver
import time
import sys
from threading import Condition
from http import server

# Import Picamera2 libraries
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# Determine the Raspberry Pi's IP address dynamically
import socket
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def main():
    try:
        # Initialize and configure the camera
        picam2 = Picamera2()
        video_config = picam2.create_video_configuration(main={"size": (640, 480)})
        picam2.configure(video_config)
        picam2.start()
        
        # Set up the output
        global output
        output = StreamingOutput()
        encoder = JpegEncoder(q=70)  # Quality set to 70 for better performance
        
        # Start recording
        picam2.start_encoder(encoder, FileOutput(output))
        
        # Start server
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        logging.info(f"Server started. Access stream at http://{ip_address}:8000")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            picam2.stop_encoder()
            picam2.stop()
        except:
            pass

if __name__ == "__main__":
    main()
