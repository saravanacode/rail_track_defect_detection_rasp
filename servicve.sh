[Unit]
Description=Raspberry Pi Camera Streaming Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/saravana/cam_stream/camera_stream.py
WorkingDirectory=/home/saravana/cam_stream/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=saravana

[Install]
WantedBy=multi-user.target
