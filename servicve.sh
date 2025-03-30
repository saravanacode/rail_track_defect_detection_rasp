[Unit]
Description=Raspberry Pi Camera Streaming Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/camera_stream.py
WorkingDirectory=/home/pi
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
