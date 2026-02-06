#!/bin/bash

# Update and install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip beets exiftool

# Install Python libraries
pip3 install -r requirements.txt

echo "Installation complete!"