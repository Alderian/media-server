"""
Unit tests for the file_probe module.

Tests the file metadata extraction functionality including
codec normalization, language mapping, and resolution detection.
"""

import unittest
from unittest.mock import MagicMock, patch

from file_probe import (
    FileMetadata,
    FileProbe,
    probe_file,
    VIDEO_CODEC_MAP,
    AUDIO_CODEC_MAP,
    LANGUAGE_MAP,
)


class TestFileMetadata(unittest.TestCase):
    """
    Tests for the FileMetadata dataclass.
    
    Verifies serialization and formatting methods work correctly.
    """

    def test_to_dict_empty(self):
        """
        Test that an empty FileMetadata converts to a dictionary with None/empty values.
        
        Ensures the dataclass serialization works for default values.
        """
        meta = FileMetadata()
        d = meta.to_dict()

        self.assertIsNone(d["video_codec"])
        self.assertIsNone(d["resolution"])
        self.assertEqual(d["audio_codecs"], [])
        self.assertEqual(d["audio_languages"], [])
        self.assertEqual(d["subtitle_languages"], [])
        self.assertFalse(d["hdr"])

    def test_to_dict_populated(self):
        """
        Test FileMetadata with populated values converts correctly.
        
        Verifies all fields are properly serialized to dictionary.
        """
        meta = FileMetadata(
            video_codec="h265",
            resolution="4K",
            width=3840,
            height=2160,
            hdr=True,
            bit_depth=10,
            audio_codecs=["aac", "ac3"],
            audio_languages=["eng", "spa"],
            audio_channels="5.1",
            subtitle_languages=["eng", "spa", "fra"],
            has_forced_subs=True,
            container="mkv",
            duration_minutes=120,
            file_size_mb=5000.0,
        )
        d = meta.to_dict()

        self.assertEqual(d["video_codec"], "h265")
        self.assertEqual(d["resolution"], "4K")
        self.assertEqual(d["audio_languages"], ["eng", "spa"])
        self.assertTrue(d["hdr"])
        self.assertEqual(d["bit_depth"], 10)

    def test_format_audio_langs(self):
        """
        Test audio language formatting removes duplicates and uppercases.
        
        Verifies the format_audio_langs helper produces expected output.
        """
        meta = FileMetadata(audio_languages=["eng", "spa", "eng", "fra"])
        result = meta.format_audio_langs()
        self.assertEqual(result, "ENG,SPA,FRA")

    def test_format_audio_langs_empty(self):
        """
        Test audio language formatting returns empty string for no languages.
        
        Verifies graceful handling of empty input.
        """
        meta = FileMetadata()
        self.assertEqual(meta.format_audio_langs(), "")

    def test_format_sub_langs(self):
        """
        Test subtitle language formatting removes duplicates and uppercases.
        
        Verifies the format_sub_langs helper produces expected output.
        """
        meta = FileMetadata(subtitle_languages=["eng", "spa"])
        result = meta.format_sub_langs()
        self.assertEqual(result, "ENG,SPA")


class TestFileProbe(unittest.TestCase):
    """
    Tests for the FileProbe class.
    
    Uses mocking to avoid requiring real media files or pymediainfo.
    """

    def setUp(self):
        """Set up a FileProbe instance for testing."""
        self.probe = FileProbe()

    def test_normalize_codec_video(self):
        """
        Test video codec normalization mappings.
        
        Verifies common codec names are normalized correctly.
        """
        test_cases = [
            ("avc", "h264"),
            ("AVC", "h264"),
            ("h.264", "h264"),
            ("hevc", "h265"),
            ("HEVC", "h265"),
            ("h.265", "h265"),
            ("mpeg-4 visual", "xvid"),
            ("vp9", "vp9"),
            ("av1", "av1"),
        ]

        for raw, expected in test_cases:
            result = self.probe._normalize_codec(raw, VIDEO_CODEC_MAP)
            self.assertEqual(result, expected, f"Failed for {raw}")

    def test_normalize_codec_audio(self):
        """
        Test audio codec normalization mappings.
        
        Verifies audio codec names are normalized correctly.
        """
        test_cases = [
            ("aac lc", "aac"),
            ("AC-3", "ac3"),
            ("E-AC-3", "eac3"),
            ("DTS", "dts"),
            ("TrueHD", "truehd"),
            ("FLAC", "flac"),
        ]

        for raw, expected in test_cases:
            result = self.probe._normalize_codec(raw, AUDIO_CODEC_MAP)
            self.assertEqual(result, expected, f"Failed for {raw}")

    def test_normalize_language(self):
        """
        Test language code normalization.
        
        Verifies various language formats are normalized to ISO 639-2.
        """
        test_cases = [
            ("english", "eng"),
            ("eng", "eng"),
            ("en", "eng"),
            ("spanish", "spa"),
            ("español", "spa"),
            ("castellano", "spa"),
            ("japanese", "jpn"),
            ("und", "und"),
        ]

        for raw, expected in test_cases:
            result = self.probe._normalize_language(raw)
            self.assertEqual(result, expected, f"Failed for {raw}")

    def test_get_resolution_name(self):
        """
        Test resolution name generation from height.
        
        Verifies common resolutions are named correctly.
        """
        test_cases = [
            (2160, "4K"),
            (1080, "1080p"),
            (720, "720p"),
            (480, "480p"),
            (360, "360p"),
        ]

        for height, expected in test_cases:
            result = self.probe._get_resolution_name(height)
            self.assertEqual(result, expected, f"Failed for {height}")

    def test_probe_nonexistent_file(self):
        """
        Test probing a non-existent file returns empty metadata.
        
        Verifies graceful handling when file doesn't exist.
        """
        result = self.probe.probe("/nonexistent/path/movie.mkv")
        self.assertIsInstance(result, FileMetadata)
        self.assertIsNone(result.video_codec)

    @patch("file_probe.MEDIAINFO_AVAILABLE", False)
    def test_probe_when_mediainfo_unavailable(self):
        """
        Test probing gracefully degrades when pymediainfo is not available.
        
        Verifies the probe returns empty metadata without crashing.
        """
        probe = FileProbe()
        probe.available = False
        result = probe.probe("/some/file.mkv")
        self.assertIsInstance(result, FileMetadata)
        self.assertIsNone(result.video_codec)


class TestProbeFileFunction(unittest.TestCase):
    """
    Tests for the probe_file convenience function.
    
    Verifies the global singleton pattern works correctly.
    """

    def test_probe_file_returns_metadata(self):
        """
        Test probe_file returns a FileMetadata instance.
        
        Verifies the convenience function works.
        """
        result = probe_file("/nonexistent/path.mkv")
        self.assertIsInstance(result, FileMetadata)


if __name__ == "__main__":
    unittest.main()
