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

# For Raspberry Pi Camera Module (using v4l2src)
gst-launch-1.0 -v v4l2src device=/dev/video0 ! \
    video/x-raw,width=$WIDTH,height=$HEIGHT,framerate=$FRAMERATE/1 ! \
    videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! \
    rtph264pay config-interval=1 pt=96 ! \
    udpsink host=0.0.0.0 port=5000

# Alternatively, if using the older camera interface (rpicamsrc)
# Uncomment this and comment out the above if needed
# gst-launch-1.0 -v rpicamsrc preview=false ! \
#     video/x-h264,width=$WIDTH,height=$HEIGHT,framerate=$FRAMERATE/1 ! \
#     h264parse ! rtph264pay config-interval=1 pt=96 ! \
#     udpsink host=0.0.0.0 port=5000
