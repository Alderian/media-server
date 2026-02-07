"""
Utility functions for Fixarr.

Contains helper functions for file type detection, logging configuration,
and common operations used throughout the application.
"""

import os
import re
import logging
from typing import Optional, Set, Tuple

# File extension sets
VIDEO_EXTENSIONS: Set[str] = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".ts", ".m2ts", ".vob",
}

AUDIO_EXTENSIONS: Set[str] = {
    ".mp3", ".flac", ".wav", ".m4a", ".ogg", ".wma",
    ".aac", ".opus", ".ape", ".alac",
}

SUBTITLE_EXTENSIONS: Set[str] = {
    ".srt", ".vtt", ".sub", ".ass", ".ssa", ".idx",
}

# Language codes for subtitle detection
LANGUAGE_CODES = {
    "en": "English", "eng": "English", "english": "English",
    "es": "Spanish", "spa": "Spanish", "spanish": "Spanish",
    "fr": "French", "fra": "French", "french": "French",
    "de": "German", "ger": "German", "deu": "German", "german": "German",
    "it": "Italian", "ita": "Italian", "italian": "Italian",
    "pt": "Portuguese", "por": "Portuguese", "portuguese": "Portuguese",
    "ru": "Russian", "rus": "Russian", "russian": "Russian",
    "ja": "Japanese", "jpn": "Japanese", "japanese": "Japanese",
    "ko": "Korean", "kor": "Korean", "korean": "Korean",
    "zh": "Chinese", "chi": "Chinese", "chinese": "Chinese",
    "ar": "Arabic", "ara": "Arabic", "arabic": "Arabic",
    "hi": "Hindi", "hin": "Hindi", "hindi": "Hindi",
    "nl": "Dutch", "dut": "Dutch", "dutch": "Dutch",
    "pl": "Polish", "pol": "Polish", "polish": "Polish",
    "sv": "Swedish", "swe": "Swedish", "swedish": "Swedish",
    "no": "Norwegian", "nor": "Norwegian", "norwegian": "Norwegian",
    "da": "Danish", "dan": "Danish", "danish": "Danish",
    "fi": "Finnish", "fin": "Finnish", "finnish": "Finnish",
    "tr": "Turkish", "tur": "Turkish", "turkish": "Turkish",
    "he": "Hebrew", "heb": "Hebrew", "hebrew": "Hebrew",
    "th": "Thai", "tha": "Thai", "thai": "Thai",
    "vi": "Vietnamese", "vie": "Vietnamese", "vietnamese": "Vietnamese",
}


def is_video(filename: str) -> bool:
    """
    Check if a file is a video based on extension.

    Args:
        filename: Name of the file to check

    Returns:
        True if the file has a video extension
    """
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS


def is_audio(filename: str) -> bool:
    """
    Check if a file is an audio file based on extension.

    Args:
        filename: Name of the file to check

    Returns:
        True if the file has an audio extension
    """
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS


def is_subtitle(filename: str) -> bool:
    """
    Check if a file is a subtitle based on extension.

    Args:
        filename: Name of the file to check

    Returns:
        True if the file has a subtitle extension
    """
    return os.path.splitext(filename)[1].lower() in SUBTITLE_EXTENSIONS


def extract_year(name: str) -> Optional[str]:
    """
    Extract a year (1900-2099) from a string.

    Args:
        name: String to search for a year

    Returns:
        Year as string or None if not found
    """
    match = re.search(r"\b(19\d{2}|20\d{2})\b", name)
    return match.group(0) if match else None


def extract_tv_info(name: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract season and episode information from a filename.

    Args:
        name: Filename to parse

    Returns:
        Tuple of (season, episode) - both may be None
    """
    patterns = [
        r"(?i)[Ss](\d{1,2})[Ee](\d{1,3})",  # S01E01 or s1e1
        r"(?i)(\d{1,2})[xX](\d{1,2})",  # 1x01
        r"(?i)[Ss]eason[\s._-]*(\d{1,2})[\s._-]*[Ee]pisode[\s._-]*(\d{1,3})",  # Season 1 Episode 1
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return int(match.group(1)), int(match.group(2))

    return None, None


def detect_subtitle_language(filename: str) -> Optional[str]:
    """
    Detect subtitle language from filename.

    Common patterns:
    - movie.en.srt
    - movie.english.srt
    - movie.eng.srt
    - movie_english.srt

    Args:
        filename: Subtitle filename

    Returns:
        Language name or None if not detected
    """
    # Remove extension and get potential language code
    basename = os.path.splitext(filename)[0]

    # Check for language code at end (e.g., movie.en or movie_eng)
    patterns = [
        r"[\._\-]([a-z]{2,3})$",  # .en, .eng, _english
        r"[\._\-]([a-z]+)$",  # _english
    ]

    for pattern in patterns:
        match = re.search(pattern, basename, re.IGNORECASE)
        if match:
            code = match.group(1).lower()
            if code in LANGUAGE_CODES:
                return LANGUAGE_CODES[code]

    return None


def find_matching_subtitles(video_path: str, subtitle_files: list) -> list:
    """
    Find subtitles that match a video file.

    Args:
        video_path: Path to the video file
        subtitle_files: List of subtitle file paths

    Returns:
        List of matching subtitle paths with detected languages
    """
    video_basename = os.path.splitext(os.path.basename(video_path))[0]
    matching = []

    for sub in subtitle_files:
        sub_basename = os.path.basename(sub)

        # Check if subtitle starts with video name
        if sub_basename.startswith(video_basename):
            language = detect_subtitle_language(sub_basename)
            matching.append({
                "path": sub,
                "language": language,
            })

    return matching


# Logging configuration
_loggers: dict = {}


def get_logger(name: str, verbose: bool = False) -> logging.Logger:
    """
    Get or create a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__)
        verbose: Enable debug-level logging

    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    _loggers[name] = logger

    return logger


def set_verbose(verbose: bool) -> None:
    """
    Set verbose mode for all loggers.

    Args:
        verbose: Enable debug-level logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    for log in _loggers.values():
        log.setLevel(level)


# Default logger for backward compatibility
logger = get_logger("fixarr")


# Deprecated function - keeping for backward compatibility
def clean_name(name: str) -> str:
    """
    Clean filename to improve metadata matching.

    DEPRECATED: Use name_cleaner.clean_media_filename() instead.
    This function is kept for backward compatibility.

    Args:
        name: Filename to clean

    Returns:
        Cleaned name
    """
    # Remove file extension
    name = os.path.splitext(name)[0]
    # Remove common release group info and quality tags
    name = re.sub(r"\[.*?\]|\(.*?\)", "", name)
    name = re.sub(
        r"(?i)(1080p|720p|4k|2160p|bluray|hdtv|web-dl|x264|x265|hevc|aac|dts|dd5\.1)",
        "",
        name,
    )
    # Replace dots, underscores, and dashes with spaces
    name = name.replace(".", " ").replace("_", " ").replace("-", " ")
    # Remove multiple spaces
    name = " ".join(name.split())
    return name.strip()
