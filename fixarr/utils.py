import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'}
AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.ogg', '.wma'}
SUBTITLE_EXTENSIONS = {'.srt', '.vtt', '.sub', '.ass', '.ssa'}

def is_video(filename):
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS

def is_audio(filename):
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS

def is_subtitle(filename):
    return os.path.splitext(filename)[1].lower() in SUBTITLE_EXTENSIONS

def clean_name(name):
    """Clean filename to improve metadata matching."""
    # Remove extensions
    name = os.path.splitext(name)[0]
    # Remove common release group info and quality tags
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'(?i)(1080p|720p|4k|2160p|bluray|hdtv|web-dl|x264|x265|hevc|aac|dts|dd5\.1)', '', name)
    # Replace dots, underscores, and dashes with spaces
    name = name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    # Remove multiple spaces
    name = ' '.join(name.split())
    return name.strip()

def extract_year(name):
    """Extract year (1900-2099) from string."""
    match = re.search(r'\b(19|20)\d{2}\b', name)
    if match:
        return match.group(0)
    return None

def extract_tv_info(name):
    """Extract season and episode information."""
    patterns = [
        r'(?i)s(\d{1,2})e(\d{1,2})',      # S01E01
        r'(?i)(\d{1,2})x(\d{1,2})',      # 1x01
        r'(?i)season\s*(\d{1,2}).*?episode\s*(\d{1,2})' # Season 1 Episode 1
    ]
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None, None
