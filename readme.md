Install the required packages:
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
                   gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly

Save the gstreamer_server.sh script to your Raspberry Pi
Make it executable:
chmod +x gstreamer_server.sh

Run the server script:
./gstreamer_server.sh




sudo apt install -y gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad gstreamer1.0-libav
raspivid -fps 26 -h 450 -w 600 -vf -n -t 0 -b 200000 -o - | gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 ! gdppay ! tcpserversink host=192.168.1.9 port=5000




libcamera-vid -t 0 --width 600 --height 450 --framerate 26 --inline --listen -o - | \
gst-launch-1.0 -v fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 ! gdppay ! \
tcpserversink host=192.168.1.9 port=5000




git clone https://github.com/mastersubhajit/video_streaming_with_raspberry_pi_camera_module.git

