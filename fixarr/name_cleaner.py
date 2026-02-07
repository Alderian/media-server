"""
Filename cleaning and normalization for media files.

Provides functions to extract clean titles and years from messy
media filenames, removing resolution tags, codec info, release
groups, and other extraneous information.
"""

import re
import os
from typing import Tuple, Optional


# Common patterns to remove from filenames
RESOLUTION_PATTERNS = [
    r"(?i)\b(2160p|4k|uhd|fullhd|hd|1080p|720p|480p|1080i|720i)\b",
]

CODEC_PATTERNS = [
    r"(?i)\b(x264|x265|h\.?264|h\.?265|hevc|avc|xvid|divx|av1|vp9)\b",
    r"(?i)\b(10bit|8bit)\b",
    r"(?i)\b(hdr|hdr10|hdr10plus|dolby\s*vision|dv|hlg)\b",
]

AUDIO_PATTERNS = [
    r"(?i)\b(aac|ac3|dts|dts-hd|truehd|atmos|flac|mp3|eac3|pcm|vorbis|opus)\b",
    r"(?i)\b(dd5\.?1|5\.1|7\.1|2\.0|stereo|mono|dual\.?audio)\b",
]

SOURCE_PATTERNS = [
    r"(?i)\b(bluray|blu-ray|bdrip|brrip|hdrip|webrip|web-dl|webdl|hdtv|dvdrip|dvdscr|hdcam|cam|telecine|telesync|ts|tc|tvrip|satrip)\b",
    r"(?i)\b(remux|proper|repack|extended|unrated|theatrical|directors\.?cut|imax|restored|remastered|edition|special|anniversary)\b",
]

LANGUAGE_PATTERNS = [
    r"(?i)\b(english|spanish|french|german|italian|portuguese|russian|japanese|korean|chinese|hindi|multi|dual)\b",
    r"(?i)\b(latino|castellano|lat|esp|eng|fra|ger|ita|por|rus|jap|kor|chi|hin)\b",
]

SUBTITLE_PATTERNS = [
    r"(?i)\b(subtitulado|subtitulada|subs?|hardsubs?|softsubs?)\b",
]

RELEASE_GROUP_PATTERNS = [
    r"\[.*?\]",  # [Group]
    r"\(.*?\)",  # (Anything in parentheses)
    r"\{.*?\}",  # {Anything in curly braces}
    r"\b[A-Z0-9]{2,}\-[A-Z0-9]{2,}\b",  # Potential-GroupName
    r"(?i)\b(yify|yts|rarbg|ettv|psa|qxr|hazel|ion10|amiable|spark|dgt|vxt)\b",
]

# Common release strings to remove completely
MISC_PATTERNS = [
    r"(?i)\b(completa|complete|full|season|temporada|temp|episodes?|capitulos?)\b",
    r"(?i)\b(internal|limited|rerip|retail|hc|korsub)\b",
]


def clean_media_filename(raw_filename: str) -> Tuple[str, Optional[int]]:
    """
    Clean a media filename and extract the title and year.

    Args:
        raw_filename: The original filename (with or without extension)

    Returns:
        Tuple of (clean_title, year) where year may be None if not found
    """
    # Remove file extension only if it's a known media extension
    media_exts = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.ts', '.srt', '.sub', '.ass', '.mp3', '.flac', '.m4a'}
    base, ext = os.path.splitext(raw_filename)
    if ext.lower() in media_exts:
        name = base
    else:
        name = raw_filename

    # Handle parent directory names if the filename is generic (like "S01E01.mkv")
    # This should be handled by the caller/scanner, but we clean what we have here.

    # Extract year before cleaning
    year_str = _extract_year(name)
    year = int(year_str) if year_str else None

    # Remove all known patterns
    patterns = (
        RESOLUTION_PATTERNS
        + CODEC_PATTERNS
        + AUDIO_PATTERNS
        + SOURCE_PATTERNS
        + LANGUAGE_PATTERNS
        + SUBTITLE_PATTERNS
        + MISC_PATTERNS
        + RELEASE_GROUP_PATTERNS
    )

    # Initial normalization: replace dots, underscores, hyphens with spaces
    name = re.sub(r"[\.\_\-]", " ", name)

    # Remove year from title if it was found
    if year_str:
        name = re.sub(rf"\b{year_str}\b", " ", name)

    # Remove release group tags and brackets
    name = re.sub(r"\[.*?\]", " ", name)
    name = re.sub(r"\{.*?\}", " ", name)
    name = re.sub(r"\(.*?\)", " ", name)

    # Apply all other patterns
    for pattern in patterns:
        name = re.sub(pattern, " ", name)

    # Clean up double dashes and special characters
    name = re.sub(r"[^\w\s\']", " ", name)

    # Remove multiple spaces and trim
    name = " ".join(name.split())

    # Title case the result
    title = _smart_title_case(name.strip())

    return title, year


def _extract_year(name: str) -> Optional[str]:
    """
    Extract a year (1900-2099) from a string.
    """
    # Try year in parentheses first (most common and safe)
    match = re.search(r"\((\d{4})\)", name)
    if match and 1900 <= int(match.group(1)) <= 2099:
        return match.group(1)

    # Try standalone year at the end or surrounded by separators
    matches = re.findall(r"\b(19\d{2}|20\d{2})\b", name)
    if matches:
        # Most likely the last one is the year
        return matches[-1]

    return None


def _smart_title_case(name: str) -> str:
    """Apply smart title casing."""
    lowercase_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "by", "in", "of"}
    words = name.lower().split()
    if not words:
        return ""
    
    result = []
    for i, word in enumerate(words):
        if i == 0 or word not in lowercase_words:
            result.append(word.capitalize())
        else:
            result.append(word)
    return " ".join(result)


def extract_tv_info(filename: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Extract TV show title, season, and episode from filename.
    """
    patterns = [
        # S01E01 format
        r"(?i)^(.*?)[\.\s\-_]*[Ss](\d{1,2})[Ee](\d{1,3})",
        # 1x01 format
        r"(?i)^(.*?)[\.\s\-_]*(\d{1,2})[xX](\d{1,2})",
        # Season 1 Episode 1
        r"(?i)^(.*?)[\.\s\-_]*Season[\.\s\-_]*(\d{1,2})[\.\s\-_]*Episode[\.\s\-_]*(\d{1,3})",
    ]

    name = os.path.splitext(filename)[0]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            raw_title = match.group(1)
            season = int(match.group(2))
            episode = int(match.group(3))

            title = None
            if raw_title:
                title, _ = clean_media_filename(raw_title)
            
            return title, season, episode

    return None, None, None


def is_likely_tv_show(filename: str) -> bool:
    """Check if filename matches TV patterns."""
    _, season, episode = extract_tv_info(filename)
    return season is not None and episode is not None


def get_spanish_to_english_hint(title: str) -> Optional[str]:
    """
    Provides English translation hints for common Spanish titles.
    This is useful for the identify stage when TMDb might prefer English.
    """
    # Very basic static mapping for common cases as a proof of concept
    # In a real app, this might use a translation API or a larger dictionary
    mappings = {
        "El Padrino": "The Godfather",
        "Pulp Fiction": "Pulp Fiction",
        "Cadena Perpetua": "The Shawshank Redemption",
        "La Lista de Schindler": "Schindler's List",
        "El Club de la Lucha": "Fight Club",
        "Origen": "Inception",
        "El Caballero Oscuro": "The Dark Knight",
    }
    return mappings.get(title)
