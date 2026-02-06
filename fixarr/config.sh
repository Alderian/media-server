#!/bin/bash
#
# Configuration for Alderian Media Organizer
#

# --- Paths ---
# The main directory where your unorganized media is located.
SOURCE_DIR="/path/to/your/disorganized/media"

# The final directory where Jellyfin will look for your organized library.
DEST_DIR="/path/to/your/organized/media/library"

# --- Tools ---
# Path to beets executable (if not in system PATH)
BEETS_CMD="beet"

# --- Options ---
# Destination subdirectories
MOVIE_DIR_NAME="Movies"
TV_SHOW_DIR_NAME="TV Shows"
MUSIC_DIR_NAME="Music"
