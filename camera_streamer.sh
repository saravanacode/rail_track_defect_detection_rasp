#!/bin/bash
# gstreamer_server.sh - Run this on your Raspberry Pi

# Make sure the script is executable: chmod +x gstreamer_server.sh

# Display the Pi's IP address for reference
echo "Your Raspberry Pi's IP address is:"
hostname -I

# Set resolution and framerate variables
WIDTH=640
HEIGHT=480
FRAMERATE=30

# Option 1: Using v4l2 with omxh264enc (hardware encoder for Raspberry Pi)
# This should work on older Raspberry Pi models (3 and earlier)
gst-launch-1.0 -v v4l2src device=/dev/video0 ! \
    video/x-raw,width=$WIDTH,height=$HEIGHT,framerate=$FRAMERATE/1 ! \
    videoconvert ! omxh264enc control-rate=variable target-bitrate=800000 ! \
    h264parse ! rtph264pay config-interval=1 pt=96 ! \
    udpsink host=0.0.0.0 port=5000
