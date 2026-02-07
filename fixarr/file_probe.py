"""
File metadata probe for Fixarr.

Extracts technical metadata from media files using pymediainfo,
including video codecs, audio tracks, subtitle tracks, and resolution.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from utils import get_logger

logger = get_logger(__name__)

# Try to import pymediainfo, gracefully degrade if not available
try:
    from pymediainfo import MediaInfo
    MEDIAINFO_AVAILABLE = True
except ImportError:
    MEDIAINFO_AVAILABLE = False
    logger.warning("pymediainfo not installed. File metadata extraction disabled.")


# Codec normalization mappings
VIDEO_CODEC_MAP = {
    "avc": "h264",
    "avc1": "h264",
    "h.264": "h264",
    "hevc": "h265",
    "h.265": "h265",
    "hvc1": "h265",
    "mpeg-4 visual": "xvid",
    "mpeg4": "xvid",
    "vp9": "vp9",
    "vp8": "vp8",
    "av1": "av1",
}

AUDIO_CODEC_MAP = {
    "aac lc": "aac",
    "he-aac": "aac",
    "aac": "aac",
    "ac-3": "ac3",
    "e-ac-3": "eac3",
    "enhanced ac-3": "eac3",
    "dts": "dts",
    "dts-hd ma": "dtshd",
    "dts-hd master audio": "dtshd",
    "truehd": "truehd",
    "mlp fba": "truehd",
    "flac": "flac",
    "opus": "opus",
    "vorbis": "vorbis",
    "pcm": "pcm",
    "mp3": "mp3",
    "mpeg audio": "mp3",
}

# ISO 639-2 to common language codes
LANGUAGE_MAP = {
    "eng": "eng",
    "en": "eng",
    "english": "eng",
    "spa": "spa",
    "es": "spa",
    "spanish": "spa",
    "español": "spa",
    "castellano": "spa",
    "latino": "lat",
    "lat": "lat",
    "fra": "fra",
    "fr": "fra",
    "french": "fra",
    "français": "fra",
    "deu": "deu",
    "de": "deu",
    "german": "deu",
    "deutsch": "deu",
    "ger": "deu",
    "ita": "ita",
    "it": "ita",
    "italian": "ita",
    "por": "por",
    "pt": "por",
    "portuguese": "por",
    "rus": "rus",
    "ru": "rus",
    "russian": "rus",
    "jpn": "jpn",
    "ja": "jpn",
    "japanese": "jpn",
    "kor": "kor",
    "ko": "kor",
    "korean": "kor",
    "zho": "zho",
    "zh": "zho",
    "chinese": "zho",
    "chi": "zho",
    "hin": "hin",
    "hi": "hin",
    "hindi": "hin",
    "ara": "ara",
    "ar": "ara",
    "arabic": "ara",
    "und": "und",
    "undetermined": "und",
}


@dataclass
class FileMetadata:
    """Technical metadata extracted from a media file."""

    # Video properties
    video_codec: Optional[str] = None
    resolution: Optional[str] = None  # e.g., "1080p", "4K", "720p"
    width: Optional[int] = None
    height: Optional[int] = None
    hdr: bool = False  # HDR10, Dolby Vision, etc.
    bit_depth: Optional[int] = None  # 8, 10, 12 bit

    # Audio properties
    audio_codecs: List[str] = field(default_factory=list)
    audio_languages: List[str] = field(default_factory=list)
    audio_channels: Optional[str] = None  # "5.1", "7.1", "2.0"

    # Subtitle properties
    subtitle_languages: List[str] = field(default_factory=list)
    has_forced_subs: bool = False

    # Container and general
    container: Optional[str] = None  # mkv, mp4, avi
    duration_minutes: Optional[int] = None
    file_size_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_codec": self.video_codec,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "hdr": self.hdr,
            "bit_depth": self.bit_depth,
            "audio_codecs": self.audio_codecs,
            "audio_languages": self.audio_languages,
            "audio_channels": self.audio_channels,
            "subtitle_languages": self.subtitle_languages,
            "has_forced_subs": self.has_forced_subs,
            "container": self.container,
            "duration_minutes": self.duration_minutes,
            "file_size_mb": self.file_size_mb,
        }

    def format_audio_langs(self) -> str:
        """Format audio languages as a comma-separated string."""
        if not self.audio_languages:
            return ""
        # Return unique languages in order, uppercase
        seen = []
        for lang in self.audio_languages:
            if lang.upper() not in seen:
                seen.append(lang.upper())
        return ",".join(seen)

    def format_sub_langs(self) -> str:
        """Format subtitle languages as a comma-separated string."""
        if not self.subtitle_languages:
            return ""
        seen = []
        for lang in self.subtitle_languages:
            if lang.upper() not in seen:
                seen.append(lang.upper())
        return ",".join(seen)


class FileProbe:
    """
    Extracts technical metadata from media files.

    Uses pymediainfo to parse video, audio, and subtitle tracks,
    normalizing codec names and language codes for consistency.
    """

    def __init__(self):
        """Initialize the file prober."""
        self.available = MEDIAINFO_AVAILABLE

    def probe(self, file_path: str) -> FileMetadata:
        """
        Extract metadata from a media file.

        Args:
            file_path: Absolute path to the media file

        Returns:
            FileMetadata with extracted technical information
        """
        metadata = FileMetadata()

        if not self.available:
            logger.debug(f"Skipping probe (mediainfo unavailable): {file_path}")
            return metadata

        if not os.path.exists(file_path):
            logger.warning(f"File not found for probing: {file_path}")
            return metadata

        try:
            media_info = MediaInfo.parse(file_path)
            metadata = self._extract_metadata(media_info, file_path)
        except Exception as e:
            logger.error(f"Error probing file {file_path}: {e}")

        return metadata

    def _extract_metadata(
        self, media_info: Any, file_path: str
    ) -> FileMetadata:
        """Extract metadata from MediaInfo parse result."""
        metadata = FileMetadata()

        # Get file size
        try:
            file_size = os.path.getsize(file_path)
            metadata.file_size_mb = round(file_size / (1024 * 1024), 2)
        except OSError:
            pass

        # Get container from extension
        metadata.container = os.path.splitext(file_path)[1].lstrip(".").lower()

        for track in media_info.tracks:
            if track.track_type == "General":
                self._parse_general_track(track, metadata)
            elif track.track_type == "Video":
                self._parse_video_track(track, metadata)
            elif track.track_type == "Audio":
                self._parse_audio_track(track, metadata)
            elif track.track_type == "Text":
                self._parse_subtitle_track(track, metadata)

        return metadata

    def _parse_general_track(self, track: Any, metadata: FileMetadata) -> None:
        """Parse general track information."""
        if track.duration:
            try:
                # Duration is in milliseconds
                duration_ms = float(track.duration)
                metadata.duration_minutes = int(duration_ms / 60000)
            except (ValueError, TypeError):
                pass

    def _parse_video_track(self, track: Any, metadata: FileMetadata) -> None:
        """Parse video track information."""
        # Codec
        codec_id = (track.codec_id or "").lower()
        format_name = (track.format or "").lower()
        
        # Try codec_id first, then format
        raw_codec = codec_id or format_name
        metadata.video_codec = self._normalize_codec(raw_codec, VIDEO_CODEC_MAP)

        # Resolution
        if track.width and track.height:
            metadata.width = int(track.width)
            metadata.height = int(track.height)
            metadata.resolution = self._get_resolution_name(metadata.height)

        # Bit depth
        if track.bit_depth:
            try:
                metadata.bit_depth = int(track.bit_depth)
            except (ValueError, TypeError):
                pass

        # HDR detection
        hdr_format = (track.hdr_format or "").lower()
        transfer_characteristics = (track.transfer_characteristics or "").lower()
        
        if any(x in hdr_format for x in ["hdr10", "dolby vision", "hlg"]):
            metadata.hdr = True
        elif "pq" in transfer_characteristics or "hlg" in transfer_characteristics:
            metadata.hdr = True
        elif metadata.bit_depth and metadata.bit_depth >= 10:
            # 10-bit video is often HDR
            metadata.hdr = True

    def _parse_audio_track(self, track: Any, metadata: FileMetadata) -> None:
        """Parse audio track information."""
        # Codec
        format_name = (track.format or "").lower()
        codec_name = (track.commercial_name or format_name).lower()
        
        normalized_codec = self._normalize_codec(codec_name, AUDIO_CODEC_MAP)
        if normalized_codec and normalized_codec not in metadata.audio_codecs:
            metadata.audio_codecs.append(normalized_codec)

        # Language
        language = track.language or track.other_language
        if language:
            if isinstance(language, list):
                language = language[0] if language else None
            if language:
                norm_lang = self._normalize_language(str(language).lower())
                if norm_lang and norm_lang not in metadata.audio_languages:
                    metadata.audio_languages.append(norm_lang)

        # Channels (take the first one found)
        if not metadata.audio_channels and track.channel_s:
            try:
                channels = int(track.channel_s)
                if channels == 2:
                    metadata.audio_channels = "2.0"
                elif channels == 6:
                    metadata.audio_channels = "5.1"
                elif channels == 8:
                    metadata.audio_channels = "7.1"
                else:
                    metadata.audio_channels = str(channels)
            except (ValueError, TypeError):
                pass

    def _parse_subtitle_track(self, track: Any, metadata: FileMetadata) -> None:
        """Parse subtitle track information."""
        language = track.language or track.other_language
        if language:
            if isinstance(language, list):
                language = language[0] if language else None
            if language:
                norm_lang = self._normalize_language(str(language).lower())
                if norm_lang and norm_lang not in metadata.subtitle_languages:
                    metadata.subtitle_languages.append(norm_lang)

        # Check for forced subtitles
        forced = track.forced
        if forced and str(forced).lower() in ("yes", "true", "1"):
            metadata.has_forced_subs = True

    def _normalize_codec(
        self, raw: str, codec_map: Dict[str, str]
    ) -> Optional[str]:
        """Normalize codec name using mapping."""
        raw = raw.strip().lower()
        
        # Direct match
        if raw in codec_map:
            return codec_map[raw]
        
        # Partial match
        for key, value in codec_map.items():
            if key in raw:
                return value
        
        # Return cleaned raw value if no mapping found
        if raw:
            return raw.replace(" ", "").replace("-", "").replace(".", "")
        
        return None

    def _normalize_language(self, raw: str) -> Optional[str]:
        """Normalize language code using mapping."""
        raw = raw.strip().lower()
        
        if raw in LANGUAGE_MAP:
            return LANGUAGE_MAP[raw]
        
        # Return first 3 chars if it looks like a language code
        if len(raw) >= 2 and raw.isalpha():
            return raw[:3]
        
        return None

    def _get_resolution_name(self, height: int) -> str:
        """Convert height to common resolution name."""
        if height >= 2160:
            return "4K"
        elif height >= 1080:
            return "1080p"
        elif height >= 720:
            return "720p"
        elif height >= 480:
            return "480p"
        else:
            return f"{height}p"


# Singleton instance for convenience
_probe_instance: Optional[FileProbe] = None


def get_file_probe() -> FileProbe:
    """Get the global FileProbe instance."""
    global _probe_instance
    if _probe_instance is None:
        _probe_instance = FileProbe()
    return _probe_instance


def probe_file(file_path: str) -> FileMetadata:
    """
    Convenience function to probe a file.

    Args:
        file_path: Path to the media file

    Returns:
        FileMetadata with extracted information
    """
    return get_file_probe().probe(file_path)
