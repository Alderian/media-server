#!/bin/bash

# Update and install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip beets exiftool

# Virtual environment
python3 -m venv organizer_env
source organizer_env/bin/activate
pip install --upgrade pip

# Install Python libraries
pip3 install -r requirements.txt

echo "Installation complete!"