#!/usr/bin/env python3
import io
import logging
import socketserver
import sys
import threading
from threading import Condition
from http import server
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import socket

# Get Raspberry Pi's IP dynamically
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PAGE = f"""
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

# Streaming Output Class
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

# HTTP Request Handler
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
                logging.warning('Removed streaming client %s: %s', self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

# HTTP Server
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Motor Control Function
def motor_control():
    # Define Motor A Pins
    in1, in2, en1 = 24, 23, 25
    # Define Motor B Pins
    in3, in4, en2 = 17, 27, 22

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en1, GPIO.OUT)
    GPIO.setup(in3, GPIO.OUT)
    GPIO.setup(in4, GPIO.OUT)
    GPIO.setup(en2, GPIO.OUT)

    # Set Motors to Forward Motion
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)

    # Setup PWM for Speed Control
    pwm1 = GPIO.PWM(en1, 1000)
    pwm2 = GPIO.PWM(en2, 1000)
    pwm1.start(50)  # Medium Speed
    pwm2.start(50)  # Medium Speed
    
    logging.info("Motors running at medium speed...")
    try:
        while True:
            pass  # Keep running indefinitely
    except KeyboardInterrupt:
        GPIO.cleanup()
        logging.info("Motor Control Stopped.")

# Main Function: Start Streaming & Motor in Parallel
def main():
    try:
        # Start Camera Streaming
        picam2 = Picamera2()
        video_config = picam2.create_video_configuration(main={"size": (640, 480)})
        picam2.configure(video_config)
        picam2.start()
        
        # Set up the output
        global output
        output = StreamingOutput()
        encoder = JpegEncoder(q=70)
        picam2.start_encoder(encoder, FileOutput(output))

        # Start Motor Control in a Separate Thread
        motor_thread = threading.Thread(target=motor_control, daemon=True)
        motor_thread.start()

        # Start Server for Camera Streaming
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        logging.info(f"Server started. Access stream at http://{ip_address}:8000")
        server.serve_forever()

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        sys.exit(1)
    finally:
        try:
            picam2.stop_encoder()
            picam2.stop()
        except:
            pass
        GPIO.cleanup()

if __name__ == "__main__":
    main()
