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
