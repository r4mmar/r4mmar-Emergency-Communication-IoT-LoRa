#!/bin/bash

sudo apt update

sudo apt install python3-pip -y

pip3 install -r requirements.txt

sudo systemctl daemon-reload

sudo systemctl enable gateway.service

sudo systemctl start gateway.service

echo "Installation Complete"
